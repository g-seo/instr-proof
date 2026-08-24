# Tasks: Require Baseline Contracts

**Input**: Design documents from `/specs/009-require-contracts/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: Required by the specification and constitution. Add the named exact-output tests first, run them to demonstrate the missing behavior, and then make the smallest production change.

**Organization**: Tasks are grouped by user story so strict empty-coverage failure, compatibility, error precedence, and safe CI adoption can each be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file and has no dependency on an incomplete task.
- **[Story]**: Maps the task to a user story in [spec.md](spec.md).
- Every task names the exact file or validation path it changes or inspects.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the locked environment, clean baseline, and active feature context before test-first changes.

- [x] T001 Synchronize the locked development environment with `uv sync --locked --dev` using `pyproject.toml` and `uv.lock`
- [x] T002 Run the pre-change suite with `uv run pytest` and record any existing failures before editing `src/instrproof/`, `tests/`, `scripts/`, or `README.md`
- [x] T003 Verify `.specify/feature.json` targets `specs/009-require-contracts` and review the exact interface contract in `specs/009-require-contracts/contracts/cli.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm existing test and architecture seams can express the feature without adding shared infrastructure or modifying analysis.

**⚠️ CRITICAL**: Complete this phase before user-story test changes.

- [x] T004 Confirm existing `git_repo` and `committed_repo` fixtures in `tests/conftest.py` cover empty, nonempty, duplicate, malformed-config, and working-tree comparison scenarios; extend only if a required state cannot be expressed
- [x] T005 Confirm `main()` has one post-`compare_repository()` result boundary and record the no-change constraint for `src/instrproof/compare.py` and `src/instrproof/models.py` against `specs/009-require-contracts/data-model.md`

**Checkpoint**: Existing fixtures and the completed-result boundary support all stories without a new production layer or model.

---

## Phase 3: User Story 1 - Reject Empty Baseline Coverage (Priority: P1) 🎯 MVP

**Goal**: Let diff users opt into an exact status-2 failure when successful analysis produces zero baseline contracts, in both normal and CI-formatted modes.

**Independent Test**: Run completed zero-contract normal and CI diffs with the option and verify status 2, empty stdout, exact mode-specific stderr, and absence of PASS/count/partial output.

### Tests for User Story 1

> Write and run these tests first; confirm strict zero-contract cases fail before implementation.

- [x] T006 [US1] Add a normal-mode zero-contract test with `--require-contracts` asserting status 2, empty stdout, and the exact lowercase stderr diagnostic in `tests/integration/test_cli_diff.py`
- [x] T007 [P] [US1] Add a CI-mode zero-contract test with `--ci --require-contracts` asserting status 2, empty stdout, and the exact `InstrProof ✗` analysis error in `tests/integration/test_cli_ci.py`
- [x] T008 [US1] Add strict diff argument-order cases covering `--require-contracts` before and after existing diff options in `tests/integration/test_cli_diff.py`

### Implementation for User Story 1

- [x] T009 [US1] Add the disabled-by-default `--require-contracts` boolean option only to the diff subparser in `src/instrproof/cli.py`
- [x] T010 [US1] Evaluate `args.require_contracts` against `result.baseline_contract_count` immediately after successful comparison and emit the exact normal or CI stderr error before result formatting in `src/instrproof/cli.py`
- [x] T011 [US1] Run `uv run pytest tests/integration/test_cli_diff.py tests/integration/test_cli_ci.py` and confirm all User Story 1 exact stream/status assertions pass

**Checkpoint**: Strict completed zero-baseline comparisons fail clearly and never print partial success output.

---

## Phase 4: User Story 2 - Preserve Optional and Nonempty Results (Priority: P1)

**Goal**: Preserve default zero-contract success and every existing positive-count PASS/regression decision, count, format, and ordering when the option is enabled.

**Independent Test**: Exercise zero contracts without the option and one, multiple, duplicate-to-one, passing, and regressing contracts with the option; compare exact outputs/statuses and repeat deterministic fixtures three times.

### Tests for User Story 2

> Add compatibility tests before any refinement and require byte-for-byte existing output on unaffected paths.

- [x] T012 [US2] Strengthen normal-mode zero-contract coverage without the option to assert exact status 0, stdout, and empty stderr in `tests/integration/test_cli_diff.py`
- [x] T013 [P] [US2] Strengthen CI zero-contract coverage without the option to assert exact status 0, existing four-line stdout, and empty stderr in `tests/integration/test_cli_ci.py`
- [x] T014 [US2] Add strict normal-mode one-contract PASS and one-regression cases asserting output and statuses are identical to invocations without the option in `tests/integration/test_cli_diff.py`
- [x] T015 [P] [US2] Add strict CI one-contract PASS and one-regression cases asserting output and statuses are identical to invocations without the option in `tests/integration/test_cli_ci.py`
- [x] T016 [US2] Add duplicate-claim coverage proving two occurrences promoted to one identity satisfy strict mode using the authoritative count in `tests/integration/test_cli_diff.py`
- [x] T017 [P] [US2] Add a multiple-contract CI fixture with the option, assert the existing exact deduplicated count and ordering, and repeat it three times in `tests/integration/test_cli_ci.py`
- [x] T018 [US2] Add a monkeypatched strict invocation asserting `compare_repository()` is called exactly once and its `ComparisonResult` is not reconstructed in `tests/integration/test_cli_diff.py`

### Implementation for User Story 2

- [x] T019 [US2] Review and, only if compatibility tests require it, narrow the post-analysis branch in `src/instrproof/cli.py` so every positive baseline count falls through unchanged to existing formatters and regression status logic
- [x] T020 [US2] Run `uv run pytest tests/integration/test_cli_diff.py tests/integration/test_cli_ci.py` and verify default, positive-count, duplicate, regression, repeatability, and single-comparison cases pass

**Checkpoint**: The option changes only completed zero-baseline results; all default and nonempty comparison behavior is unchanged.

---

## Phase 5: User Story 3 - Retain Analysis Error Precedence (Priority: P1)

**Goal**: Preserve existing attributable or sanitized status-2 diagnostics whenever analysis fails before a complete comparison exists.

**Independent Test**: Enable the option for unavailable BASE, malformed BASE config, malformed HEAD config, unreadable instruction source, malformed required repository data, and unexpected CI failure; verify each old exact diagnostic wins and zero-contract text is absent.

### Tests for User Story 3

> Extend existing failure fixtures with the option before changing any CLI error path.

- [x] T021 [US3] Add strict normal-mode unavailable-BASE and malformed-BASE-config cases asserting existing exact status-2 stderr, empty stdout, and no zero-contract text in `tests/integration/test_cli_diff.py`
- [x] T022 [US3] Add separate strict normal-mode malformed-HEAD-config, unreadable-instruction-source, and malformed-required-repository-data cases asserting each existing exact status-2 diagnostic, empty stdout, and no zero-contract text in `tests/integration/test_cli_diff.py`
- [x] T023 [P] [US3] Add strict CI unavailable-BASE and repository/configuration failure cases asserting existing sanitized exact output and no zero-contract text in `tests/integration/test_cli_ci.py`
- [x] T024 [US3] Add a strict unexpected CI exception case asserting the existing `internal analysis failure.` message, status 2, empty stdout, and no zero-contract text in `tests/integration/test_cli_ci.py`

### Implementation for User Story 3

- [x] T025 [US3] Keep all existing exception handlers ahead of the contract requirement and adjust only misplaced policy logic, if exposed by tests, in `src/instrproof/cli.py`
- [x] T026 [US3] Run `uv run pytest tests/integration/test_cli_diff.py tests/integration/test_cli_ci.py` and verify every analysis failure retains precedence and its prior diagnostic

**Checkpoint**: No failed analysis is reinterpreted as empty baseline coverage.

---

## Phase 6: User Story 4 - Adopt Strict Coverage Safely in CI (Priority: P2)

**Goal**: Scope the option visibly to diff, document safe CI use and its limited guarantee, and prove installed wheel/source-distribution equivalence without changing the public demo.

**Independent Test**: Inspect subcommand help, reject the option for check/explain, run the README workflow command, and compare installed wheel/sdist status/stdout/stderr for strict PASS, regression, zero-contract failure, and unavailable-BASE analysis error while the existing demo output remains exact.

### Tests for User Story 4

- [x] T027 [US4] Add parser/help assertions proving normal and CI diff accept `--require-contracts`, diff help displays it, and root/check/explain help do not in `tests/integration/test_cli_diff.py`
- [x] T028 [US4] Add argparse rejection cases for `check --require-contracts` and `explain AGENTS.md:1 --require-contracts` with existing invalid-argument status behavior in `tests/integration/test_cli_diff.py`
- [x] T029 [P] [US4] Add README assertions for default empty success, strict status 2, recommended nonempty CI coverage, the exact consumer command, and the limited natural-language guarantee in `tests/unit/test_readme_release_docs.py`
- [x] T030 [P] [US4] Extend installed wheel and source-distribution checks to run diff help plus identical strict nonempty PASS, confirmed-regression, zero-contract-failure, and unavailable-BASE-analysis-error inputs with exact status/stdout/stderr assertions in `tests/integration/test_cli_installation.py`
- [x] T031 [US4] Extend release smoke expectations for byte-identical wheel/sdist captures of strict PASS status 0, confirmed regression status 1, zero-contract failure status 2, and unavailable-BASE analysis error status 2 in `tests/integration/test_release_validation.py`
- [x] T032 [P] [US4] Confirm the existing public demo command and exact visible output assertions remain unchanged in `tests/integration/test_reproducible_demo.py`

### Implementation and Documentation for User Story 4

- [x] T033 [US4] Update the consumer workflow command and explain default zero coverage, recommended strict CI use, status 2, and the nonempty-only guarantee in `README.md`
- [x] T034 [US4] Extend the shared artifact smoke fixture with identical strict PASS, confirmed-regression, zero-contract-failure, and unavailable-BASE-analysis-error inputs and captured status/stdout/stderr files for wheel/sdist comparison in `scripts/validate-release.sh`
- [x] T035 [US4] Run `uv run pytest tests/integration/test_cli_diff.py tests/integration/test_cli_installation.py tests/integration/test_release_validation.py tests/integration/test_reproducible_demo.py tests/unit/test_readme_release_docs.py`

**Checkpoint**: Users can discover and adopt strict CI coverage from source, wheel, or source distribution without affecting other commands or the demo.

---

## Phase 7: Polish & Cross-Cutting Validation

**Purpose**: Validate the integrated feature against all specification, distribution, runtime, and scope constraints.

- [x] T036 Review the implementation against `specs/009-require-contracts/spec.md` and confirm no edits exist in `src/instrproof/compare.py`, `src/instrproof/models.py`, extraction/discovery modules, package metadata, dependencies, demo logic, or CI structure
- [x] T037 Execute the zero-default, zero-strict, and nonempty-strict fixtures and verify exact outcomes using `specs/009-require-contracts/quickstart.md`
- [x] T038 Run the focused suites with `uv run pytest tests/integration/test_cli_diff.py`, `uv run pytest tests/integration/test_cli_ci.py`, `uv run pytest tests/integration/test_cli_installation.py`, and `uv run pytest tests/integration/test_release_validation.py`
- [x] T039 Run the complete suite with `uv run pytest` and require all existing and new exact-output assertions to pass
- [x] T040 Run the unchanged public demonstration with `./scripts/run-demo.sh` and verify its command text, output, and status remain unchanged
- [x] T041 Run release validation with `./scripts/validate-release.sh` and require wheel/source-distribution installation and captured behavior equivalence to pass
- [x] T042 Verify `.github/workflows/ci.yml` retains the Python 3.12, 3.13, and 3.14 test matrix, then require a successful complete-suite CI job result for every version before completion without modifying the workflow
- [x] T043 Inspect `git diff --check`, `git diff`, and `git status --short`; confirm changes are limited to feature 009 artifacts, `src/instrproof/cli.py`, focused tests, `scripts/validate-release.sh`, and `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on Setup and blocks user-story work.
- **US1 (Phase 3)**: Depends on Foundation and delivers the strict zero-contract MVP.
- **US2 (Phase 4)**: Depends on US1's CLI branch so it can prove unchanged fallback behavior.
- **US3 (Phase 5)**: Depends on US1's post-analysis placement; its tests can be prepared alongside US2, but completion requires the US1 implementation.
- **US4 (Phase 6)**: Depends on US1 for the public option and on US2/US3 for complete compatibility guidance and artifact behavior.
- **Polish (Phase 7)**: Depends on all selected stories.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 -> US2 --+
                          \-> US3 --+-> US4 -> Polish
```

### Within Each User Story

- Write the listed tests first and run them to demonstrate the intended failure or lock existing compatibility behavior.
- Implement only the smallest change needed for that story.
- Run the story checkpoint before advancing.
- Keep `compare_repository()` single-pass and do not modify analysis or domain models.

### Parallel Opportunities

- T007 can run in parallel with the sequential normal-mode T006/T008 work because it changes `tests/integration/test_cli_ci.py`.
- T013, T015, and T017 form one sequential CI-test stream that can run alongside the normal-mode T012/T014/T016/T018 stream.
- T023/T024 form a CI error stream that can run alongside the normal-mode T021/T022 stream.
- T029, T030, and T032 touch independent documentation, four-outcome installation, and demo test files and can run in parallel after US1.
- Story-level test preparation for US3 can proceed alongside US2, but both integrate through the same small `cli.py` policy and must preserve story checkpoints.

---

## Parallel Execution Examples

### User Story 1

```text
Task T006: Add exact normal strict-empty coverage in tests/integration/test_cli_diff.py
Task T007: Add exact CI strict-empty coverage in tests/integration/test_cli_ci.py
```

### User Story 2

```text
Task T012: Lock default and strict normal compatibility in tests/integration/test_cli_diff.py
Task T013: Lock default zero-contract CI compatibility in tests/integration/test_cli_ci.py
```

### User Story 3

```text
Task T021: Add normal error-precedence coverage in tests/integration/test_cli_diff.py
Task T023: Add CI error-precedence coverage in tests/integration/test_cli_ci.py
```

### User Story 4

```text
Task T029: Add README contract assertions in tests/unit/test_readme_release_docs.py
Task T030: Add installed artifact behavior checks in tests/integration/test_cli_installation.py
Task T032: Verify unchanged demo assertions in tests/integration/test_reproducible_demo.py
```

---

## Implementation Strategy

### MVP First

1. Complete Setup and Foundation.
2. Complete US1 tests and the diff-scoped CLI option/post-analysis policy.
3. Stop and validate the US1 checkpoint: both zero-contract modes return 2 with exact stderr and empty stdout.

### Incremental Delivery

1. **US1**: Add strict zero-baseline failure.
2. **US2**: Prove default and positive-count results remain byte-for-byte compatible.
3. **US3**: Lock existing analysis-error precedence.
4. **US4**: Add scoped help, documentation, installed-artifact parity, and unchanged-demo proof.
5. **Polish**: Run focused/full tests, quickstart, demo, release validation, require successful Python 3.12–3.14 CI jobs, and perform final scope review.

### Parallel Team Strategy

After Foundation, implement US1 centrally in `cli.py`. Then separate normal-mode and CI-mode test streams can cover US2 and US3 in parallel. Once behavior is stable, documentation, installed-artifact tests, and demo compatibility checks for US4 can proceed concurrently before the release smoke fixture is finalized.

## Notes

- `[P]` means different-file work with no dependency on an incomplete task; tasks sharing a file are deliberately serialized.
- Story labels provide traceability to [spec.md](spec.md).
- Every observable production behavior has a preceding focused test.
- Existing user changes and unrelated worktree content must remain intact.
- Required validation failures block completion and must be reported rather than waived.
