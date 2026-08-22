# Tasks: Discover Instruction Documents

**Input**: Design documents from `/specs/003-discover-instructions/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Automated tests are required by the specification and constitution. Within each story, write the listed tests first and confirm they fail for the missing behavior before implementation.

**Organization**: Tasks are grouped by user story so each discovery increment remains independently testable while reusing the feature-001/002 contract pipeline.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add only the planned discovery module and focused test location to the existing Python package layout.

- [x] T001 Create the instruction-discovery module and unit-test skeletons with module documentation in src/instrproof/discovery.py and tests/unit/test_discovery.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Move instruction-source eligibility out of the domain value before any new discovery source can flow downstream.

**⚠️ CRITICAL**: No user story can accept configured filenames until this validation boundary is corrected.

- [x] T002 Add failing model tests proving InstructionSource accepts any valid discovered RepoPath while RepoPath still rejects invalid paths in tests/unit/test_models.py
- [x] T003 Remove hard-coded AGENTS.md/CLAUDE.md eligibility from InstructionSource without changing claim or contract identity in src/instrproof/models.py

**Checkpoint**: Any valid normalized repository-relative path can represent a source, while discovery remains responsible for admitting it.

---

## Phase 3: User Story 1 - Discover Repository Instruction Documents (Priority: P1) 🎯 MVP

**Goal**: Discover root and nested `AGENTS.md` and `CLAUDE.md` deterministically in BASE and HEAD and pass their complete paths into existing extraction.

**Independent Test**: Build a repository containing all four default source categories with BASE-valid claims, then verify each source is independently analyzed with no configuration file.

### Tests for User Story 1

- [x] T004 [P] [US1] Add failing unit tests for root/nested default-name selection, lexical ordering, and normalized-path deduplication in tests/unit/test_discovery.py
- [x] T005 [P] [US1] Add failing repository tests for independently enumerating and loading root/nested AGENTS.md and CLAUDE.md from BASE and HEAD in tests/integration/test_repository.py
- [x] T006 [P] [US1] Add failing end-to-end tests proving default nested sources produce existing contract analysis and complete source-path diagnostics in tests/integration/test_cli_diff.py

### Implementation for User Story 1

- [x] T007 [US1] Implement pure default instruction-path selection returning a sorted unique tuple of RepoPath values in src/instrproof/discovery.py
- [x] T008 [US1] Delegate BASE and HEAD instruction filtering to the discovery component while retaining one path enumeration and existing UTF-8 errors in src/instrproof/repository.py

**Checkpoint**: Root and nested default sources work without configuration, and the existing diff command analyzes each complete source path.

---

## Phase 4: User Story 2 - Add Repository-Specific Instruction Sources (Priority: P2)

**Goal**: Accept strict repository-root `instrproof.json` rules for exact files and deterministic recursive globs, with overlaps analyzed once and configuration failures reported explicitly.

**Independent Test**: Configure one exact Markdown file and one glob matching multiple files, overlap a default source through repeated rules, and verify all matched physical files are analyzed once; separately verify zero matches succeed and malformed configurations return analysis errors.

### Tests for User Story 2

- [x] T009 [P] [US2] Add failing unit tests for exact rules, POSIX segment globs, zero-segment/deep `**`, case sensitivity, normalization, overlap deduplication, zero matches, duplicates, and invalid patterns in tests/unit/test_discovery.py
- [x] T010 [P] [US2] Add failing repository tests for absent/valid `instrproof.json`, exact/glob loading, and unreadable or invalid UTF-8/JSON/schema/path configuration errors in tests/integration/test_repository.py
- [x] T011 [P] [US2] Add failing CLI tests for configured PathExists/PackageScriptExists sources, overlapping-rule deduplication, zero-match success, and configuration-error exit status 2 in tests/integration/test_cli_diff.py

### Implementation for User Story 2

- [x] T012 [US2] Implement immutable discovery configuration, strict rule validation/normalization, exact matching, segment-aware glob matching, and union deduplication in src/instrproof/discovery.py
- [x] T013 [US2] Implement optional working-tree instrproof.json loading and explicit RepositoryError mapping, then apply configured selection to both source loaders in src/instrproof/repository.py
- [x] T014 [US2] Load discovery configuration once per invocation and pass the identical rule set to independently discovered BASE and HEAD sources in src/instrproof/compare.py

**Checkpoint**: Repository-specific files and globs participate through the existing pipeline, every normalized source is analyzed once, and invalid configuration cannot become a false pass.

---

## Phase 5: User Story 3 - Resolve Claims from Their Correct Context (Priority: P3)

**Goal**: Prove nested and configured sources retain full path context so Markdown links remain source-relative while inline paths remain repository-root-relative.

**Independent Test**: Analyze `packages/auth/AGENTS.md` containing `[architecture](docs/architecture.md)` and `` `docs/root-policy.md` ``, then verify targets normalize respectively to `packages/auth/docs/architecture.md` and `docs/root-policy.md`.

### Tests for User Story 3

- [x] T015 [P] [US3] Add extraction regression tests using nested default and custom InstructionSource paths for Markdown-relative and root-relative inline claims in tests/unit/test_extract.py
- [x] T016 [P] [US3] Add end-to-end regressions for nested Markdown-link and inline-path resolution through discovered sources in tests/integration/test_cli_diff.py

### Implementation for User Story 3

- [x] T017 [US3] Preserve complete discovered RepoPath values through source loading and correct only test-exposed resolution regressions without changing established extraction semantics in src/instrproof/repository.py and src/instrproof/extract.py

**Checkpoint**: Nested discovery changes source participation only; both feature-001 resolution forms retain their established bases.

---

## Phase 6: User Story 4 - Preserve State-Aware Regression Semantics (Priority: P4)

**Goal**: Verify independently discovered BASE and HEAD source sets naturally preserve existing claim-survival behavior for retained, removed, updated, and new documents.

**Independent Test**: Compare cases with a retained claim and missing evidence, a deleted source, an updated claim, and a HEAD-only source under one rule set, then verify only the retained identical claim regresses.

### Tests for User Story 4

- [x] T018 [P] [US4] Add repository tests proving the same resolved rules select different BASE/HEAD source sets when files are deleted or newly created in tests/integration/test_repository.py
- [x] T019 [P] [US4] Add CLI regressions for deleted documents, removed/updated claims, HEAD-only documents, surviving claims, and identical targets from distinct sources in tests/integration/test_cli_diff.py

### Implementation for User Story 4

- [x] T020 [US4] Verify comparison orchestration uses existing promotion and claim-survival logic without file-lifecycle branches, correcting only source-discovery wiring defects in src/instrproof/compare.py

**Checkpoint**: BASE and HEAD discover independently, and source-set changes need no regression-engine special cases.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Document the public configuration, validate required scale, and run all compatibility gates.

- [x] T021 [P] Document default recursive discovery, instrproof.json schema/globs, deduplication, path resolution, and explicit errors in README.md
- [x] T022 [P] Extend the 100-source/1,000-candidate timing scenario to exercise expanded discovery within five seconds in tests/integration/test_performance.py
- [x] T023 Run all quickstart and project checks, inspect git diff/status for scope, and record any required artifact corrections in specs/003-discover-instructions/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on T001 and blocks every story.
- **User Story 1 (Phase 3)**: Depends on Foundational; establishes default discovery and repository integration.
- **User Story 2 (Phase 4)**: Depends on User Story 1's selector/repository seam; adds configuration without changing downstream analysis.
- **User Story 3 (Phase 5)**: Depends on User Story 1; configured-source variants additionally depend on User Story 2.
- **User Story 4 (Phase 6)**: Depends on User Stories 1 and 2 so the shared rule set and both state loaders exist.
- **Polish (Phase 7)**: Depends on all selected stories.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 (default discovery) -> US2 (configured discovery)
                                  |                    |
                                  +------> US3 <-------+
                                                       |
                                                       +-> US4

US1 + US2 + US3 + US4 -> Polish
```

### Within Each User Story

- Write story tests first and confirm they fail for the absent behavior.
- Implement pure selection/model behavior before repository integration.
- Complete repository integration before CLI end-to-end validation.
- Do not modify extraction or comparison semantics unless a story's regression test exposes a violation of the existing contract.

### Parallel Opportunities

- T004, T005, and T006 can be authored in parallel in separate test files.
- T009, T010, and T011 can be authored in parallel after US1.
- T015 and T016 can be authored in parallel.
- T018 and T019 can be authored in parallel.
- T021 and T022 can proceed in parallel after behavior stabilizes.

---

## Parallel Examples

### User Story 1

```text
Task T004: Default selection tests in tests/unit/test_discovery.py
Task T005: BASE/HEAD source-loading tests in tests/integration/test_repository.py
Task T006: Default nested-source CLI tests in tests/integration/test_cli_diff.py
```

### User Story 2

```text
Task T009: Exact/glob/validation unit tests in tests/unit/test_discovery.py
Task T010: Configuration repository-boundary tests in tests/integration/test_repository.py
Task T011: Configured-source and error CLI tests in tests/integration/test_cli_diff.py
```

### User Story 3

```text
Task T015: Nested resolution extractor tests in tests/unit/test_extract.py
Task T016: Nested resolution end-to-end tests in tests/integration/test_cli_diff.py
```

### User Story 4

```text
Task T018: Independent snapshot discovery tests in tests/integration/test_repository.py
Task T019: Claim-survival CLI tests in tests/integration/test_cli_diff.py
```

---

## Implementation Strategy

### MVP First: User Story 1

1. Complete T001-T003 to establish the discovery boundary.
2. Complete T004-T008 to deliver recursive default `AGENTS.md`/`CLAUDE.md` discovery.
3. Run focused unit, repository, and CLI tests.
4. Stop and validate the default-discovery MVP before adding configuration.

### Incremental Delivery

1. **US1**: Root/nested defaults with full source identity.
2. **US2**: Exact files, globs, deduplication, and explicit configuration errors.
3. **US3**: Nested resolution compatibility proven end to end.
4. **US4**: BASE/HEAD source-set and claim-survival compatibility proven end to end.
5. **Polish**: Public documentation, performance coverage, full feature-001/002 regression suite.

### Scope Discipline

- Reuse current `GitRepository`, extractors, contract types, comparison functions, formatting, and CLI command.
- Add no runtime dependency, indexing, caching, concurrency, agent semantics, precedence, or new command.
- Keep line metadata diagnostic-only and complete repository-relative source paths in identity.

## Notes

- `[P]` means the task touches different files and does not depend on another incomplete task in its phase.
- `[USn]` provides requirement traceability to the matching prioritized user story.
- Every task includes exact repository-relative file paths and is intended to be executable without additional design decisions.
- Commit after each task or cohesive test/implementation pair.
