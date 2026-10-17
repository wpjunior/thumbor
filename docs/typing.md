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

## Baseline

Recorded with ty 0.0.89 over `thumbor/`, before any annotation work:
**419 diagnostics**.

| Count | Rule |
| ----: | ---- |
| 327 | `unresolved-attribute` |
| 27 | `invalid-assignment` |
| 18 | `unresolved-import` |
| 17 | `invalid-method-override` |
| 10 | `invalid-argument-type` |
| 4 | `invalid-parameter-default` |
| 3 | `deprecated` |
| 2 | `unsupported-operator` |
| 2 | `too-many-positional-arguments` |
| 2 | `no-matching-overload` |
| 2 | `invalid-type-form` |
| 5 | one each: `unused-type-ignore-comment`, `redundant-condition`, `not-subscriptable`, `not-iterable`, `invalid-return-type` |

That number is large but concentrated. Two causes account for most of it:

- **303 of the 419** (72%) are "attribute is not defined on `None`". Every
  collaborator on `Context` is declared as `server=None, config=None,
  importer=None`, so ty infers `None` and then rejects `context.config.X`,
  `context.request.Y` and `context.modules.Z` everywhere downstream. Annotating
  `Context` alone should clear the bulk of them.
- **17** are the C extensions in `thumbor/ext/filters/`. ty does not read
  `.so` files, so `make compile_ext` does not help; these need `.pyi` stubs.

The four `invalid-parameter-default` are genuine bugs already in the tree:
`LoaderResult.__init__` annotates `buffer: bytes = None` and
`metadata: Dict[str, any] = None` — implicit `Optional`, plus the builtin
`any` function used where `typing.Any` was meant.

## Dependencies

Typed (ship `py.typed`): `tornado`, `Pillow`, `numpy`, `cv2`.

Untyped: `derpconf`, `libthumbor`, `piexif`, `statsd`, `JpegIPTC`, `cairosvg`,
`pycurl`, `remotecv`.

`derpconf` is the important one: `Config` builds its 136 attributes at runtime
through `Config.define(...)`, and thumbor reads 111 distinct ones as
`config.MAX_WIDTH` and friends. Those names are all statically available in
`thumbor/config.py`, so the stub for them can be generated rather than written
by hand.

## Roadmap

Phase 0 (done) is this page, the `[tool.ty]` config and `make typecheck`.
The `mypy.ini` that used to sit in the repo root was removed: it was never
referenced by the Makefile, CI or pre-commit, and keeping two checkers
configured invites them to disagree.

The remaining phases, in dependency order:

1. Generate the `derpconf.Config` stub from the `Config.define` calls, write
   `.pyi` stubs for `thumbor/ext/filters/`, and annotate the data carriers:
   `Context`, `ServerParameters`, `RequestParameters`, `LoaderResult` (fixing
   the bugs above), `FocalPoint`, `EngineResult`.
2. `BaseFilter`, `BaseMetrics`, `BaseOptimizer`. The 32 filter subclasses
   inherit the contract, so they come along nearly for free.
3. `Protocol` definitions for the duck-typed plugin points that are modules
   rather than classes — loaders (`async def load(context, url)`),
   handler lists (`def get_handlers(context)`) and url signers — plus
   attribute annotations on `Importer`.
4. `BaseStorage` (both of them: `storages/` and `result_storages/` define
   distinct classes under the same name) and `BaseDetector`.
5. `BaseEngine` and `BaseHandler`, the two widest interfaces (43 and 44
   methods). Only then does ty become a CI gate and a pre-commit hook.

## Conventions

- Prefer `X | None` over `Optional[X]`, and builtin generics (`dict[str, Any]`)
  over `typing.Dict`. The floor is Python 3.10.
- Import `Context` under `if TYPE_CHECKING:` to avoid the import cycle, and
  quote the annotation.
- Suppress with `# ty: ignore[rule-name]`, always naming the rule, and only
  where the dynamism is deliberate. Blanket ignores hide the next regression.
