# Implementation Plan: Harden Path and Instruction Discovery

**Branch**: `[008-human-path-discovery]` | **Date**: 2026-08-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-human-path-discovery/spec.md`

## Summary

Close two precision defects without changing public contracts: recognize a narrow set of repository-root filenames in inline code before existing BASE-evidence promotion, and load `instrproof.json` independently from the resolved BASE tree and working tree. Comparison retains BASE-discovered paths and unions their still-readable HEAD files with normal HEAD discovery, deduplicating by `RepoPath`; current-only analysis, identity, survival rules, output, and statuses stay unchanged.

## Technical Context

**Language/Version**: Python 3.12+; tested on 3.12, 3.13, and 3.14

**Primary Dependencies**: Standard library only at runtime; argparse; Git subprocesses; Hatchling

**Storage**: Git object database for BASE and working-tree filesystem for HEAD; no persistence layer

**Testing**: pytest unit, temporary-Git integration, exact CLI compatibility, demo, and release validation

**Target Platform**: Existing cross-platform Python CLI behavior with Git; demo/release workflows on supported Linux

**Project Type**: Single Python package and CLI

**Performance Goals**: Preserve the existing under-five-second check/diff target for 100 instruction documents and 1,000 candidates; never load one HEAD source twice

**Constraints**: Deterministic, offline after setup, no runtime dependency, LLM, new contract type, identity/CLI change, checkout mutation, parser dependency, or filesystem evidence in extraction

**Scale/Scope**: Focused changes to three production modules, tests, README, and feature artifacts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Pre-design gate

- **I. Simplicity & Necessity — PASS**: One pure filename predicate, one shared configuration parser, state-specific loaders, and an ordered source union; no dependency, layer, entity, or alternate engine.
- **II. Correctness & Testing — PASS**: Both gaps have unit, repository/comparison integration, CLI, end-to-end, repeatability, demo, and release coverage.
- **III. Architectural Boundaries — PASS**: Lexical policy stays in `extract.py`, selection in `discovery.py`, access in `repository.py`, orchestration in `compare.py`, and presentation in `cli.py`.
- **IV. Security & Failure Handling — PASS**: Inputs remain validated at repository boundaries; BASE/HEAD failures are explicit attributable analysis errors.
- **V. Spec-Driven Change Discipline — PASS**: Design maps to FR-001–FR-032 and rejects identity, output, and scope expansion.

### Post-design gate

- **I — PASS**: `models.py` remains unchanged; retained sources are tuples of existing paths.
- **II — PASS**: Design covers grammar, configurations, carry-forward, deduplication, retirement, output, statuses, and state leaks.
- **III — PASS**: [data-model.md](data-model.md) uses existing boundaries and [contracts/cli.md](contracts/cli.md) preserves the interface.
- **IV — PASS**: One strict parser uses state labels; carried sources use normal HEAD readability/UTF-8 policy.
- **V — PASS**: No unresolved clarification or requirement deviation remains.

## Project Structure

### Documentation (this feature)

```text
specs/008-human-path-discovery/
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
├── extract.py       # nested grammar plus pure root filename classifier
├── discovery.py     # unchanged deterministic path/rule selection
├── repository.py    # shared config parser and state-specific access
├── compare.py       # state orchestration and comparison-only source union
├── models.py        # unchanged immutable values
└── cli.py           # unchanged dispatch/presentation

tests/
├── unit/test_extract.py
├── unit/test_compare.py
├── integration/test_repository.py
├── integration/test_cli_diff.py
├── integration/test_cli_ci.py
├── integration/test_performance.py
├── integration/test_reproducible_demo.py
└── integration/test_release_validation.py

README.md
scripts/run-demo.sh
scripts/validate-release.sh
```

**Structure Decision**: Preserve the existing single-package layout. Production changes are limited to `extract.py`, `repository.py`, and `compare.py`; no new production module is justified.

## Phase 0: Research Decisions

[research.md](research.md) resolves separate root grammar, ASCII-letter final extensions, exact allowlist, lexical/evidence separation, shared labelled config parsing, exact-tree reads, comparison-only carry-forward, deduplication, current-only compatibility, and validation.

## Phase 1: Design and Contracts

- [data-model.md](data-model.md) documents existing values, independent snapshots, transitions, union derivation, and ordering/read-once invariants.
- [contracts/cli.md](contracts/cli.md) defines grammar, configuration ownership, rule-removal behavior, error attribution, and unchanged output/status contracts.
- [quickstart.md](quickstart.md) provides focused checks and three copy-and-run Git fixtures.

## Implementation Strategy

1. Add failing extraction tests, then add an immutable extensionless set and independently testable pure predicate while preserving `_INLINE_PATH`, fenced masking, `_resolve`, and Markdown links.
2. Add failing repository tests, then refactor parsing into one bytes-plus-label function and expose independent BASE-tree and HEAD-working-tree loaders without checkout mutation.
3. Add failing comparison tests with an orchestration-level read counter, retain BASE paths, and build one sorted unique HEAD source union. Assert each physical HEAD source is loaded once, then pass claims to unchanged `compare_contracts`.
4. Update compatibility assertions and README, verify the unchanged Python 3.12–3.14 CI matrix, then run focused suites, the full suite three times, demo, and release validation.

## Verification

```sh
uv sync --locked --dev
uv run pytest tests/unit/test_extract.py
uv run pytest tests/integration/test_repository.py
uv run pytest tests/unit/test_compare.py
uv run pytest tests/integration/test_cli_diff.py
uv run pytest
uv run pytest
uv run pytest
./scripts/run-demo.sh
./scripts/validate-release.sh
```

Verify `.github/workflows/ci.yml` retains test-matrix entries for Python 3.12, 3.13, and 3.14; the CI run remains the authority for executing all three environments. Before completion inspect `git diff`, `git diff --check`, and `git status`.

## Complexity Tracking

No constitution violations require justification.
