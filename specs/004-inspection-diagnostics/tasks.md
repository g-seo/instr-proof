# Tasks: Inspection and Diagnostics

**Input**: Design documents from `/specs/004-inspection-diagnostics/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Automated tests are required. New behavior tests must fail for the intended missing capability before implementation; existing compatibility tests must continue passing throughout.

**Organization**: Shared candidate-evidence inspection is foundational. User stories then consume that single result path independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Separate-file work with no incomplete dependency
- **[Story]**: Maps to US1, US2, or US3
- Every task names an exact file

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the unchanged feature 001–003 baseline.

- [X] T001 Run the complete suite configured in `pyproject.toml` and confirm all 195 pre-feature tests documented in `specs/004-inspection-diagnostics/quickstart.md` pass before source changes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement the single structured evidence-inspection path reused by promotion, check, and explain.

**⚠️ CRITICAL**: This phase blocks all user stories.

- [X] T002 [P] Add failing model tests for `CurrentOccurrence`, `CurrentAnalysisResult`, `SourceLocationSelector`, PRESENT/MISSING invariants, ordering inputs, and neutral contract `source_location` aliases in `tests/unit/test_models.py`
- [X] T003 Implement the minimal immutable occurrence, analysis-result, and selector values plus backward-compatible neutral location aliases without changing existing contract equality, hashes, constructors, or EvidenceState in `src/instrproof/models.py`
- [X] T004 Add failing unit tests for supported PathExists/PackageScriptExists PRESENT and MISSING occurrences, unsupported-input exclusion, evidence-once-per-identity, repeated-line retention, lazy script inspection, propagated repository failure, and unchanged promotion results in `tests/unit/test_compare.py`
- [X] T005 Implement `inspect_claim_occurrences`, promotion from inspected PRESENT identities, and shared current claim collection; refactor existing `promote_contracts` and `compare_repository` to consume these primitives without observable changes in `src/instrproof/compare.py`

**Checkpoint**: The shared primitive distinguishes PRESENT, MISSING, unsupported absence, and analysis failure, while all existing promotion/comparison tests pass.

---

## Phase 3: User Story 1 - Inspect Current Verified Contracts (Priority: P1) 🎯 MVP

**Goal**: Provide `instrproof check` as a deterministic view of distinct current PRESENT contracts.

**Independent Test**: Combine valid and missing path/script candidates across root, nested, configured, repeated, and distinct-source cases; check must list only PRESENT identities with correct source/type/target/state/order/count and succeed at zero.

### Tests for User Story 1

- [X] T006 [P] [US1] Add failing unit tests for `analyze_current_repository`, PRESENT-only verified promotion, representative diagnostic location, duplicate identity count, distinct-source identity, deterministic ordering, and zero verified contracts in `tests/unit/test_compare.py`
- [X] T007 [P] [US1] Add failing CLI tests for PathExists, PackageScriptExists, multiple/root/nested/configured sources, MISSING exclusion, unsupported/ambiguous exclusion, exact total, stable order, zero result, and analysis errors in `tests/integration/test_cli_inspection.py`

### Implementation for User Story 1

- [X] T008 [US1] Implement `analyze_current_repository` and the verified-contract projection from shared inspected occurrences using existing contract models and lazy HEAD evidence in `src/instrproof/compare.py`
- [X] T009 [US1] Add the `check` argparse command, structured dispatch, deterministic formatter, zero output, and status/error mapping without touching the diff formatter in `src/instrproof/cli.py`

**Checkpoint**: `check` independently delivers the MVP and never lists a MISSING occurrence.

---

## Phase 4: User Story 2 - Explain a Current Instruction Occurrence (Priority: P2)

**Goal**: Explain all supported occurrences at an exact source line with exact evidence and PRESENT/MISSING state.

**Independent Test**: Explain present and missing path/script occurrences from root, nested, and configured sources; verify exact fields, all deterministic same-line matches, repeated-line lookup, invalid selectors, no-match, and analysis failures without BASE/HEAD output.

### Tests for User Story 2

- [X] T010 [P] [US2] Add failing unit tests for final-colon selector parsing, path normalization, positive-line validation, exact source-line filtering, all distinct same-line matches, repeated occurrence lookup, identity ordering, evidence references, and no-match result in `tests/unit/test_compare.py`
- [X] T011 [P] [US2] Add failing CLI tests for PRESENT/MISSING PathExists and PackageScriptExists, nested/configured lookup, exact evidence text, invalid source/line, no match, multiple matches, injected internal failure, required-data failure, and no BASE/HEAD fields in `tests/integration/test_cli_inspection.py`

### Implementation for User Story 2

- [X] T012 [US2] Implement selector parsing and exact occurrence lookup over `CurrentAnalysisResult.occurrences`, returning every identity-sorted match regardless of PRESENT/MISSING in `src/instrproof/compare.py`
- [X] T013 [US2] Add the `explain` argparse command, multi-section formatter, no-match status 1, invalid/analysis/internal-error status 2, and current-only structured dispatch in `src/instrproof/cli.py`

**Checkpoint**: `explain` independently handles supported PRESENT/MISSING occurrences and never requires verified promotion.

---

## Phase 5: User Story 3 - Preserve Existing Contract and Regression Semantics (Priority: P3)

**Goal**: Prove identity/location separation, structural pipeline reuse, and unchanged features 001–003 behavior.

**Independent Test**: Move/repeat equal claims, verify unchanged identity with updated locations, and run all existing extraction, normalization, discovery, repository, promotion, comparison, regression, CLI diff, and performance cases unchanged.

### Tests for User Story 3

- [X] T014 [P] [US3] Add identity/location regression tests proving line movement preserves equality/hash/deduplication, repeated lines remain lookupable, and equal targets from different sources remain distinct in `tests/unit/test_compare.py`
- [X] T015 [P] [US3] Add CLI dispatch compatibility tests proving check/explain installation leaves exact existing diff passing, regression, ordering, error, output, and status behavior unchanged in `tests/integration/test_cli_diff.py`

### Implementation for User Story 3

- [X] T016 [US3] Verify and enforce in `src/instrproof/compare.py` that `compare_repository` and `analyze_current_repository` call the shared claim collector, `promote_contracts` and current analysis call the shared evidence inspector/promotion helper, and no command-specific discovery, extraction, or validation loop remains

**Checkpoint**: All user stories pass through one evidence path and the complete pre-feature suite remains unchanged.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete documentation, reproducible performance evidence, and final validation.

- [X] T017 [P] Document check/explain usage, output, exact lookup, PRESENT/MISSING semantics, zero/no-match outcomes, errors, current-only scope, and unchanged diff in `README.md`
- [X] T018 [P] Add the documented local fixture with exactly 100 discovered sources and 1,000 supported candidates, five-second assertion, monotonic timing, and diagnostic environment details while retaining the existing diff performance test in `tests/integration/test_performance.py`
- [X] T019 Run all manual scenarios in `specs/004-inspection-diagnostics/quickstart.md` and correct only specification-consistent discrepancies in that guide
- [X] T020 Run `uv run pytest` from `pyproject.toml` and resolve every new failure while preserving all 195 pre-feature assertions unchanged
- [X] T021 Inspect `git diff --check`, `git diff`, and `git status --short`, then correct only feature 004 changes that violate `specs/004-inspection-diagnostics/plan.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup**: Starts immediately.
- **Foundation**: Depends on T001 and blocks all story work.
- **US1**: Depends on T002–T005 and delivers the MVP.
- **US2**: Depends on T002–T005; test preparation can overlap US1, but shared-file implementation must be coordinated.
- **US3**: Depends on completed US1/US2 paths to verify structural reuse and compatibility.
- **Polish**: Depends on desired stories; T017 and T018 can run in parallel before T019–T021.

### User Story Dependencies

- **US1 (P1)**: No story dependency after foundation; recommended MVP.
- **US2 (P2)**: Uses the foundational `CurrentAnalysisResult` directly, not check output or verified-only contracts.
- **US3 (P3)**: Validates the integrated US1/US2 behavior against established semantics.

### Within Each User Story

- Add and fail new behavior tests before implementation.
- Keep existing compatibility tests passing after every refactor.
- Implement structured analysis before CLI formatting.
- Never modify extraction grammar, normalization, evidence scope, or identity for presentation convenience.
- Run focused unit/integration tests at every checkpoint.

### Parallel Opportunities

- T002 and later non-model investigation can proceed independently, but T003 precedes code using new values.
- T006 and T007 modify separate test files.
- T010 and T011 modify separate test files.
- T014 and T015 modify separate test files.
- T017 and T018 modify documentation and performance tests separately.
- US1/US2 test preparation may overlap after T005; serialize edits to `compare.py` and `cli.py`.

---

## Parallel Example: User Story 1

```text
Task T006: Current verified projection tests in tests/unit/test_compare.py
Task T007: Check CLI tests in tests/integration/test_cli_inspection.py
```

## Parallel Example: User Story 2

```text
Task T010: Selector/lookup tests in tests/unit/test_compare.py
Task T011: Explain CLI tests in tests/integration/test_cli_inspection.py
```

## Parallel Example: User Story 3

```text
Task T014: Identity/location tests in tests/unit/test_compare.py
Task T015: Diff compatibility tests in tests/integration/test_cli_diff.py
```

---

## Implementation Strategy

### MVP First: User Story 1

1. Complete T001–T005.
2. Write and fail T006–T007.
3. Implement T008–T009.
4. Validate check independently and stop if an MVP delivery is desired.

### Incremental Delivery

1. Establish the baseline and shared evidence-inspection foundation.
2. Deliver check over PRESENT verified identities.
3. Deliver explain over all supported current occurrences.
4. Prove identity, shared-pipeline, and diff compatibility.
5. Complete documentation, performance, manual validation, full tests, and diff review.

### Parallel Team Strategy

1. Complete T001–T005 together.
2. Parallelize each story's unit and CLI tests.
3. Serialize overlapping changes in `src/instrproof/compare.py` and `src/instrproof/cli.py`.
4. Complete T019–T021 after integration.

## Notes

- `[P]` marks separate-file work only.
- Unsupported text is excluded by existing extractors; do not create rejection diagnostics.
- MISSING occurrences are explainable but never verified.
- Analysis failures are errors and never evidence states.
- No task introduces BASE/HEAD explanation, persistence, dependencies, or duplicate contract classes.
