# Implementation Plan: CI Regression Checks

**Branch**: `005-ci-regression-checks` | **Date**: 2026-08-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-ci-regression-checks/spec.md`

## Summary

Extend the existing `diff` parser with `--ci`, run the unchanged `compare_repository()` pipeline exactly once, and select either the existing formatter or a deterministic CI formatter over the returned `ComparisonResult`. CI classification maps a completed empty result to status `0`, a completed non-empty result to status `1`, and analysis failures to status `2`. Existing `ContractIdentity` ordering remains authoritative. A narrow BASE-resolution error subtype preserves the requested ref for actionable CI diagnostics without adding fallback or fetch behavior.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: Python standard library (`argparse`, `dataclasses`, `enum`, `pathlib`, `subprocess`); Git command-line client; no new runtime dependency

**Storage**: N/A; reads Git objects and the current working tree without persistent feature state

**Testing**: pytest 8+, existing temporary local Git repository fixtures, `uv run pytest`

**Target Platform**: Non-interactive command-line environments with Python 3.12+ and Git, especially Linux-based pull-request CI; existing local CLI platforms remain supported

**Project Type**: Single-package Python CLI

**Performance Goals**: CI mode adds only linear formatting over the existing comparison result; one invocation with at least 100 regressions emits all results without a second repository analysis

**Constraints**: Deterministic text and ordering; exact statuses `0`/`1`/`2`; no network access or automatic fetching; no new dependency; no change to analysis semantics or non-CI output; no stack trace in expected CI error output

**Scale/Scope**: One CLI option, one CI formatter/classification path, one precise repository error subtype, focused unit/integration coverage, and one minimal GitHub Actions documentation example

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Pre-design gate

- **I. Simplicity & Necessity — PASS**: The existing CLI, comparison function, result model, regression ordering, and Git boundary are reused. The only new error type solves the concrete need to retain the unavailable ref for CI guidance. No dependency or provider abstraction is introduced.
- **II. Correctness & Testing — PASS**: The plan includes exact-output and exit-status tests for pass, both contract types, multiple regressions, deterministic ordering, missing BASE, repository failures, internal failures, and compatibility with features 001–004.
- **III. Architectural Boundaries — PASS**: Regression logic remains in `compare.py`, Git operations remain in `repository.py`, domain results remain in `models.py`, and CI presentation/process behavior remains in `cli.py`.
- **IV. Security & Failure Handling — PASS**: BASE input continues through argument parsing and exact `git rev-parse --verify --end-of-options`; known failures preserve actionable context, unexpected failures suppress sensitive exception details, and failures never become regressions.
- **V. Spec-Driven Change Discipline — PASS**: Every planned change traces to requirements FR-001–FR-027 and does not extend out-of-scope behavior.

### Post-design gate

- **PASS**: Phase 1 introduces no second analysis path, persistence, provider integration, or dependency. The CLI contract, data model, and quickstart preserve all pre-design boundaries. No constitutional violation requires justification.

## Project Structure

### Documentation (this feature)

```text
specs/005-ci-regression-checks/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md             # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
src/instrproof/
├── cli.py                # Add --ci dispatch, CI formatter, and status/error mapping
├── compare.py            # Reuse unchanged comparison pipeline and ordering
├── models.py             # Reuse ComparisonResult and Regression structures
└── repository.py         # Retain exact BASE-resolution context with a narrow error type

tests/
├── integration/
│   ├── test_cli_ci.py    # CI output, status, errors, ordering, and checkout scenarios
│   ├── test_cli_diff.py  # Existing non-CI compatibility suite
│   └── test_cli_inspection.py # Existing check/explain compatibility suite
└── unit/
    ├── test_compare.py   # Existing regression decisions and ordering
    └── test_models.py    # Existing identity/result invariants

README.md                 # --ci, BASE availability, statuses, and Actions example
```

**Structure Decision**: Preserve the existing single-package CLI layout. CI surface coverage belongs in `tests/integration/test_cli_ci.py`, where returned status and stdout/stderr can be verified together; no additional production or unit-test module is planned. The formatter and classification remain small presentation concerns in `cli.py`. `compare.py` and `models.py` should remain behaviorally unchanged because they already provide the complete, sorted, structured result required by both modes.

## Complexity Tracking

No constitution violations or complexity exceptions.
