# Type Checking

thumbor is being annotated incrementally. The checker is
[ty](https://github.com/astral-sh/ty), from the same team that maintains uv,
and it is wired up in **reporting-only** mode: it never fails a build and is
not part of CI yet.

## Running it

```
$ make typecheck
```

This prints every diagnostic, followed by a count per rule so progress is
comparable between runs. To check a single module while you work on it:

```
$ uv run --locked --extra tests --extra all ty check thumbor/context.py
```

ty is configured under `[tool.ty]` in `pyproject.toml`. It is scoped to the
`thumbor` package for now; `tests/` and `integration_tests/` are added once
the package itself is clean.

## The gate

```
$ make typecheck-ci
```

This one does fail, but only on the rules that are already at zero. The
rules thumbor still owes work on are set to `warn` in `[tool.ty.rules]`, and
the command runs with `--exit-zero-on-warning`, so the existing backlog does
not block anything while a newly introduced problem does.

That is the mechanism for finishing a rule off: drive it to zero, delete its
line from `[tool.ty.rules]`, and from then on it is an error that the gate
catches. `invalid-method-override`, `call-non-callable`, `missing-argument`,
`invalid-parameter-default`, `invalid-type-form` and `redundant-condition`
went through this already.

Wiring it into CI and pre-commit is the remaining step and has not been
done; the workflow files are untouched.

## Where the diagnostics come from

The count started at **419** (ty 0.0.89, `thumbor/` only), was **375**
after phase 1, **369** after phase 2, **323** after phase 3, **316** after
phase 4, **155** after phase 5, **67** after phase 6 and is **37** after
phase 7. The number moves slowly on
purpose: annotating a module often *reveals* errors that were previously
hidden behind `Unknown`, so a phase can fix real problems while the total
barely moves — or rises.

Almost all of it is one shape. `Context`, `ContextImporter`, `BaseFilter`
and `BaseEngine` each initialise their collaborators to `None`, so ty infers
`None` and rejects every downstream `self.context.config.X`,
`self.engine.size` and `context.modules.storage`. The chain has four links
and the errors only clear when a link is annotated — fixing `Context` alone
moved the total by 25.

86 of them were a single problem — the reachable `None` on
`BaseFilter.engine` — and phase 6 fixed it, which is why the count finally
moved a long way. The lesson held: those 86 were never 86 problems, and no
amount of annotating around them would have been progress.

## Optional or not: the rule we follow

Many attributes have a `None` default that the real code path never leaves
in place. We decide per attribute, rather than applying one blanket policy:

- **The `None` is only an artifact of construction** — declare the attribute
  as always-present and suppress the one assignment, with a comment saying
  why. `Context.config` and `Context.server` work this way: a running
  server always passes them and only `tests/test_context.py` builds a bare
  `Context`. One suppression at the source beats a few hundred downstream.
- **The `None` is genuinely reachable** — keep it in the type and narrow at
  the point of use. `BaseFilter.engine` is the example: `run()` assigns
  `None` to it when there is no engine, so `engine: BaseEngine` would hide a
  real `AttributeError`.

Never suppress a reachable `None` just to lower the count. The checker
earning its keep matters more than the number.

## Conventions

- Prefer `X | None` over `Optional[X]`, and builtin generics (`dict[str, Any]`)
  over `typing.Dict`. The floor is Python 3.10.
- Add `from __future__ import annotations` to a module when it needs forward
  references — a `TYPE_CHECKING` import or a class defined further down the
  file. It keeps annotations free of quotes. Nothing in thumbor reads
  annotations at runtime, so this is safe.
- Import `Context` and other cycle-forming types under `if TYPE_CHECKING:`.
- Suppress with `# ty: ignore[rule-name]`, always naming the rule, and only
  where the dynamism is deliberate. Blanket ignores hide the next regression.

## Generated stubs

**`thumbor/config.pyi`** — derpconf builds its options at runtime from the
136 `Config.define` calls in `thumbor/config.py`, so a checker sees none of
them. `scripts/generate_config_stub.py` reads those calls and writes the
stub; run it with `make config-stub` after adding, removing or renaming an
option. `tests/test_config_stub.py` fails when the checked-in stub is stale.

With the stub in place, `context.config.MAX_WIDTH` resolves to `int` and
`context.config.FILTERS` to `list[str]`. An option whose default is `None`
has no inferable type and widens to `Any`; refining those 31 by hand is
future work. Note that the stub gives options *types* but does not catch
typos, because derpconf's `__getattr__` accepts any name.

The generator runs in a subprocess from the test, deliberately: derpconf
keeps options in class-level state and `tests/test_config.py` registers
extra aliases into it, so comparing against the live `Config` from inside
the suite reports a stale stub that is in fact current.

**`thumbor/ext/filters/*.pyi`** — 16 hand-written stubs, one per C
extension. ty cannot read a compiled `.so`, so `make compile_ext` does not
help. The signatures are transcribed from each module's
`PyArg_ParseTuple`/`PyArg_UnpackTuple` format string; keep them in sync when
the C signature changes.

## Dependencies

Typed (ship `py.typed`): `tornado`, `Pillow`, `numpy`, `cv2`.

Untyped: `derpconf`, `libthumbor`, `piexif`, `statsd`, `JpegIPTC`, `cairosvg`,
`pycurl`, `remotecv`.

thumbor does not ship a `py.typed` marker of its own yet, so these
annotations are for development only and are not published to consumers.

## Roadmap

**Phase 0 (done)** — `[tool.ty]`, `make typecheck`, this page. The old
`mypy.ini` was removed: it was never referenced by the Makefile, CI or
pre-commit, and keeping two checkers configured invites them to disagree.

**Phase 1 (done)** — the generated `config.pyi`, the 16 C extension stubs,
and the data carriers: `Context`, `ServerParameters`, `RequestParameters`,
`FocalPoint`, `LoaderResult` and `EngineResult`.

Phase 1 also fixed two real bugs that were sitting in the only annotations
the codebase had. `LoaderResult.__init__` declared `buffer: bytes = None`
and `metadata: Dict[str, any] = None` — implicit `Optional`, plus the
builtin `any` function where `typing.Any` was meant.

**Phase 2 (done)** — `BaseFilter`, `FiltersFactory`, `FiltersRunner`,
`filter_method`, `BaseMetrics` and `BaseOptimizer`, with their subclasses.
The 32 filter subclasses inherit the contract and needed no changes.

Phase 2 also corrected an inconsistency left by phase 1: `Context.modules`
had been declared `ContextImporter | None`, although its `None` is the same
construction artifact as `config` and `server`. Making it non-optional
removed 25 diagnostics in `filters/frame.py` and elsewhere, and introduced
no `redundant-condition` warnings on the existing `if self.modules` guards.

**Phase 3 (done)** — `Protocol` definitions for the plugin points that are
modules rather than classes, plus attribute annotations on `Importer` and
`ContextImporter`.

`LoaderModule` lives in `thumbor/loaders/__init__.py` and
`HandlerListModule` in `thumbor/handler_lists/__init__.py`. `UrlSigner`
had to go in `thumbor/importer.py` instead of beside the others, because
`thumbor/url_signers/__init__.py` replaces itself in `sys.modules` with
libthumbor's package and so cannot host a type. All three declare their
members as `@staticmethod`, which is what makes a Protocol match a module
rather than an instance.

`Importer` and `ContextImporter` assign their attributes through `setattr`,
so declaring them is the only way the checker can see them. Which ones are
optional is not a judgement call here: `config.validates_presence_of`
names exactly those the config guarantees, and those are declared
always-present. The rest keep their `None`. This is what the two
`call-non-callable` diagnostics in `handlers/imaging.py` were pointing at,
and they are gone.

Phase 3 also removed three now-redundant `cast()` calls in the handler
lists — `config.HEALTHCHECK_ROUTE` and friends have real types since the
`config.pyi` landed — and `.flake8` now ignores `E704`, which fires on the
`def f() -> T: ...` bodies black writes for Protocol members.

**Phase 4 (done)** — both `BaseStorage` classes and `BaseDetector`, with
their implementations. The two storage bases now carry docstrings saying
which is which, since `storages/` and `result_storages/` define distinct
classes under the same name.

Declaring the storage contracts is what surfaced the `MixedStorage`
findings below. It also let three annotations be corrected:
`get_detection_offset` was declared `Dict[str, int]` in both detectors but
returns floats, and `FocalPoint.from_square` had been annotated with `int`
parameters in phase 1 although `CascadeLoaderDetector.detect` passes it
`int + float`. `RequestParameters.url` is now declared non-optional, since
`ImagingHandler` always passes the tornado request and
`_set_request_headers` sets the url from its path.

**Phase 7 (in progress)** — draining what was left, which by then was a
long tail rather than any one cause. Three real defects came out of it:

- `filters:upscale()` returned **HTTP 500** on any URL asking for the
  original size, such as `/unsafe/origxorig/filters:upscale()/img.jpg`.
  `request.width` stays as the string `"orig"` through the transformer, and
  comparing it against the source size raised `TypeError`. Now the filter
  returns early, since there is no target to scale up to.
- `BaseEngine.read` was annotated `-> bytes` in phase 5, but `JSONEngine`
  returns a JSON string, which is exactly why `BaseHandler._ensure_bytes`
  exists. Corrected to `bytes | str`.
- `thumbor/testing.py` built its multipart body with
  `b"..." % guess_type(f)[0].encode() or b"application/octet-stream"`. The
  `or` applied to the formatted line, not to the `None` that `guess_type`
  can return, so `.encode()` would already have raised. The fallback never
  worked.

Two name collisions were also untangled: `curve.py` and `frame.py` both
assigned a plain string to `regex`, which is the attribute `compile_regex`
overwrites with the filter's compiled pattern. `curve.py`'s is a parameter
spec and was renamed; `frame.py`'s was vestigial and removed.

`filter_method` now returns a `RunnableMethod` protocol that carries the
`filter_data` the decorator attaches, instead of a bare `Callable` that
could not describe it.

**Phase 6 (done)** — fixed the `BaseFilter.engine` defect the earlier
phases had been recording.

`run()` assigned `None` to `self.engine` when the context had no engine and
then called the filter anyway, so any filter that reads the engine raised
`AttributeError` on `NoneType` — saying nothing about which filter or why.
The `[None]` branch could not simply go: filters that never touch the
engine rely on it, and `tests/filters/test_base_filter.py` exercises
exactly that with filters of its own.

So `BaseFilter` now declares `uses_engine`, the 23 built-in filters that
read `self.engine` set it to `True`, and `run()` raises a named
`RuntimeError` instead of letting the `AttributeError` happen. The default
is `False` so that third-party filters, which do not know about the flag,
keep their current behaviour.

That invariant is what makes `engine: BaseEngine` true rather than
convenient: inside the method of a filter that declares the flag, it cannot
be None, because `run()` refused to get there. Only the two assignments
that can store `None` are suppressed.

`tests/filters/test_base_filter.py` covers the refusal, the success path,
and that a filter without the flag still runs. A fourth test walks every
built-in filter and asserts the flag matches whether the source actually
reads `self.engine`, so adding a filter that touches the engine and
forgetting the flag fails the suite rather than reintroducing the bug.

**Phase 5 (done)** — `BaseEngine` and `BaseHandler`, the two widest
interfaces, and the partial gate described above.

The single biggest win was declaring `BaseHandler.context`. `on_finish` does
`self.context = getattr(self, "context", None)` so that a handler whose
`initialize` never ran can bail out instead of raising, and that one line
was making ty infer `Any | None` for every `self.context` read in the
handlers — 111 diagnostics from one assignment.

`BaseEngine` got all 43 method signatures plus its attributes.
`BaseEngine.read` gained the `extension=None, quality=None` defaults every
subclass and every caller already assumed, which closed the
`invalid-method-override` on `PILEngine.read` and the `missing-argument` in
`filters/frame.py`. `json_engine.read` was aligned the same way.

Three groups of diagnostics are suppressed rather than fixed, each with a
comment at the site: `BaseEngine.wrap` replaces `read` and `rotate` with
per-instance callables, so the attribute and the method of the same name
coexist; tornado types its verb handlers as `(*args: str, **kwargs: str)`
while thumbor declares the concrete arguments its routes capture; and
`BaseHandler._cleanup` deliberately assigns `None` over its declared types
to drop references early.

## Open findings

Things the checker surfaced that are real but out of scope for a typing
change, and should be fixed on their own:

- `datetime.utcnow()` and `datetime.utcfromtimestamp()` are deprecated, in
  `handlers/__init__.py`, `handlers/image_resource.py` and
  `loaders/file_loader.py`. Fixing them changes behaviour (naive to
  timezone-aware datetimes), so it needs its own change and tests.
- `RequestParameters.filters` defaults to `[]` but arrives from the URL as a
  `str`, and is consumed with `.split("):")`. The annotation records the
  union rather than papering over it.
- `ImageApiHandler.validate(body)` and `BaseHandler.validate(path)` share a
  name by accident and do unrelated things — one checks an upload body, the
  other a loader path. The subclass shadows the parent in a hierarchy where
  both are reachable.
- `PILEngine.gen_image` calls `Filter.get_median_color(self.context.modules)`
  — an unbound instance method with a `ContextImporter` passed as `self`. It
  works only because both that class and `Filter` happen to expose
  `.engine`, which is all the method touches.
- `MixedStorage.resolve_original_photo_path` delegates to
  `self.file_storage.resolve_original_photo_path`, but no storage shipped
  with thumbor defines that method, and unlike every other method on the
  class it does not call `_init_file_storage()` first. It raises
  `AttributeError` whichever way it is reached. Left as is because it is
  public API; the diagnostic is suppressed where it occurs.
- `result_storages/file_storage.last_updated()` returns `True` on both of
  its failure paths and a `datetime` otherwise, and its only caller does
  `result_last_modified.strftime(...)` — which would raise on the `True`.
  The annotation records `datetime | bool` rather than hiding it. The same
  caller also does `await` on `last_updated()`, which is a plain `def`, so
  a result storage returning a real value there raises `TypeError` that the
  surrounding `except NotImplementedError` does not catch. Unreachable with
  the bundled file storage, whose `get()` returns a `ResultStorageResult`
  and so takes the other branch.
- `BaseEngine.read(self, extension, quality)` takes no defaults, but every
  subclass declares `read(self, extension=None, quality=None)` and every
  caller invokes `read()` with no arguments. The base signature is stricter
  than its implementations, which is both one of the 17
  `invalid-method-override` diagnostics and the `missing-argument` one in
  `filters/frame.py`. Phase 5 territory, since it touches `BaseEngine`.
- `Importer.import_item` declares `config_key=None`, but it cannot do
  anything without it — all 19 call sites pass it and the method would
  raise on `None`. Left as is, since the signature is public; the two
  resulting diagnostics are suppressed where they occur.

