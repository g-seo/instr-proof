# Implementation Plan: Require Baseline Contracts

**Branch**: `[009-require-contracts]` | **Date**: 2026-08-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-require-contracts/spec.md`

## Summary

Add an opt-in `--require-contracts` argument only to `instrproof diff`. Keep `compare_repository()` and `ComparisonResult` unchanged, invoke comparison exactly once, and evaluate the policy in `cli.py` only after a complete result exists. If the authoritative deduplicated baseline count is zero, emit the exact normal or CI analysis error to stderr and return status 2 before any result formatting; otherwise use the existing PASS/regression path unchanged.

## Technical Context

**Language/Version**: Python 3.12+; tested on 3.12, 3.13, and 3.14

**Primary Dependencies**: Python standard library only at runtime, including `argparse`; Hatchling for packaging

**Storage**: N/A; invocation-local CLI arguments and the existing immutable comparison result

**Testing**: pytest unit/integration tests, temporary Git repositories, exact stream/status assertions, wheel and source-distribution installation, public demo, and release validation

**Target Platform**: Existing cross-platform Python CLI with Git; supported CI and validation workflows on Linux

**Project Type**: Single Python package and CLI

**Performance Goals**: Preserve one repository comparison per diff invocation and add only a constant-time count check after analysis

**Constraints**: Disabled by default; exact stderr text; no stdout on requirement failure; no analysis, model, identity, dependency, package metadata, demo, or CI-structure changes; deterministic existing output

**Scale/Scope**: One production CLI module, focused integration and artifact-validation tests, README, and feature design artifacts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Pre-design gate

- **I. Simplicity & Necessity — PASS**: One diff-scoped boolean argument and one post-analysis conditional satisfy the feature without a new abstraction, dependency, configuration source, or domain type.
- **II. Correctness & Testing — PASS**: Exact normal/CI streams and statuses, parser scope, nonempty compatibility, deduplication, concrete repository/source-data failures, single comparison, repeatability, all four installed-artifact outcomes, demo, release validation, and successful supported-runtime CI results all receive explicit coverage.
- **III. Architectural Boundaries — PASS**: Repository analysis remains in `compare_repository()`; the opt-in presentation/exit policy remains in `cli.py`; existing formatters and models keep their responsibilities.
- **IV. Security & Failure Handling — PASS**: Existing repository and configuration errors remain explicit and take precedence; the new completed-result failure is actionable, sanitized, and written only to stderr.
- **V. Spec-Driven Change Discipline — PASS**: The plan maps directly to FR-001–FR-028 and does not alter requirements, analysis semantics, or out-of-scope surfaces.

### Post-design gate

- **I — PASS**: [research.md](research.md) selects the smallest direct CLI change and rejects synthetic regressions or analyzer changes.
- **II — PASS**: [contracts/cli.md](contracts/cli.md) and [quickstart.md](quickstart.md) define exact results across the full decision table, concrete failure-precedence fixtures, four-outcome artifact parity, and successful supported-runtime evidence.
- **III — PASS**: [data-model.md](data-model.md) keeps `ComparisonResult` authoritative and documents only transient CLI policy state; no production model changes are planned.
- **IV — PASS**: The policy is unreachable until existing exception handling has produced a valid result, preserving attributable and sanitized errors.
- **V — PASS**: No unresolved clarification, architectural deviation, or unjustified complexity remains after design.

## Project Structure

### Documentation (this feature)

```text
specs/009-require-contracts/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
└── tasks.md                 # generated later by /speckit-tasks
```

### Source Code (repository root)

```text
src/instrproof/
├── cli.py                   # diff argument and post-analysis policy
├── compare.py               # unchanged comparison orchestration
└── models.py                # unchanged ComparisonResult and identities

tests/
├── integration/test_cli_diff.py
├── integration/test_cli_ci.py
├── integration/test_cli_installation.py
├── integration/test_release_validation.py
├── integration/test_reproducible_demo.py
└── unit/test_readme_release_docs.py

README.md
scripts/
├── run-demo.sh              # unchanged public demonstration
└── validate-release.sh      # artifact parity fixture additions only
```

**Structure Decision**: Preserve the existing single-package layout. Production behavior changes only in `src/instrproof/cli.py`; tests and release smoke fixtures extend existing files, and the public demo stays unchanged.

## Phase 0: Research Decisions

[research.md](research.md) resolves argument ownership, the post-analysis policy boundary, exact output construction, error precedence, concrete failure fixtures, comparison call count, deduplicated-count authority, deterministic coverage, four-outcome artifact equivalence, supported-runtime evidence, and documentation scope. There are no remaining `NEEDS CLARIFICATION` items.

## Phase 1: Design and Contracts

- [data-model.md](data-model.md) documents the unchanged `ComparisonResult`, transient diff-policy input, derived requirement outcome, decision table, invariants, and state transitions.
- [contracts/cli.md](contracts/cli.md) defines command grammar, exact normal/CI streams, status semantics, help isolation, concrete failure precedence, installed-artifact equivalence, and compatibility.
- [quickstart.md](quickstart.md) provides focused automated commands, copy-and-run zero/nonzero fixtures, four-outcome artifact validation, and supported-runtime completion evidence without changing the public demo story.

## Implementation Strategy

1. Add parser/help tests proving diff accepts `--require-contracts` in normal and CI forms and check/explain reject it; then add the boolean argument only to the diff parser.
2. Add exact-output tests for zero contracts with and without the option. After the existing `try`/`except` comparison block, test `args.require_contracts` and `result.baseline_contract_count == 0`; emit the exact mode-specific error to stderr and return 2 before calling either result formatter.
3. Add one-contract PASS, one-contract regression, multiple-contract deterministic, duplicate-to-one, and comparison-call-count tests. Reuse existing real-repository fixtures and repeat deterministic cases three times.
4. Extend existing BASE/config/internal failure cases with the flag. Include unavailable BASE, malformed BASE config, malformed HEAD config, an unreadable instruction source, malformed required repository data, and unexpected CI failure; assert each old exact error remains, stdout stays empty, and the zero-contract text is absent.
5. Extend installed-artifact/release smoke coverage so wheel and source distribution run the same four strict inputs: non-regressing comparison (status 0), confirmed regression (status 1), zero-contract requirement failure (status 2), and unavailable-BASE analysis error (status 2). Capture and compare status, stdout, and stderr byte-for-byte for every outcome.
6. Update README default/strict coverage guidance and consumer workflow, retain the demo command, then run focused suites, the full suite, demo, and release validation. Require successful CI suite results on Python 3.12, 3.13, and 3.14 before completion; inspecting the matrix alone is insufficient.

## Verification

```sh
uv run pytest tests/integration/test_cli_diff.py
uv run pytest tests/integration/test_cli_ci.py
uv run pytest tests/integration/test_cli_installation.py
uv run pytest tests/integration/test_release_validation.py
uv run pytest tests/integration/test_reproducible_demo.py
uv run pytest tests/unit/test_readme_release_docs.py
uv run pytest
./scripts/run-demo.sh
./scripts/validate-release.sh
```

Verify `.github/workflows/ci.yml` retains Python 3.12, 3.13, and 3.14, then require a successful complete-suite CI result for each version before completion. CI remains authoritative for those distinct runtime executions; matrix inspection alone does not satisfy the gate. Before completion inspect `git diff`, `git diff --check`, and `git status`, ensuring no analysis module, domain model, demo logic, package metadata, dependency, or CI-structure change is included.

## Complexity Tracking

No constitution violations require justification.
