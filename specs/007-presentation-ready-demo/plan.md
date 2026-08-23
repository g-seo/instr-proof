# Implementation Plan: Reproducible Public Demo

**Branch**: `[007-presentation-ready-demo]` | **Date**: 2026-08-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-presentation-ready-demo/spec.md`

## Summary

Add a presentation-ready layer around the existing InstrProof executable without changing production analysis code. A static minimal repository template is copied into an isolated temporary directory, committed as a real Git baseline, refactored into one stale `PathExists` claim, and repaired while one shell runner validates exact commands, diagnostics, and statuses. Subprocess integration tests and concise README guidance make the workflow repeatable, offline after setup, safe by default, inspectable with `--keep`, and independent from feature 006 release fixtures.

## Technical Context

**Language/Version**: Python 3.12+ for the demo repository and pytest tests; Bash with POSIX command-line utilities for orchestration

**Primary Dependencies**: Existing dependency-free InstrProof CLI; Git; uv; Python standard library only in the template; no new project dependency

**Storage**: Static example files plus one `mktemp` working repository per run; no persistence unless `--keep` is selected

**Testing**: pytest subprocess integration tests, standard-library `unittest` inside the demo repository, and the complete existing pytest suite

**Target Platform**: Supported Linux environment with Git, uv, Bash, and synchronized project dependencies

**Project Type**: Existing single-package CLI with a separate public example and maintenance runner

**Performance Goals**: Complete one run in under 30 seconds after setup; three consecutive runs have equivalent normalized output

**Constraints**: No network after setup; no production analysis, CLI, CI, or release-fixture changes; exactly one status-1 regression; status-0 repair; same immutable BASE; no parent-checkout mutation; exact before/after equality for parent Git porcelain plus every Git-visible tracked/untracked path's type, bytes or cryptographic digest, symlink target, and relevant executable mode; cleanup on success, failure, and interruption

**Scale/Scope**: One minimal demo template, one runner, one integration-test module, one README section, three stages, and one `PathExists` regression

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **I. Simplicity & Necessity — PASS**: One static example, one runner, one integration module, and documentation reuse Git, uv, the existing CLI, and the standard library without a new dependency or abstraction.
- **II. Correctness & Testing — PASS**: Subprocess tests cover the complete workflow, exact status 1, repaired status 0, diagnostics, cleanup, retention, argument validation, outside-checkout use, repeatability, failures, and byte-level preservation of pre-existing tracked and untracked parent files.
- **III. Architectural Boundaries — PASS**: Assets remain under `examples/`, `scripts/`, tests, docs, and feature specs. `src/instrproof`, project CI, and the feature 006 fixture remain unchanged.
- **IV. Security & Failure Handling — PASS**: The runner accepts only no argument or `--keep`, avoids `eval`, uses fixed argument-safe commands, validates inputs and outcomes, isolates writes, and cleans through traps.
- **V. Spec-Driven Change Discipline — PASS**: Every planned behavior traces to feature 007; all named exclusions remain outside the design.

**Post-design re-evaluation**: The runner contract preserves these boundaries. Test failure injection uses test-local `PATH` shims rather than a production hook or public command override. No violation requires justification.

## Project Structure

### Documentation (this feature)

```text
specs/007-presentation-ready-demo/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── demo-runner.md
└── tasks.md                 # created by /speckit-tasks
```

### Source Code (repository root)

```text
.
├── examples/demo-repo/
│   ├── AGENTS.md
│   ├── src/auth/service.py
│   └── tests/test_service.py
├── scripts/
│   ├── run-demo.sh
│   └── validate-release.sh        # unchanged
├── src/instrproof/                # unchanged
├── tests/integration/test_reproducible_demo.py
└── README.md
```

**Structure Decision**: Keep public presentation assets separate from production package code and feature 006 validation. The template is immutable input; the runner mutates only its temporary copy. Tests exercise the public shell interface instead of reconstructing its steps.

## Implementation Strategy

### Minimal baseline template

- Store one inline claim in `AGENTS.md`: `Authentication logic is implemented in \`src/auth/service.py\`.`
- Provide a standard-library authentication function and one `unittest` importing `src.auth.service`.
- Avoid extra instruction files, path claims, links, package manifests, and `.git` content so inspection returns exactly one contract.
- Treat template bytes as immutable; every mutation follows a copy into a unique temporary directory.

### Runner initialization and isolation

- Use a Bash shebang and strict mode, resolve project root from the script path, and accept only no arguments or exactly `--keep`; reject other input with status 2 before meaningful setup.
- Validate Git, uv, required template files, and the project CLI. Preserve the existing before/after parent `git status --porcelain` comparison so path and status changes remain explicit while allowing pre-existing dirty state only when it is unchanged.
- Enumerate the parent snapshot with the argument-safe, NUL-delimited equivalent of `git ls-files -z --cached --others --exclude-standard`. For every returned repository-relative path, record a canonical entry containing the path, file type, a SHA-256 digest of complete regular-file bytes, the exact symlink target when applicable, and the executable mode where relevant. Do not use modification times or sizes as equality evidence.
- Store the initial snapshot outside the parent repository, take the same snapshot again on normal exit, failure, and interruption before cleanup, and require exact equality of porcelain output, Git-visible path set, tracked contents, pre-existing untracked contents, file types, symlink targets, and relevant modes. Ignored files are outside the snapshot unless the demo directly targets one; the runner has no planned ignored-file target.
- Create a `mktemp -d` root, install exit/signal traps, copy template contents, initialize Git quietly, configure local author values, commit, tag the commit `demo-base`, and record its object identity.
- Invoke only `uv run --project "$repo_root" instrproof ...` from the temporary repository. Do not import analysis code, set `PYTHONPATH`, use `eval`, or execute user-provided strings.

### Stable three-stage presentation

- Emit the three specified labels exactly once and print concise `$ ...` commands or bounded relevant diffs; suppress routine setup and temporary details.
- Stage 1 runs `python -m unittest discover -s tests` and `instrproof check`; require status 0, one verified total, `PathExists`, `AGENTS.md`, and `src/auth/service.py`.
- Stage 2 uses `git mv` to `src/auth/auth_service.py`, updates the test import, proves `AGENTS.md` is unchanged and the old path absent, displays source/test changes, and reruns application tests.
- Capture broken `diff --base demo-base --ci` streams and status with an explicit conditional. Require status 1, empty stderr, exactly one regression, `AGENTS.md`, and one `PathExists(src/auth/service.py)` diagnostic.
- Stage 3 replaces only the old claim target in `AGENTS.md`, proves the file and new claim remain, verifies `demo-base` still resolves to the recorded commit, shows the instruction diff, and reruns tests and the same comparison.
- Require status 0, empty stderr, `1 baseline contracts checked.`, and `No instruction contract regressions.`. Print stable broken/repaired status lines and a plain-language final explanation.

### Cleanup and retention

- Default traps delete only the validated `mktemp` root on every exit using an explicit safe target; never delete the project root or an unresolved path.
- Track successful repository initialization separately. Before it completes, even `--keep` cleans partial setup; afterward, `--keep` preserves attributable final or failed state without changing the failure status.
- Successful keep mode prints exactly one final `Retained demo repository: <absolute-path>` line and preserves `.git`, `demo-base`, the moved source, repaired instruction, and passing test.
- Signal handling performs cleanup and exits nonzero without background processes.

### Automated validation

- Invoke the public runner only through subprocess with captured text; do not reproduce its Git workflow in tests.
- Assert stage labels/count/order, baseline contract, source, target, exact regression count, statuses, same BASE, final explanation, cleanup, and exact parent snapshots covering porcelain, Git-visible paths, tracked/untracked bytes, file types, symlink targets, and executable modes.
- Create one collision-resistant, test-specific untracked sentinel in the parent repository only after proving its path is unused; write known nonempty bytes, retain those exact bytes, run the complete demo, and assert the same path and bytes remain. In the same test, retain bytes from at least one stable tracked file such as `README.md` or the demo template and require equality after execution.
- Remove only the test-created sentinel in a `finally` path that cannot overwrite the original demo assertion or subprocess failure. Never delete, rewrite, or normalize any unrelated untracked file during test cleanup.
- Parse keep mode's single absolute path, inspect its Git tag and repaired state, rerun documented comparisons, and safely remove only that test-owned directory.
- Invoke from a neutral directory and compare three default outputs, normalizing only documented variable values. Keep normal output free of paths/hashes where possible.
- Test status-2 arguments and stage failures with test-local `PATH` shims; do not add a production command override.
- Run focused tests followed by the full suite to preserve the 285-test baseline.

### Documentation

- Add `Reproducible demo` near Usage with prerequisites, `./scripts/run-demo.sh`, three-stage meaning, expected status 1, runtime, offline behavior, and checkout isolation.
- Document `--keep`, its retained-path marker, inspection of history/status/files, manual comparisons using the project-root invocation, and user-owned cleanup.
- Reference rather than duplicate release-readiness docs; leave CI and feature 006 documentation unchanged.

## Validation Approach

1. Run template application tests and `instrproof check`; assert exactly one expected contract.
2. Run focused runner integration tests covering default, keep, invalid arguments, outside checkout, failures, isolation, cleanup, and three-run equivalence.
3. Run the demo manually and verify concise ordered output and completion under 30 seconds without network after setup.
4. Run the full suite and confirm the prior 285 tests plus new tests pass.
5. Verify the parent porcelain state and canonical Git-visible snapshot are identical before/after, including a pre-existing untracked sentinel and a stable tracked file, then verify `scripts/validate-release.sh`, `.github/workflows/ci.yml`, and `src/instrproof` remain unchanged in behavior and scope.
6. Run `git diff --check`, inspect diff/status, and remove only feature-created temporary residue.
