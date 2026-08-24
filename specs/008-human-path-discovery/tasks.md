# Tasks: Harden Path and Instruction Discovery

**Input**: Design documents from `/specs/008-human-path-discovery/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Required by the specification and constitution. For each behavior slice, add the named tests first, run them to confirm the intended failure, then implement production changes.

**Organization**: Tasks are grouped by user story so accepted root-file protection, rejection precision, revision-specific discovery, and compatibility can each be validated at a checkpoint.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file and has no dependency on an incomplete task.
- **[Story]**: Maps the task to a user story in [spec.md](spec.md).
- Every task names the exact file or validation path it changes or inspects.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the locked development environment and a clean behavioral baseline before test-first changes.

- [x] T001 Synchronize the locked development environment with `uv sync --locked --dev` using `pyproject.toml` and `uv.lock`
- [x] T002 Run the pre-change suite with `uv run pytest` and record any existing failures before editing `src/instrproof/` or `tests/`
- [x] T003 Verify the active feature pointer targets `specs/008-human-path-discovery` in `.specify/feature.json` and review the compatibility constraints in `specs/008-human-path-discovery/contracts/cli.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prepare shared real-Git fixture support needed by root-file and revision-specific comparison tests without adding production abstractions.

**⚠️ CRITICAL**: Complete this phase before the user-story integration tests.

- [x] T004 Reuse existing temporary-repository fixtures and extend `tests/conftest.py` only where required to write raw config bytes, commit BASE state, and preserve working-tree changes
- [x] T005 Reuse existing CLI capture patterns and add a local helper only if repeated status/stdout/stderr setup requires it in `tests/integration/test_cli_diff.py`

**Checkpoint**: Test infrastructure can express distinct BASE/HEAD files and configurations without checkout mutation.

---

## Phase 3: User Story 1 - Protect Referenced Root Files (Priority: P1) 🎯 MVP

**Goal**: Promote supported inline root filenames only with exact case-sensitive BASE evidence and report deletion regressions through the existing `PathExists` contract.

**Independent Test**: Commit `README.md` and an inline claim, delete only the file, and verify exactly one `PathExists(README.md)` regression; verify `Makefile`, extension-bearing examples, missing BASE evidence, case mismatch, and coordinated target update outcomes.

### Tests for User Story 1

> Write and run these tests first; confirm the new accepted cases fail before implementation.

- [x] T006 [P] [US1] Add predicate and extraction unit cases for `README.md`, `Cargo.toml`, `package.json`, `pyproject.toml`, `.pre-commit-config.yaml`, and all seven exact extensionless names in `tests/unit/test_extract.py`
- [x] T007 [P] [US1] Add promotion tests proving exact BASE evidence, missing BASE evidence, and case mismatch behavior for root targets in `tests/unit/test_compare.py`
- [x] T008 [US1] Add real-Git normal-mode integration cases for root-file deletion yielding exactly one regression and coordinated root-claim update yielding none in `tests/integration/test_cli_diff.py`
- [x] T009 [P] [US1] Add CI-mode root-file regression assertions for exact target, count, formatting, and status 1 in `tests/integration/test_cli_ci.py`

### Implementation for User Story 1

- [x] T010 [US1] Add the immutable extensionless filename allowlist and independently unit-testable ASCII-letter final-extension predicate in `src/instrproof/extract.py`
- [x] T011 [US1] Route inline candidates through the existing nested matcher or new root classifier, then through unchanged `_resolve` and `RepoPath` normalization in `src/instrproof/extract.py`
- [x] T012 [US1] Run `uv run pytest tests/unit/test_extract.py tests/unit/test_compare.py tests/integration/test_cli_diff.py tests/integration/test_cli_ci.py` and confirm the User Story 1 cases pass without changing `src/instrproof/models.py` or `src/instrproof/cli.py`

**Checkpoint**: Supported root-level inline files are independently protected by existing contracts and exact BASE evidence.

---

## Phase 4: User Story 2 - Reject Ambiguous Inline Text (Priority: P1)

**Goal**: Preserve high precision by rejecting unsupported single tokens and prohibited syntax even when similarly named repository entries exist.

**Independent Test**: Extract from instructions containing arbitrary words, directories, versions, numeric pseudo-extensions, URLs, fragments, queries, globs, placeholders, shell expressions, whitespace, absolute paths, backslashes, NUL, and fenced code; verify zero root claims while nested paths and Markdown links remain unchanged.

### Tests for User Story 2

> Add rejection tests before tightening the classifier and confirm any newly exposed false positives fail.

- [x] T013 [US2] Add parametrized predicate/extraction rejection coverage for `pytest`, `src`, `main`, `build`, `README`, `v1.0`, `python3.12`, URLs, fragments, queries, globs, placeholders, shell expressions, whitespace, absolute paths, backslashes, and NUL in `tests/unit/test_extract.py`
- [x] T014 [US2] Add regression cases proving fenced code stays masked and existing nested inline paths and source-relative Markdown links are unchanged in `tests/unit/test_extract.py`
- [x] T015 [P] [US2] Add an evidence-boundary test proving existing repository entries cannot promote lexically unsupported root tokens in `tests/unit/test_compare.py`

### Implementation for User Story 2

- [x] T016 [US2] Complete prohibited-form guards and numeric-pseudo-extension rejection in the pure root filename predicate without filesystem access in `src/instrproof/extract.py`
- [x] T017 [US2] Run `uv run pytest tests/unit/test_extract.py tests/unit/test_compare.py` and verify every defined ambiguous form is rejected while User Story 1 accepted forms still pass

**Checkpoint**: The expanded extractor retains the required precision boundary independently of repository contents.

---

## Phase 5: User Story 3 - Preserve Baseline Discovery Rules (Priority: P1)

**Goal**: Load discovery configuration from each repository state and carry surviving BASE-discovered sources into comparison so HEAD rule removal cannot hide stale claims.

**Independent Test**: Commit BASE config selecting `docs/ai-rules.md`, remove the HEAD rule while retaining its unchanged claim, delete its evidence, and verify a regression; then verify repaired claim, deleted source, HEAD-only rule, and BASE-only config behaviors.

### Tests for User Story 3

> Add repository and comparison tests first; confirm current HEAD-config reuse and source omission produce failures.

- [x] T018 [US3] Add BASE-config tests for absent, valid, malformed UTF-8, malformed JSON, invalid schema/rules, exact BASE-versus-HEAD values, and no working-tree mutation in `tests/integration/test_repository.py`
- [x] T019 [US3] Add HEAD-config tests for independent valid/malformed values and attributable `HEAD instrproof.json` errors in `tests/integration/test_repository.py`
- [x] T020 [P] [US3] Expand repository-orchestration stubs for independent BASE/HEAD config calls and add an explicit call-count assertion proving overlapping normal and carried paths load each physical HEAD source once in `tests/unit/test_compare.py`
- [x] T021 [US3] Add real-Git comparisons for unchanged rule/stale evidence, removed rule/stale claim, removed rule/repaired claim, removed source, HEAD-only rule, and BASE config deleted in HEAD in `tests/integration/test_cli_diff.py`

### Implementation for User Story 3

- [x] T022 [US3] Refactor strict config decoding/validation into one raw-bytes plus state-label parser and preserve schema/rule diagnostics in `src/instrproof/repository.py`
- [x] T023 [US3] Implement working-tree HEAD configuration loading and exact resolved-tree BASE configuration existence/read operations with default-on-absence behavior in `src/instrproof/repository.py`
- [x] T024 [US3] Add a narrow working-tree source loader that accepts normalized retained `RepoPath` values, skips deleted/non-files, applies normal UTF-8/readability errors, and returns deterministic unique sources in `src/instrproof/repository.py`
- [x] T025 [US3] Reorder `compare_repository` to resolve BASE, load/discover/promote with BASE config, load normal HEAD with HEAD config, union surviving BASE paths, extract once, and call unchanged `compare_contracts` in `src/instrproof/compare.py`
- [x] T026 [US3] Keep `analyze_current_repository` on HEAD configuration and normal current discovery only, updating repository method calls without historical union behavior in `src/instrproof/compare.py`
- [x] T027 [US3] Run `uv run pytest tests/integration/test_repository.py tests/unit/test_compare.py tests/integration/test_cli_diff.py` and verify all User Story 3 lifecycle and error cases pass

**Checkpoint**: BASE configuration owns baseline discovery, HEAD owns normal current discovery, and removed rules cannot hide surviving stale claims.

---

## Phase 6: User Story 4 - Retain Compatible and Deterministic Analysis (Priority: P2)

**Goal**: Preserve default discovery, deduplication, current-only commands, exact CLI presentation/statuses, deterministic ordering, and existing public workflows.

**Independent Test**: Run default/overlap/malformed/current-only/output fixtures repeatedly and verify byte-for-byte compatible results, one read per source, stable ordering, statuses 0/1/2, and unchanged demo/release workflows.

### Tests for User Story 4

- [x] T028 [P] [US4] Add overlapping default/custom/carry-forward source deduplication and read-once assertions in `tests/integration/test_repository.py`
- [x] T029 [US4] Add unchanged root/nested `AGENTS.md` and `CLAUDE.md`, tracked modification, and non-ignored untracked discovery assertions in `tests/integration/test_repository.py`
- [x] T030 [P] [US4] Add exact normal and CI output/status assertions for success, root regression, BASE config error, and HEAD config error in `tests/integration/test_cli_diff.py` and `tests/integration/test_cli_ci.py`
- [x] T031 [P] [US4] Add `check` and `explain` compatibility cases proving only current HEAD rules select sources in `tests/integration/test_cli_inspection.py`
- [x] T032 [US4] Extend the existing 100-document/1,000-candidate performance fixture to cover deterministic comparison without duplicate source analysis in `tests/integration/test_performance.py`

### Implementation and Documentation for User Story 4

- [x] T033 [US4] Preserve lexical sorting and normalized `RepoPath` deduplication across normal and carried HEAD sources without changing representative selection in `src/instrproof/repository.py` and `src/instrproof/compare.py`
- [x] T034 [US4] Document supported extension-bearing root files, exact extensionless allowlist, BASE evidence, revision-owned configs, rule-removal carry-forward, and HEAD-only non-retroactivity in `README.md`
- [x] T035 [US4] Run exact compatibility suites with `uv run pytest tests/integration/test_cli_diff.py tests/integration/test_cli_ci.py tests/integration/test_cli_inspection.py tests/integration/test_performance.py`

**Checkpoint**: Existing commands and workflows retain compatible deterministic behavior with the two correctness gaps closed.

---

## Phase 7: Polish & Cross-Cutting Validation

**Purpose**: Validate the complete implementation against all feature and release criteria.

- [x] T036 Review production changes for scope and invariants against `specs/008-human-path-discovery/spec.md`, confirming no edits are needed in `src/instrproof/models.py`, `src/instrproof/cli.py`, packaging, demo, release scripts, or workflows
- [x] T037 Execute all three copy-and-run scenarios and verify their expected statuses/output using `specs/008-human-path-discovery/quickstart.md`
- [x] T038 Run `uv run pytest` three times and compare results to detect ordering, cache, or state-leak regressions across `tests/`
- [x] T039 Run the unchanged public demonstration with `./scripts/run-demo.sh` and verify no demo-created changes remain
- [x] T040 Run the unchanged release workflow with `./scripts/validate-release.sh` and require successful completion
- [x] T041 Verify `.github/workflows/ci.yml` retains executable test-matrix entries for Python 3.12, 3.13, and 3.14 without modifying the workflow
- [x] T042 Inspect `git diff --check`, `git diff`, and `git status --short`; verify changes are limited to feature artifacts, `src/instrproof/extract.py`, `src/instrproof/repository.py`, `src/instrproof/compare.py`, focused tests, and `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on Setup and blocks real-Git story integration work.
- **US1 (Phase 3)**: Depends on Foundational; delivers the accepted root-file MVP.
- **US2 (Phase 4)**: Depends on US1's classifier seam, then independently proves precision rejection.
- **US3 (Phase 5)**: Depends on Foundational but not on US1/US2 production behavior; it can proceed in parallel after Phase 2.
- **US4 (Phase 6)**: Depends on US1–US3 because it verifies their integrated compatibility and determinism.
- **Polish (Phase 7)**: Depends on all selected stories.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 -> US2 --+
                    \-> US3 --------+-> US4 -> Polish
```

### Within Each User Story

- Write the listed tests first and run them to demonstrate failure.
- Implement only the smallest production change needed for those tests.
- Run the story checkpoint before proceeding.
- Do not change `compare_contracts`, contract identity, CLI dispatch/presentation, generated files, dependencies, demo scripts, or release scripts.

### Parallel Opportunities

- T006 and T007 can run in parallel; T009 can run alongside unit-test work after shared test setup.
- T015 can run in parallel with the sequential T013–T014 extraction-test work.
- T020 can run in parallel with the sequential T018–T019 repository-test work.
- After Foundation, US3 can proceed in parallel with the sequential US1 → US2 extraction stream.
- T028 and T029 are sequential in `tests/integration/test_repository.py`; T030 and T031 can run in parallel with that stream because they touch CLI integration files.
- T036 is completion-gated scope review and is not a parallel implementation task.

---

## Parallel Execution Examples

### User Story 1

```text
Task T006: Add accepted root filename extraction tests in tests/unit/test_extract.py
Task T007: Add BASE promotion/evidence tests in tests/unit/test_compare.py
Task T009: Add CI root regression contract tests in tests/integration/test_cli_ci.py
```

### User Story 2

```text
Task T015: Prove unsupported tokens cannot be promoted in tests/unit/test_compare.py
```

### User Story 3

```text
Task T020: Update orchestration stubs in tests/unit/test_compare.py
```

### User Story 4

```text
Task T028: Add source deduplication/read-once coverage in tests/integration/test_repository.py
Task T030: Add exact diff/CI output contracts in tests/integration/test_cli_diff.py and tests/integration/test_cli_ci.py
Task T031: Add current-only check/explain coverage in tests/integration/test_cli_inspection.py
```

---

## Implementation Strategy

### MVP First

1. Complete Setup and Foundation.
2. Complete US1 tests and root filename implementation.
3. Stop and validate the US1 checkpoint: supported root files promote only with BASE evidence and deletion produces exactly one regression.

### Incremental Delivery

1. **US1**: Add supported root-file protection.
2. **US2**: Lock down ambiguity rejection and preserve nested/link behavior.
3. **US3**: Make configuration revision-specific and retain surviving BASE sources.
4. **US4**: Prove public compatibility, deterministic deduplication, documentation, and performance.
5. **Polish**: Run repeated suite, demo, release validation, and scope inspection.

### Parallel Team Strategy

After Foundation, one stream can implement US1 then US2 in `extract.py` while another implements US3 in `repository.py`/`compare.py`. Merge both before US4 compatibility work because US4 verifies their combined CLI behavior.

## Notes

- `[P]` means different-file work with no dependency on an incomplete task; tasks sharing a file should be serialized or carefully coordinated.
- Story labels provide traceability to [spec.md](spec.md).
- Every production change has preceding focused regression tests.
- Keep existing user changes and unrelated worktree content intact.
- Required validation failures block completion and must be reported rather than waived.

## Phase 8: Convergence

- [x] T043 Add direct BASE-snapshot schema rejection coverage for non-object roots, unsupported keys, non-array `instructions`, and non-string entries with attributable BASE diagnostics in `tests/integration/test_repository.py` per FR-029 and T018 (partial)
- [x] T044 Add a real-Git comparison where HEAD deletes only `instrproof.json` while the BASE-selected custom source and stale claim survive and their evidence is removed in `tests/integration/test_cli_diff.py` per US3/AC5, FR-029, and T021 (partial)
- [x] T045 Add explicit repository assertions that HEAD discovery reads tracked instruction modifications and includes non-ignored untracked instruction sources in `tests/integration/test_repository.py` per FR-025 and T029 (partial)
