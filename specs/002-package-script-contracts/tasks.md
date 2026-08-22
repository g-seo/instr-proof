# Tasks: Package Script Contracts (Revised Deterministic Grammar)

**Input**: Design documents from `/specs/002-package-script-contracts/`

**Prerequisites**: Revised plan.md, spec.md with FR-024–FR-027, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Automated tests are required by the feature specification and constitution. Write each story's tests first and confirm they fail for the intended missing behavior before implementing that story.

**Organization**: Tasks are grouped by user story so the second contract can be delivered incrementally through the existing InstrProof pipeline.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes a different file and has no dependency on another incomplete task in the same group
- **[Story]**: Maps the task to a user story from `spec.md`
- Every task names the exact file or directory it affects

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a clean feature-001 baseline before extending its architecture

- [x] T001 Run the existing PathExists test suite with `uv run pytest` and confirm the feature-001 baseline passes without modifying `tests/` or `src/instrproof/`
- [x] T002 Verify `pyproject.toml` remains Python 3.12+, standard-library-only at runtime, and requires no dependency changes for JSON manifest parsing

**Checkpoint**: Existing behavior is green and the no-new-dependency constraint is confirmed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Generalize the existing domain identity just enough for both contract types while keeping type-specific target validation

**⚠️ CRITICAL**: Complete this phase before implementing any user story.

- [x] T003 Add failing model tests for the closed `ContractType`, string-based normalized targets, `test:unit` script targets, cross-type inequality, and exclusion of source location, written syntax, and evidence states from equality/hash identity in `tests/unit/test_models.py`
- [x] T004 Extend the immutable domain model with `ContractType`, `PackageManager`, `PackageScriptClaim`, `PackageScriptExistsContract`, `SourceLocation`, and `EvidenceState` while adapting PathExists identity to normalized string targets in `src/instrproof/models.py`
- [x] T005 Update existing PathExists model and comparison test fixtures for the generalized identity target without changing their asserted behavior in `tests/unit/test_models.py` and `tests/unit/test_compare.py`
- [x] T006 Run `uv run pytest tests/unit/test_models.py tests/unit/test_compare.py` and resolve only foundational compatibility failures in `src/instrproof/models.py`

**Checkpoint**: Both typed contract identities can be represented, and all pre-existing PathExists domain tests still pass.

---

## Phase 3: User Story 1 - Detect Broken Package-Script Instructions (Priority: P1) 🎯 MVP

**Goal**: Promote a valid BASE package-script claim and report it when the unchanged HEAD claim points to a removed or renamed root script.

**Independent Test**: Commit an instruction containing `pnpm typecheck` and a root `package.json` defining `typecheck`, then verify unchanged evidence exits 0 while removing or renaming the script key exits 1 with a `PackageScriptExists` regression.

### Tests for User Story 1

- [x] T007 [P] [US1] Add failing extraction tests for all five supported forms and exact case-sensitive targets containing letters, digits, hyphen, underscore, colon, dot, and slash in `tests/unit/test_extract.py`
- [x] T008 [P] [US1] Add failing repository tests for reading BASE and HEAD root `package.json` script keys and ignoring script command-body values in `tests/integration/test_repository.py`
- [x] T009 [US1] Add failing promotion/comparison tests for script exists→exists, exists→removed, and exists→renamed with an unchanged claim in `tests/unit/test_compare.py`
- [x] T010 [US1] Add failing CLI tests for package-script pass, removal regression, rename regression, current HEAD source line, contract type/target, `base=present head=missing`, and exit codes in `tests/integration/test_cli_diff.py`

### Implementation for User Story 1

- [x] T011 [US1] Implement the five command forms and `[A-Za-z0-9][A-Za-z0-9._:/-]*` case-sensitive script normalization using existing fence masking and line tracking in `src/instrproof/extract.py`
- [x] T012 [US1] Implement cached BASE-tree and HEAD-working-tree root package manifest script access behind `GitRepository` in `src/instrproof/repository.py`
- [x] T013 [US1] Extend BASE promotion and HEAD evidence dispatch for `PackageScriptExists` within the existing comparison functions and `compare_repository` orchestration in `src/instrproof/compare.py`
- [x] T014 [US1] Format PackageScriptExists regressions with source, current line when available, type, target, and `base=present head=missing` while retaining command/summary/exit semantics in `src/instrproof/cli.py`
- [x] T015 [US1] Run the US1 unit and integration cases in `tests/unit/test_extract.py`, `tests/unit/test_compare.py`, `tests/integration/test_repository.py`, and `tests/integration/test_cli_diff.py` and fix only US1 regressions in `src/instrproof/`

**Checkpoint**: The first PackageScriptExists contract works end to end through `instrproof diff --base <base-ref>`.

---

## Phase 4: User Story 2 - Respect Intentional Instruction Changes (Priority: P2)

**Goal**: Preserve identity across prose, line, and package-manager syntax changes while retiring old contracts when targets or instructions change.

**Independent Test**: Starting from a valid BASE package contract, verify line/prose movement and `pnpm run typecheck`→`pnpm typecheck` preserve identity, while coordinated target rename or instruction removal produces no old-contract regression.

### Tests for User Story 2

- [x] T016 [P] [US2] Add failing unit tests for line/prose independence, package-manager syntax equivalence, diagnostic metadata inequality exclusion, lowest-line representative selection, target retirement, and instruction removal in `tests/unit/test_compare.py`
- [x] T017 [P] [US2] Add failing end-to-end tests for syntax-only survival, coordinated rename, removed instruction, moved-claim current location, and required PathExists diagnostic fields without changed PathExists regression decisions in `tests/integration/test_cli_diff.py`

### Implementation for User Story 2

- [x] T018 [US2] Update shared identity derivation, lowest-line duplicate location selection, HEAD surviving-claim lookup, and PRESENT→MISSING regression metadata without adding diagnostics to equality, hashing, survival, or ordering in `src/instrproof/compare.py`
- [x] T019 [US2] Ensure package manager, optional `run`, written command, prose, and line remain diagnostic-only during package claim construction in `src/instrproof/extract.py`
- [x] T020 [US2] Run the US2 cases in `tests/unit/test_compare.py` and `tests/integration/test_cli_diff.py` and fix only identity, survival, and shared diagnostic behavior in `src/instrproof/compare.py`, `src/instrproof/extract.py`, and `src/instrproof/cli.py`

**Checkpoint**: Intentional instruction changes retire old contracts and syntax/location-only edits preserve them.

---

## Phase 5: User Story 3 - Monitor Only High-Confidence Script Commands (Priority: P3)

**Goal**: Reject ambiguous command text and non-BASE scripts, use root evidence only, and distinguish missing evidence from malformed required evidence.

**Independent Test**: Mix supported commands, built-in/ambiguous forms, a script absent from BASE, and a script present only in a nested manifest; verify only clear root-validated candidates are monitored and malformed required root evidence exits 2.

### Tests for User Story 3

- [x] T021 [P] [US3] Add failing table-driven tests for every allowed manager-start boundary, every allowed end/prose delimiter, whitespace termination, `&&`/`||`/`;`/`|` termination, lone-`&` rejection, trailing-argument extraction, invalid adjacent characters, npm shorthand rejection, all 36 pnpm and 34 yarn shorthand exclusions, explicit-`run` bypass, multiple commands, and fenced commands in `tests/unit/test_extract.py`
- [x] T022 [P] [US3] Add failing repository tests for absent manifests, absent scripts members, nested manifests, invalid UTF-8/JSON/root shape/scripts shape, unreadable HEAD manifests, and lazy evidence access in `tests/integration/test_repository.py`
- [x] T023 [US3] Add failing CLI tests for nonexistent BASE scripts, root-only validation, malformed BASE/HEAD manifests, and path-only diffs with unrelated malformed manifests in `tests/integration/test_cli_diff.py`

### Implementation for User Story 3

- [x] T024 [US3] Implement the exact start/termination character sets, token-adjacency rejection, operator termination, frozen `PNPM_SHORTHAND_EXCLUSIONS` and `YARN_SHORTHAND_EXCLUSIONS`, and explicit-`run` bypass from `research.md` without shell interpretation in `src/instrproof/extract.py`
- [x] T025 [US3] Implement explicit missing-versus-invalid root manifest semantics, safe UTF-8/JSON/schema validation, and lazy cached reads in `src/instrproof/repository.py`
- [x] T026 [US3] Ensure BASE scripts load only for package candidates and HEAD scripts load only for surviving promoted package contracts in `src/instrproof/compare.py`
- [x] T027 [US3] Run the US3 cases in `tests/unit/test_extract.py`, `tests/integration/test_repository.py`, and `tests/integration/test_cli_diff.py` and fix only precision/evidence-error behavior in `src/instrproof/`

**Checkpoint**: Only precise, BASE-grounded root package claims are monitored, and analysis failures cannot appear as ordinary absence.

---

## Phase 6: User Story 4 - Evaluate Mixed Contracts Together (Priority: P4)

**Goal**: Evaluate multiple PathExists and PackageScriptExists contracts in one deterministic diff without changing feature-001 behavior.

**Independent Test**: In one temporary repository, promote multiple path and package contracts, remove selected evidence of both types, and verify one sorted result contains all and only those regressions while the complete original PathExists suite remains green.

### Tests for User Story 4

- [x] T028 [P] [US4] Add failing mixed baseline-count, deduplication, coexistence, and deterministic type/source/target ordering tests in `tests/unit/test_compare.py`
- [x] T029 [P] [US4] Add failing CLI compatibility tests for mixed rows, multiple package contracts, common diagnostic fields on both types, unchanged PathExists regression decisions, summary grammar, clean output, and exit statuses in `tests/integration/test_cli_diff.py`
- [x] T030 [P] [US4] Extend the 100-document/1,000-candidate performance fixture with a deterministic mixture of path and package candidates in `tests/integration/test_performance.py`

### Implementation for User Story 4

- [x] T031 [US4] Finalize shared mixed-contract aggregation, total baseline counting, deduplication, and lexical source/type/target ordering in `src/instrproof/compare.py`
- [x] T032 [US4] Render the shared source/location/type/target/BASE-state/HEAD-state row contract for both types while preserving PathExists analysis, summaries, and exits according to `specs/002-package-script-contracts/contracts/cli.md` in `src/instrproof/cli.py`
- [x] T033 [US4] Run all original and mixed contract tests with `uv run pytest tests/` and correct compatibility issues only in `src/instrproof/`

**Checkpoint**: One diff command deterministically evaluates both contract types, and every feature-001 test still passes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation alignment, and scope control across all stories

- [x] T034 [P] Update user-facing PackageScriptExists examples, exact supported token characters, shorthand exclusions, and diagnostic row format without documenting non-goals as supported in `README.md`
- [x] T035 [P] Review public module docstrings and type annotations for the two-contract terminology in `src/instrproof/models.py`, `src/instrproof/extract.py`, `src/instrproof/compare.py`, and `src/instrproof/repository.py`
- [x] T036 Run every scenario and focused command from `specs/002-package-script-contracts/quickstart.md` and reconcile any documentation mismatch in `specs/002-package-script-contracts/quickstart.md`
- [x] T037 Run `uv run pytest`, confirm the combined 100-document/1,000-candidate case remains below five seconds, and record no unresolved failures in `tests/integration/test_performance.py`
- [x] T038 Inspect `git diff --check`, `git diff`, and `git status --short`; remove no user changes and confirm modifications are limited to feature-002 artifacts, `README.md`, `src/instrproof/`, and `tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and establishes the green feature-001 baseline.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories because both contract types need the generalized identity model.
- **User Story 1 (Phase 3)**: Depends on Foundational and delivers the MVP end to end.
- **User Story 2 (Phase 4)**: Depends on the US1 package contract flow so it can refine identity and survival behavior.
- **User Story 3 (Phase 5)**: Depends on US1 extraction and manifest access; it can run in parallel with US2 after US1 if separate contributors coordinate changes to `extract.py` and integration tests.
- **User Story 4 (Phase 6)**: Depends on US1–US3 because it validates and finalizes combined behavior and compatibility.
- **Polish (Phase 7)**: Depends on all selected stories.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 (MVP) -> US2 ----\
                                \-> US3 -----+-> US4 -> Polish
```

### Within Each User Story

- Add the listed tests first and confirm they fail for the intended missing behavior.
- Complete model/extraction/repository work before comparison orchestration that consumes it.
- Complete comparison behavior before CLI output assertions.
- Run the story-focused tests at its checkpoint before proceeding.

### Parallel Opportunities

- In US1, extraction tests (T007) and repository tests (T008) can be authored in parallel before comparison/CLI tests.
- After US1, US2 and US3 can proceed concurrently when ownership of shared files is coordinated; their `[P]` test tasks touch different files within each story.
- In US4, comparison (T028), CLI (T029), and performance (T030) tests can be authored in parallel.
- Final documentation (T034) and module review (T035) can proceed in parallel.

---

## Parallel Example: User Story 1

```text
Task T007: Add supported-form extraction tests in tests/unit/test_extract.py
Task T008: Add root package manifest evidence tests in tests/integration/test_repository.py
```

## Parallel Example: User Story 2

```text
Task T016: Add identity and survival unit tests in tests/unit/test_compare.py
Task T017: Add coordinated-change CLI tests in tests/integration/test_cli_diff.py
```

## Parallel Example: User Story 3

```text
Task T021: Add ambiguous-command extraction tests in tests/unit/test_extract.py
Task T022: Add manifest failure and root-only tests in tests/integration/test_repository.py
```

## Parallel Example: User Story 4

```text
Task T028: Add mixed comparison tests in tests/unit/test_compare.py
Task T029: Add mixed CLI compatibility tests in tests/integration/test_cli_diff.py
Task T030: Extend the performance fixture in tests/integration/test_performance.py
```

---

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational phases.
2. Complete User Story 1 through T015.
3. Stop and validate the independent exists→exists, exists→removed, and exists→renamed scenarios.
4. The result is a demonstrable PackageScriptExists MVP using the existing diff command.

### Incremental Delivery

1. **US1**: Detect unchanged package claims whose root scripts disappear.
2. **US2**: Make intentional instruction edits and syntax/location-only changes behave correctly.
3. **US3**: Enforce precision, root-only grounding, lazy reads, and explicit evidence errors.
4. **US4**: Prove mixed-contract compatibility, deterministic aggregation, and performance.
5. **Polish**: Align documentation and run complete repository validation.

### Scope Controls

- Do not add runtime dependencies or new CLI commands.
- Do not create a package-script-specific pipeline, registry, or orchestration module.
- Do not inspect nested/workspace manifests or infer replacement scripts.
- Do not interpret shell semantics or script command bodies.
- Do not change PathExists extraction, evidence, identity, survival, or regression decisions; apply only the required shared diagnostic-row additions.

## Notes

- `[P]` tasks are safe parallel opportunities only when their listed prerequisite phase is complete.
- Story labels provide traceability to the four prioritized stories in `spec.md`.
- Exact behavior and output are defined in `specs/002-package-script-contracts/contracts/cli.md`.
- Commit after each task or coherent task group, and preserve unrelated worktree changes.

---

## Phase 8: Convergence

- [x] T039 Exclude `Regression` source-location and evidence-state diagnostic metadata from equality and hashing, and add model regression coverage in `src/instrproof/models.py` and `tests/unit/test_models.py` per plan: Diagnostic evidence / T018 (partial)
