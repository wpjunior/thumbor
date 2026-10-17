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

## Where the diagnostics come from

The count started at **419** (ty 0.0.89, `thumbor/` only) and is **375**
after phase 1. The number moves slowly on purpose: annotating a module
often *reveals* errors that were previously hidden behind `Unknown`, so a
phase can fix real problems without the total dropping much.

Almost all of it is one shape. `Context`, `ContextImporter`, `BaseFilter`
and `BaseEngine` each initialise their collaborators to `None`, so ty infers
`None` and rejects every downstream `self.context.config.X`,
`self.engine.size` and `context.modules.storage`. The chain has four links
and the errors only clear when a link is annotated — fixing `Context` alone
moved the total by 25.

That is why the biggest numeric wins are in phases 2 and 5, not here:
`BaseFilter.context` feeds the 32 filters and `BaseHandler.context` feeds
the handlers, which together hold most of the remaining diagnostics.

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

**Phase 2** — `BaseFilter`, `BaseMetrics`, `BaseOptimizer`. The 32 filter
subclasses inherit the contract, so they come along nearly for free. This is
where `BaseFilter.engine`'s reachable `None` gets handled.

**Phase 3** — `Protocol` definitions for the duck-typed plugin points that
are modules rather than classes: loaders (`async def load(context, url)`),
handler lists (`def get_handlers(context)`) and url signers. Plus attribute
annotations on `Importer`, whose attributes are assigned through `setattr`
and so are invisible to the checker — this is what the two
`call-non-callable` diagnostics in `handlers/imaging.py` are pointing at.

**Phase 4** — `BaseStorage` (both of them: `storages/` and
`result_storages/` define distinct classes under the same name) and
`BaseDetector`.

**Phase 5** — `BaseEngine` and `BaseHandler`, the two widest interfaces (43
and 44 methods). Only then does ty become a CI gate and a pre-commit hook.

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
- `BaseFilter.run()` assigns `None` to `self.engine` when there is no
  engine, which makes filters such as `background_color` raise
  `AttributeError`. Unreachable in a running server, since `context.modules`
  is always present there.
