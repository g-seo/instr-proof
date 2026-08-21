# Tasks: Detect Path Regressions

**Input**: Design documents from `specs/001-detect-path-regressions/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Automated tests are required by the feature specification and project constitution. Story tests are written before their corresponding implementation and verified to fail for the expected missing behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated as an independent increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and has no dependency on another incomplete task in the same phase
- **[Story]**: Maps the task to a user story in spec.md
- Every task names the exact file or files it changes

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the installable Python CLI and its test environment.

- [X] T001 Create the Python 3.12+ uv project metadata, `instrproof` console entry point, pytest development dependency, and pytest configuration in `pyproject.toml`
- [X] T002 Create the package entry files and version metadata in `src/instrproof/__init__.py` and `src/instrproof/__main__.py`

**Checkpoint**: `uv sync --dev` succeeds and `uv run python -c "import instrproof"` imports the package.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Provide stable domain values, repository evidence access, and isolated Git fixtures required by every story.

**⚠️ CRITICAL**: No user-story implementation begins until this phase is complete.

- [X] T003 [P] Write unit tests for RepoPath validation/normalization and identity equality independent of line/prose metadata in `tests/unit/test_models.py`
- [X] T004 Implement frozen RepoPath, InstructionSource, PathClaim, ContractIdentity, PathExistsContract, Regression, and ComparisonResult values in `src/instrproof/models.py`
- [X] T005 [P] Create pytest helpers that initialize, configure, commit, and mutate repositories under `tmp_path` in `tests/conftest.py`
- [X] T006 Write integration tests using the T005 fixtures for repository-root discovery, BASE ref validation, BASE tree listing/content/existence, HEAD instruction listing/content/existence, and Git/read failures in `tests/integration/test_repository.py`
- [X] T007 Implement shell-free Git command execution plus BASE Git-tree and HEAD working-tree evidence access in `src/instrproof/repository.py`
- [X] T008 Run `uv run pytest tests/unit/test_models.py tests/integration/test_repository.py` and resolve foundational failures in `src/instrproof/models.py`, `src/instrproof/repository.py`, and their test files

**Checkpoint**: Domain identities are stable and temporary repositories can be inspected without mutating their Git state.

---

## Phase 3: User Story 1 - Detect Broken Instruction Paths (Priority: P1) 🎯 MVP

**Goal**: Compare BASE with the checked-out HEAD and report an unchanged inline or Markdown path claim whose BASE-valid target disappeared, while passing when the target remains.

**Independent Test**: In a temporary repository, commit an instruction and existing target as BASE, run once with the target present for exit 0, then remove the target while retaining the claim and run for exit 1 with source/type/target output.

### Tests for User Story 1

> Write these tests first and confirm they fail for the missing story behavior.

- [X] T009 [P] [US1] Write extraction tests for root-relative inline code paths and instruction-relative local Markdown links in `tests/unit/test_extract.py`
- [X] T010 [P] [US1] Write promotion/comparison tests for BASE-valid contracts, preserved targets, and missing targets in `tests/unit/test_compare.py`
- [X] T011 [P] [US1] Write CLI integration tests for pass and single/multiple regression output, stable sorting, and exit statuses 0 and 1 in `tests/integration/test_cli_diff.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement supported instruction discovery input handling, inline-code and local-Markdown-link extraction, and required relative resolution in `src/instrproof/extract.py`
- [X] T013 [US1] Implement BASE target validation, PathExists contract promotion, HEAD claim matching, target existence comparison, deduplication, and regression sorting in `src/instrproof/compare.py`
- [X] T014 [US1] Implement `argparse` command parsing, repository orchestration, deterministic presentation, console exit mapping, and module entry delegation in `src/instrproof/cli.py` and `src/instrproof/__main__.py`

**Checkpoint**: User Story 1 passes independently and provides the end-to-end `instrproof diff --base <ref>` MVP.

---

## Phase 4: User Story 2 - Avoid Stale-Claim False Positives (Priority: P2)

**Goal**: Treat changed or removed claims as retired and preserve identity when only prose or line position changes.

**Independent Test**: In temporary BASE/HEAD fixtures, rename a target and update its claim, remove a claim/document, and move an unchanged claim through surrounding prose; verify the first two pass and the third retains the same identity and follows target existence.

### Tests for User Story 2

> Write these tests first and confirm they fail if claim survival relies on lines or prose.

- [X] T015 [P] [US2] Add unit tests for changed/removed claims, duplicate claim collapse, and line/prose-independent identity in `tests/unit/test_compare.py`
- [X] T016 [P] [US2] Add temporary-repository CLI scenarios for updated targets, removed instructions, and moved claims in `tests/integration/test_cli_diff.py`

### Implementation for User Story 2

- [X] T017 [US2] Refine HEAD survival and baseline retirement behavior to use only source/type/normalized-target identity in `src/instrproof/compare.py`

**Checkpoint**: User Stories 1 and 2 both pass, with intentional instruction maintenance producing no old-contract regression.

---

## Phase 5: User Story 3 - Monitor Only Validated Paths (Priority: P3)

**Goal**: Restrict monitoring to high-confidence supported syntax whose normalized target exists in BASE, including correctly resolved nested Markdown links.

**Independent Test**: In a temporary repository containing valid and invalid inline/link forms at root and nested locations, verify only BASE-existing, repository-contained targets become contracts and a removed nested-link target reports its `docs/...` normalized path.

### Tests for User Story 3

> Write these tests first and confirm unsupported or unvalidated candidates expose the missing precision behavior.

- [X] T018 [P] [US3] Add table-driven extraction tests for fenced code, arbitrary prose, path-shape rules, URLs, absolute/fragment-only/query links, fragments, `.`/`..`, backslashes, NUL, drive/UNC forms, and repository escapes in `tests/unit/test_extract.py`
- [X] T019 [P] [US3] Add comparison tests proving nonexistent BASE targets are not promoted and equivalent targets deduplicate in `tests/unit/test_compare.py`
- [X] T020 [P] [US3] Add nested `CLAUDE.md` Markdown-link and nonexistent-BASE-target CLI scenarios in `tests/integration/test_cli_diff.py`

### Implementation for User Story 3

- [X] T021 [US3] Enforce the conservative candidate grammar, fenced-code exclusion, local-link filtering, cross-platform lexical normalization, repository-boundary rejection, and BASE-only promotion rules in `src/instrproof/extract.py` and `src/instrproof/compare.py`

**Checkpoint**: All three stories and all seven required demonstration cases pass independently.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate operational failures, performance, documentation, and the complete delivery without expanding scope.

- [X] T022 [P] Add CLI tests for missing arguments, non-repository execution, invalid BASE refs, unreadable/invalid instruction data, stderr diagnostics, and exit status 2 in `tests/integration/test_cli_diff.py`
- [X] T023 [P] Add the 100-document/1,000-candidate performance acceptance test with a five-second threshold in `tests/integration/test_performance.py`
- [X] T024 [P] Document uv setup, supported instruction/path syntax, BASE-versus-working-tree behavior, examples, output, and exit statuses in `README.md`
- [X] T025 Run `uv run pytest`, execute every scenario in `specs/001-detect-path-regressions/quickstart.md`, inspect `git diff` and `git status`, and record any necessary corrections in the files changed by this feature

**Checkpoint**: Full validation passes, documentation matches the CLI contract, and no unrelated files are included.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2 and delivers the MVP.
- **User Story 2 (Phase 4)**: Depends on the PathExists comparison slice delivered by User Story 1.
- **User Story 3 (Phase 5)**: Depends on User Story 1 extraction/promotion; it can proceed in parallel with User Story 2 after User Story 1 completes because it primarily changes extraction precision while US2 changes survival semantics.
- **Polish (Phase 6)**: Depends on all selected user stories; T022–T024 can run in parallel, then T025 performs final validation.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 (MVP) -> US2
                              \-> US3
US2 + US3 -> Polish
```

### Within Each User Story

- Write and run story tests first; verify they fail for the intended missing behavior.
- Implement extraction/evidence/domain behavior before CLI orchestration that consumes it.
- Run the story's focused tests at its checkpoint.
- Do not begin polish until required story checkpoints pass.

## Parallel Opportunities

- In Foundation, T003 and T005 can be authored in parallel after setup; T006 follows T005, while T004 and T007 then satisfy their respective tests.
- In US1, T009, T010, and T011 can be authored in parallel before T012–T014 proceed in dependency order.
- After US1, US2 and US3 can be developed concurrently, with coordination before final edits to `src/instrproof/compare.py`.
- In US2, T015 and T016 can be authored in parallel.
- In US3, T018, T019, and T020 can be authored in parallel.
- In Polish, T022, T023, and T024 can run in parallel before T025.

## Parallel Example: User Story 1

```text
Task T009: Write extraction tests in tests/unit/test_extract.py
Task T010: Write promotion/comparison tests in tests/unit/test_compare.py
Task T011: Write CLI integration tests in tests/integration/test_cli_diff.py
```

## Parallel Example: User Story 2

```text
Task T015: Add identity/survival unit tests in tests/unit/test_compare.py
Task T016: Add instruction-maintenance CLI scenarios in tests/integration/test_cli_diff.py
```

## Parallel Example: User Story 3

```text
Task T018: Add precision-boundary extraction tests in tests/unit/test_extract.py
Task T019: Add BASE-promotion tests in tests/unit/test_compare.py
Task T020: Add nested-link CLI scenarios in tests/integration/test_cli_diff.py
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundation.
2. Complete User Story 1 through T014.
3. Run the US1 unit and integration tests independently.
4. Demonstrate exit 0 for an intact target and exit 1 with deterministic regression details for a removed target.
5. Stop here if only the minimum useful capability is needed.

### Incremental Delivery

1. **US1**: Detect unchanged claims with disappeared targets.
2. **US2**: Eliminate false positives when instructions change or disappear and prove stable identity.
3. **US3**: Enforce precision and BASE-validation boundaries, including nested Markdown resolution.
4. **Polish**: Prove error behavior, performance, documentation, and full-suite consistency.

## Notes

- `[P]` means the task edits a different file or can be safely authored without an incomplete same-phase dependency.
- Story labels provide traceability to `spec.md`; setup, foundation, and polish tasks intentionally have no story label.
- Git subprocesses must use argument arrays and must not use a shell.
- Tests must use pytest temporary repositories and must not mutate the InstrProof repository.
- Do not add PackageScriptExists, `check`, `explain`, rename hints, semantic analysis, LLM behavior, or a contract plugin framework.

---

## Phase 7: Convergence

- [X] T026 Make BASE target evidence distinguish an absent path from Git/object inspection failures and add exit-status-2 regression coverage in `src/instrproof/repository.py`, `tests/integration/test_repository.py`, and `tests/integration/test_cli_diff.py` per FR-021 and Constitution IV (partial)
- [X] T027 Exclude unterminated fenced blocks and valid fenced blocks with longer closing delimiters from claim extraction, with precision regression tests in `src/instrproof/extract.py` and `tests/unit/test_extract.py` per FR-011 and plan decision 5 (partial)
- [X] T028 Resolve both commit and tree BASE refs as immutable inspectable snapshots and add repository/CLI coverage in `src/instrproof/repository.py`, `tests/integration/test_repository.py`, and `tests/integration/test_cli_diff.py` per plan decision 2 and `contracts/cli.md` (partial)
- [X] T029 Add temporary-repository integration tests for file-to-directory and directory-to-file replacement at the same normalized target plus a supported instruction document present only in HEAD in `tests/integration/test_cli_diff.py` per spec Edge Cases and Constitution II (missing)
