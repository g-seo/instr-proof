# Quickstart: Validate the Reproducible Demo

## Prerequisites

- Supported Linux
- Git, uv, and Python 3.12+
- Synchronized development dependencies

```sh
uv sync --locked --dev
```

No network is required after setup.

## Run the demo

```sh
./scripts/run-demo.sh
```

The absolute script path also works from outside the repository. Expected runtime is under 30 seconds.

Verify ordered labels for baseline, stale refactor, and repaired instruction. Per the [runner contract](contracts/demo-runner.md), baseline inspection reports one `PathExists` contract for `AGENTS.md` and `src/auth/service.py`; the broken comparison reports exactly one regression and expected status 1; the repaired comparison against the same `demo-base` reports no regression and status 0. The generated repository is removed by default.

## Retain and inspect

```sh
./scripts/run-demo.sh --keep
```

The final line reports one retained absolute path. There, verify `demo-base`, the repaired `AGENTS.md`, replacement source, and passing application test. Use the documented project-root invocation to rerun `check` or comparisons, then delete only the displayed directory.

## Focused validation

```sh
uv run pytest tests/integration/test_reproducible_demo.py
```

Expected: subprocess checks cover complete output/status behavior, shared BASE, cleanup, keep mode, outside-checkout use, failures, and three-run equivalence. Parent isolation includes unchanged porcelain, an identical Git-visible path/type/content/link/mode snapshot, exact preservation of a collision-resistant pre-existing untracked sentinel, and unchanged bytes for a stable tracked file.

## Compatibility validation

```sh
uv run pytest
./scripts/validate-release.sh
```

Expected: the previous 285 tests plus demo tests pass and feature 006 release validation remains successful. See the [data model](data-model.md) for state invariants.
