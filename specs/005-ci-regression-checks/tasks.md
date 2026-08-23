# Tasks: CI Regression Checks

**Input**: Design documents from `/specs/005-ci-regression-checks/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Automated tests are required by the specification and constitution. Within each story, write the listed tests first and confirm they fail for the expected missing behavior before implementing.

**Organization**: Tasks are grouped by user story so each increment has an explicit independent test and traceable implementation scope.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file and has no dependency on another incomplete task
- **[Story]**: Maps the task to a user story from spec.md
- Every task names the exact file or repository path it affects

## Phase 1: Setup and Baseline

**Purpose**: Confirm the feature starts from a passing features 001–004 baseline before changing shared CLI behavior.

- [X] T001 Run `uv run pytest` against `tests/` before modifying `src/instrproof/`; if a pre-existing failure occurs, stop and report its test path and output in the implementation handoff rather than creating a feature file for it

**Checkpoint**: The existing regression, discovery, inspection, and CLI suites pass, or any unrelated baseline failure is documented before feature work begins.

---

## Phase 2: Foundational Review

**Purpose**: Confirm the existing shared seam; no new foundational component is required.

- [X] T002 Verify `ComparisonResult.baseline_contract_count`, complete regression tuples, and `ContractIdentity` sorting in `src/instrproof/models.py` and `src/instrproof/compare.py`, updating `specs/005-ci-regression-checks/plan.md` first if implementation reveals a required architectural change

**Checkpoint**: `compare_repository()` remains the single analysis entry point for both modes, and no CI-specific analysis pipeline is introduced.

---

## Phase 3: User Story 1 - Gate Pull Requests on Regressions (Priority: P1) 🎯 MVP

**Goal**: Add `instrproof diff --base <base-ref> --ci` as a thin consumer of the existing comparison result with exact PASS/REGRESSION status mapping and complete regression reporting.

**Independent Test**: Run CI mode against local comparisons containing zero regressions, one PathExists regression, one PackageScriptExists regression, multiple regressions, and coordinated instruction updates/removals; verify statuses `0` or `1` and the same regression decisions as normal diff.

### Tests for User Story 1

- [X] T003 [US1] Add failing CLI tests for `--ci` parsing, PASS output with exact zero and nonzero baseline counts, the zero-regression statement, and status `0` in `tests/integration/test_cli_ci.py`
- [X] T004 [US1] Add failing CLI tests for one PathExists regression, one PackageScriptExists regression, multiple mixed regressions, all-regressions reporting, and status `1` independent of count in `tests/integration/test_cli_ci.py`
- [X] T005 [US1] Add failing compatibility cases proving coordinated instruction updates/removals retain existing PASS decisions and CI invokes `compare_repository()` once in `tests/integration/test_cli_ci.py`

### Implementation for User Story 1

- [X] T006 [US1] Add the `--ci` option and route both diff modes through one `compare_repository()` call in `src/instrproof/cli.py`
- [X] T007 [US1] Implement PASS/REGRESSION classification and the complete CI result formatter over `ComparisonResult` in `src/instrproof/cli.py`
- [X] T008 [US1] Run `uv run pytest tests/integration/test_cli_ci.py` and verify the User Story 1 cases in `tests/integration/test_cli_ci.py` pass independently

**Checkpoint**: CI mode is a usable pull-request gate for completed comparisons, reports every established regression, and never derives exit status from regression count.

---

## Phase 4: User Story 2 - Receive Stable, Actionable Build Output (Priority: P2)

**Goal**: Guarantee exact concise output, complete diagnostic fields, accurate counts, and stable domain ordering across repeated runs.

**Independent Test**: Repeat an unchanged mixed BASE/HEAD comparison at least three times and verify byte-equivalent output ordered by normalized source, contract type, and target, including distinct contracts with identical targets across sources.

### Tests for User Story 2

- [X] T009 [US2] Add failing exact-output tests for singular/plural totals, instruction source, optional HEAD line, contract type, normalized target, and no duplicate diagnostics in `tests/integration/test_cli_ci.py`
- [X] T010 [US2] Add failing ordering tests covering different sources, the same source, both contract types, identical targets from distinct sources, and three repeated invocations in `tests/integration/test_cli_ci.py`
- [X] T011 [US2] Add a failing scale case proving 100 regressions are each emitted once with an accurate total and status `1` in `tests/integration/test_cli_ci.py`

### Implementation for User Story 2

- [X] T012 [US2] Align CI formatting with the exact blocks and tuple-preserving ordering defined in `specs/005-ci-regression-checks/contracts/cli.md` by updating `src/instrproof/cli.py`
- [X] T013 [US2] Run `uv run pytest tests/integration/test_cli_ci.py` and verify all deterministic-output and ordering cases in `tests/integration/test_cli_ci.py` pass independently

**Checkpoint**: Equivalent comparisons produce equivalent build-log output, every regression appears exactly once, and diagnostic lines remain presentation-only.

---

## Phase 5: User Story 3 - Distinguish Analysis Failure from Regression (Priority: P3)

**Goal**: Return status `2` with actionable, non-regression diagnostics whenever exact BASE resolution or repository analysis cannot complete.

**Independent Test**: Exercise invalid and locally unavailable BASE refs, a shallow-checkout-like repository without the requested ref, malformed required data, repository inspection failure, and an injected unexpected exception; verify each is stderr-only analysis-error output with status `2` and no regression framing.

### Tests for User Story 3

- [X] T014 [P] [US3] Add failing repository tests for `BaseReferenceError` retaining the exact requested ref while preserving `RepositoryError` compatibility in `tests/integration/test_repository.py`
- [X] T015 [P] [US3] Add failing CI tests for invalid BASE, unavailable remote-tracking BASE, and a local shallow-checkout-like missing-ref fixture without network access in `tests/integration/test_cli_ci.py`
- [X] T016 [US3] Add failing CI tests for malformed required repository data, injected `RepositoryError`, and unexpected internal failure mapping to distinct status-`2` analysis errors with no partial regression output in `tests/integration/test_cli_ci.py`

### Implementation for User Story 3

- [X] T017 [US3] Add the narrow `BaseReferenceError` subtype and wrap only exact `resolve_base()` failures without fallback or fetch behavior in `src/instrproof/repository.py`
- [X] T018 [US3] Add CI-only BASE guidance, expected repository-error formatting, and sanitized unexpected-error handling while preserving non-CI error behavior in `src/instrproof/cli.py`
- [X] T019 [US3] Run `uv run pytest tests/integration/test_repository.py tests/integration/test_cli_ci.py` and verify all User Story 3 failure cases report status `2`, never `1`

**Checkpoint**: Missing refs and all other incomplete analyses are clearly distinguishable from confirmed regressions, with no hidden network or revision substitution.

---

## Phase 6: User Story 4 - Adopt CI Without Disrupting Existing Commands (Priority: P4)

**Goal**: Document a reliable GitHub Actions required check and prove all pre-existing command surfaces remain unchanged when CI mode is absent.

**Independent Test**: Validate the documented checkout/install/run sequence against a locally available `origin/main`, then run the existing diff, check, and explain suites and compare their expected output and statuses with the pre-feature baseline.

### Tests for User Story 4

- [X] T020 [US4] Add compatibility assertions that non-CI diff output/errors and `check`/`explain` dispatch remain unchanged after CI execution in `tests/integration/test_cli_ci.py`

### Implementation for User Story 4

- [X] T021 [US4] Document `--ci`, PASS/REGRESSION/ANALYSIS ERROR output, statuses `0`/`1`/`2`, exact BASE availability, and shallow-checkout failure behavior in `README.md`
- [X] T022 [US4] Add a minimal GitHub Actions pull-request workflow example with sufficient checkout history and `instrproof diff --base origin/main --ci` in `README.md`
- [X] T023 [US4] Run `uv run pytest tests/integration/test_cli_diff.py tests/integration/test_cli_inspection.py tests/integration/test_cli_ci.py` and verify normal diff, check, explain, and CI behavior together

**Checkpoint**: Maintainers can configure a normal required check, and every existing non-CI command retains its prior observable behavior.

---

## Phase 7: Polish and Cross-Cutting Validation

**Purpose**: Verify the complete feature, compatibility guarantees, documentation, and scoped repository state.

- [X] T024 [P] Review `src/instrproof/cli.py` and `src/instrproof/repository.py` for accidental duplicate analysis, output nondeterminism, leaked exception detail, automatic fetch behavior, or unnecessary abstractions
- [X] T025 [P] Validate every documented command and expected result in `specs/005-ci-regression-checks/quickstart.md` against `README.md` and the implemented CLI
- [X] T026 Run the complete `uv run pytest` suite under `tests/` and confirm all features 001–004 retain their established outcomes
- [X] T027 Inspect `git diff --check`, `git diff`, and `git status --short` for the repository and remove no user-owned or unrelated changes

---

## Dependencies and Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and establishes the compatibility baseline.
- **Foundational Review (Phase 2)**: Depends on T001 and confirms the shared result seam before test or implementation changes.
- **User Story 1 (Phase 3)**: Depends on T002 and establishes the `--ci` path used by later stories.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because it hardens the CI formatter introduced there.
- **User Story 3 (Phase 5)**: Depends on User Story 1 for CI dispatch but its repository error tests T014 and CLI error tests T015 can be written in parallel.
- **User Story 4 (Phase 6)**: Depends on User Stories 1–3 so documentation and compatibility validation describe the finished behavior.
- **Polish (Phase 7)**: Depends on all selected user stories.

### User Story Dependencies

```text
Setup -> Foundational Review -> US1 (MVP)
                                  |-> US2 deterministic diagnostics
                                  |-> US3 analysis-error separation
                                  `-> US4 documentation/compatibility (after US2 + US3)
```

- **US1 (P1)**: First independently deliverable increment; no other story dependency after foundation.
- **US2 (P2)**: Extends US1 presentation without changing its analysis or status decisions.
- **US3 (P3)**: Extends US1 failure handling; may proceed alongside US2 after US1 completes.
- **US4 (P4)**: Documents and validates the integrated US1–US3 behavior.

### Within Each User Story

- Write tests first and confirm they fail for the intended missing behavior.
- Implement only the production behavior needed to pass that story's tests.
- Run the story's focused test command at its checkpoint.
- Do not change `src/instrproof/compare.py` or `src/instrproof/models.py` unless a requirement or architecture change is first recorded in the active Spec Kit artifacts.

### Parallel Opportunities

- After US1, US2 and US3 can proceed in parallel because deterministic completed-result output and typed failure handling are separable.
- T014 and T015 can run in parallel because they modify different test files.
- T021 and T022 are sequential because both modify `README.md`.
- T024 and T025 can run in parallel because one reviews production code while the other validates documentation.

---

## Parallel Example: User Story 3

```text
Task T014: Add BaseReferenceError repository tests in tests/integration/test_repository.py
Task T015: Add missing-ref and shallow-checkout-like CLI tests in tests/integration/test_cli_ci.py
```

After both tests fail as expected, complete T017 before T018 because CI formatting consumes the repository error subtype.

## Implementation Strategy

### MVP First: User Story 1

1. Complete T001–T002 to establish the baseline and shared seam.
2. Write and fail T003–T005.
3. Implement T006–T007 using one `compare_repository()` result.
4. Complete T008 and stop to validate statuses `0` and `1` independently.

### Incremental Delivery

1. **US1**: Deliver a functional CI gate over the existing engine.
2. **US2**: Lock down deterministic, complete, actionable output.
3. **US3**: Add exact missing-BASE and analysis-error classification.
4. **US4**: Document required-check adoption and verify compatibility.
5. **Polish**: Run the full features 001–004 suite and repository checks.

### Scope Controls

- Do not add a second regression engine, subprocess invocation of InstrProof, output parsing, CI provider abstraction, network fetch, or new formatting dependency.
- Keep `--ci` out of discovery, extraction, promotion, identity, survival, validation, and comparison APIs.
- Treat every analysis failure as status `2`; never encode regression quantity into status.
- Preserve all user-owned changes and restrict implementation to the files named by these tasks unless an artifact is updated first.

## Notes

- `[P]` means different files or independently draftable sections with no incomplete dependency.
- `[USn]` labels provide direct traceability to the specification's user stories.
- Commit after each task or coherent test/implementation pair when using version control.
- Stop at any checkpoint to validate the current increment independently.
