# Tasks: Reproducible Public Demo

**Input**: Design documents from `/specs/007-presentation-ready-demo/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Automated subprocess execution of the complete public demo is required. Story-specific test tasks precede their corresponding runner behavior.

**Organization**: Tasks are grouped by user story so the core product story, safe repeatability, retained inspection, and automated contract protection remain independently verifiable increments.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it targets a different file and has no dependency on incomplete work
- **[Story]**: Maps the task to a user story in `spec.md`
- Every task names an exact repository path

## Phase 1: Setup (Static Demo Template)

**Purpose**: Establish the immutable, minimal public repository input used by every story.

- [X] T001 [P] Add the single supported inline `src/auth/service.py` claim and no other contract evidence in `examples/demo-repo/AGENTS.md`
- [X] T002 [P] Add the dependency-free baseline authentication behavior in `examples/demo-repo/src/auth/service.py`
- [X] T003 [P] Add one standard-library application test importing the baseline service in `examples/demo-repo/tests/test_service.py`

---

## Phase 2: Foundational (Safe Runner Boundary)

**Purpose**: Create the argument-safe, isolated execution boundary required before any presentation stage can run.

**⚠️ CRITICAL**: Complete this phase before user-story work; every story consumes the same runner, temporary repository, CLI invocation, and cleanup boundary.

- [X] T004 Add failing foundational subprocess tests for shell syntax, no-argument invocation prerequisites, unsupported-argument status 2, caller-independent root resolution, immutable template expectations, and absence of `.git` content in `tests/integration/test_reproducible_demo.py`
- [X] T005 Implement `scripts/run-demo.sh` argument parsing, concise usage, Git/uv/template/CLI prerequisite checks, project-root resolution, fixed argument-safe `uv run --project` invocation, `mktemp` allocation, template copying, local Git identity, baseline commit, immutable `demo-base`, and default exit/signal cleanup in `scripts/run-demo.sh`
- [X] T006 Make `scripts/run-demo.sh` executable and run the foundational syntax, usage, prerequisite, initialization, and template checks in `tests/integration/test_reproducible_demo.py`

**Checkpoint**: The public entry point safely creates and cleans a real isolated demonstration repository but does not yet perform the three-stage story.

---

## Phase 3: User Story 1 - Catch and Resolve a Stale Instruction (Priority: P1) 🎯 MVP

**Goal**: Present the complete baseline-to-regression-to-repair product story with exact real CLI diagnostics and statuses.

**Independent Test**: Run `./scripts/run-demo.sh` once and verify the three labels appear exactly once and in order, baseline inspection reports one expected contract, broken comparison against `demo-base` reports one expected regression/status 1, repaired comparison against the same BASE reports no regression/status 0, application tests pass at every stage, and the final explanation is understandable on its own.

### Tests for User Story 1

- [X] T007 [US1] Add failing full-workflow subprocess assertions for exact stage labels/order, displayed commands/changes, application-test passes, baseline total/type/source/target, broken regression count/diagnostic/status 1, repaired no-regression/status 0, shared `demo-base`, and final explanation in `tests/integration/test_reproducible_demo.py`

### Implementation for User Story 1

- [X] T008 [US1] Implement the stable `[1/3]` baseline stage, application test execution, real `instrproof check` capture, and exact one-contract validation in `scripts/run-demo.sh`
- [X] T009 [US1] Implement the stable `[2/3]` refactor stage with `git mv` to `src/auth/auth_service.py`, test-import update, unchanged-instruction/old-path assertions, bounded diff, passing application test, explicit status capture, and exact one-regression validation in `scripts/run-demo.sh`
- [X] T010 [US1] Implement the stable `[3/3]` repair stage with in-place claim update, instruction/BASE identity assertions, bounded instruction diff, passing application test, status-0/no-regression validation, and concise final product explanation in `scripts/run-demo.sh`
- [X] T011 [US1] Run the complete default workflow and focused User Story 1 assertions in `tests/integration/test_reproducible_demo.py`, correcting only `examples/demo-repo/` and `scripts/run-demo.sh` contract defects

**Checkpoint**: A reviewer can run one command and see the independently complete InstrProof value story; this is the MVP.

---

## Phase 4: User Story 2 - Safe and Reproducible Live Runs (Priority: P2)

**Goal**: Prove default success, failure, interruption, outside-checkout use, and repeated runs never mutate the parent or leave unretained state.

**Independent Test**: Snapshot parent porcelain plus every NUL-enumerated tracked/non-ignored-untracked path's type, bytes/digest, symlink target, and executable mode; add a verified-unused untracked sentinel with known bytes and retain a stable tracked file's bytes; invoke the script by absolute path from a neutral directory three times; and verify exact parent equality, equivalent output/statuses, automatic cleanup, no active child, and attributable nonzero failures.

### Tests for User Story 2

- [X] T012 [US2] Add failing subprocess tests in `tests/integration/test_reproducible_demo.py` that preserve before/after `git status --porcelain`, build exact canonical snapshots from NUL-delimited `git ls-files --cached --others --exclude-standard` entries (relative path, file type, complete-byte SHA-256, symlink target, relevant executable mode), require identical Git-visible path sets and tracked/untracked state, create a collision-resistant verified-unused parent untracked sentinel with known nonempty bytes, assert its same-path byte equality plus byte equality for a stable tracked file, and remove only the sentinel in `finally` without hiding the original demo failure or deleting unrelated files
- [X] T013 [US2] Add failing three-run exact normalized-output equivalence, under-30-second runtime, no-network-after-setup, missing-prerequisite, unexpected-command-result, and interruption cleanup assertions in `tests/integration/test_reproducible_demo.py`

### Implementation for User Story 2

- [X] T014 [US2] Add parent before/after porcelain plus canonical Git-visible path/type/content-digest/symlink-target/executable-mode snapshot comparison on success, failure, and interruption, with ignored files excluded unless directly targeted and no timestamp/size reliance, alongside stable output, stage-attributable errors, and hardened safe cleanup/termination in `scripts/run-demo.sh`
- [X] T015 [US2] Run User Story 2 isolation, failure, interruption, runtime, outside-checkout, and three-run repeatability scenarios in `tests/integration/test_reproducible_demo.py`

**Checkpoint**: Default live presentations are isolated, deterministic, fast, offline after setup, self-cleaning, and proven not to alter parent porcelain, Git-visible paths, tracked content, pre-existing untracked content, file types, symlink targets, or relevant executable modes.

---

## Phase 5: User Story 3 - Retain and Inspect the Demo Repository (Priority: P3)

**Goal**: Let users explicitly retain an initialized final repository, inspect its real BASE and repaired state, and rerun the comparisons manually.

**Independent Test**: Run `./scripts/run-demo.sh --keep`, parse the one retained absolute path, verify it is a valid Git repository whose `demo-base` is preserved and whose source/instruction are repaired, rerun documented checks, then safely delete the test-owned path.

### Tests for User Story 3

- [X] T016 [US3] Add failing `--keep` subprocess tests for one final retained-path marker, valid Git metadata, resolvable `demo-base`, repaired instruction/source state, passing application test, and manual comparison reruns in `tests/integration/test_reproducible_demo.py`
- [X] T017 [US3] Add failing retention-boundary tests proving pre-initialization failures still clean up and post-initialization failures remain nonzero while exposing attributable retained state in `tests/integration/test_reproducible_demo.py`

### Implementation for User Story 3

- [X] T018 [US3] Implement initialization-gated `--keep` cleanup policy, preserved final/failed repository state, and exactly one final absolute retained-path line in `scripts/run-demo.sh`
- [X] T019 [US3] Add public retention, inspection, manual `check`/`diff --base demo-base --ci` rerun, and user-owned cleanup guidance to the `Reproducible demo` section in `README.md`
- [X] T020 [US3] Run all User Story 3 keep-mode, retained-state, manual-rerun, and cleanup tests in `tests/integration/test_reproducible_demo.py`

**Checkpoint**: Opt-in inspection works without weakening default cleanup or masking operational failures.

---

## Phase 6: User Story 4 - Trust the Public Demo Contract (Priority: P4)

**Goal**: Protect the public story against drift in template evidence, stage ordering, BASE identity, diagnostics, statuses, isolation, cleanup, and compatibility.

**Independent Test**: Run the focused integration module and verify it executes the real public script and would fail for changes to the source, target, count, order, statuses, BASE, repair state, or cleanup; then run the complete suite and retain all prior behavior.

### Tests for User Story 4

- [X] T021 [US4] Strengthen exact template-source, old/new-target, stage-count/order, regression-count, status-marker, final-message, and same-BASE contract assertions in `tests/integration/test_reproducible_demo.py`
- [X] T022 [US4] Add deterministic test-local `PATH` shim scenarios for missing or misbehaving Git/uv/InstrProof processes, wrong status, wrong diagnostic, and attributable nonzero runner failures in `tests/integration/test_reproducible_demo.py`

### Implementation for User Story 4

- [X] T023 [US4] Resolve failure-contract gaps exposed by T021-T022 using fixed commands and validation only in `scripts/run-demo.sh`, without adding public command overrides or touching `src/instrproof/`
- [X] T024 [US4] Run the entire focused public-demo test module and confirm every test invokes `scripts/run-demo.sh` through subprocess in `tests/integration/test_reproducible_demo.py`

**Checkpoint**: The public demonstration has automated, externally observable protection against story and safety regressions.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Complete public guidance and prove performance, compatibility, architectural boundaries, and clean repository scope.

- [X] T025 Add prerequisites, one-command default invocation, three-stage explanation, expected status 1, under-30-second expectation, offline behavior, and parent-isolation guarantees to the `Reproducible demo` section in `README.md`
- [X] T026 Execute every default, `--keep`, outside-checkout, failure, interruption, repeatability, and manual retained-repository scenario from `specs/007-presentation-ready-demo/quickstart.md`
- [X] T027 Run the complete automated suite and confirm the existing 285 tests plus all new tests pass using `tests/`
- [X] T028 Run `scripts/validate-release.sh` and confirm feature 006 artifact behavior remains passing without modifying `scripts/validate-release.sh`
- [X] T029 Inspect `git diff --check`, `git diff`, and `git status`; confirm `.github/workflows/ci.yml`, `src/instrproof/`, and feature 006 fixtures are untouched and remove only feature-created temporary residue

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately; its three static-template files can be authored in parallel.
- **Foundational (Phase 2)**: Depends on Setup and blocks every user story.
- **US1 (Phase 3)**: Depends on Foundation and delivers the independently runnable MVP.
- **US2 (Phase 4)**: Depends on US1's complete default runner so isolation and repeatability exercise the real story.
- **US3 (Phase 5)**: Depends on Foundation and the completed US1 repository state transitions; its test authoring can begin while US2 hardening proceeds, but runner edits remain sequential.
- **US4 (Phase 6)**: Depends on US1-US3 interfaces being stable so it can lock the final public contract.
- **Polish (Phase 7)**: Depends on all selected user stories.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 (MVP) -> US2
                           |       |
                           +-> US3-+
                                  |
                                  v
                                 US4 -> Polish
```

- **US1 (P1)**: Establishes all three product stages and is the MVP.
- **US2 (P2)**: Hardens the default US1 workflow for safe live presentation.
- **US3 (P3)**: Adds opt-in persistence over the US1 temporary repository without changing the core story.
- **US4 (P4)**: Consolidates automated protection after all public behavior is stable.

### Within Each User Story

- Add subprocess tests first and confirm they fail for the missing story behavior.
- Implement only the smallest runner or documentation change needed for that story.
- Run focused tests at the story checkpoint before moving to the next priority.
- Serialize edits to `scripts/run-demo.sh` and `tests/integration/test_reproducible_demo.py` even when conceptual work could overlap.
- Never change `src/instrproof/`, `.github/workflows/ci.yml`, or `scripts/validate-release.sh` to satisfy demo tests.

### Parallel Opportunities

- T001, T002, and T003 target independent template files and can run in parallel.
- After Foundation, US3 test design can be prepared while US2 requirements are reviewed, but shared-file edits must be serialized before merge.
- README retention guidance T019 can be drafted after the keep interface is fixed while separate test review proceeds.
- Boundary review of unchanged production/release files can begin while the full suite runs in Polish.

---

## Parallel Example: Setup

```text
Task T001: Add examples/demo-repo/AGENTS.md
Task T002: Add examples/demo-repo/src/auth/service.py
Task T003: Add examples/demo-repo/tests/test_service.py
```

## Parallel Example: User Story 3

```text
Sequential shared-file work: T016 -> T017 -> T018
After T018 fixes the interface, review T019 README.md while preparing the T020 focused run.
```

---

## Implementation Strategy

### MVP First

1. Complete the minimal static template.
2. Complete safe runner initialization and cleanup foundation.
3. Add failing end-to-end assertions for the product story.
4. Implement baseline, broken refactor, and repair stages.
5. Stop and validate the default one-command workflow as the presentation-ready MVP.

### Incremental Delivery

1. **US1**: One understandable baseline-to-failure-to-repair demo.
2. **US2**: Safe, fast, repeatable default operation from any directory.
3. **US3**: Explicit retained-repository inspection and manual reruns.
4. **US4**: Complete automated protection against public-contract drift.
5. **Polish**: Documentation, full suite, feature 006 validation, and scope review.

### Scope Guardrails

- Use only the existing Git, uv, Bash, Python standard library, pytest, and InstrProof CLI capabilities.
- Keep the template static and minimal; never initialize Git inside `examples/demo-repo/`.
- Do not add dependencies, production CLI behavior, contract types, package scripts, CI changes, release-fixture changes, network operations, containers, hosted integrations, media generation, or extra platform guarantees.
- Treat expected broken status 1 as domain behavior while rejecting every other unexpected status or diagnostic.

## Notes

- `[P]` marks truly independent file work only.
- Story labels trace each task to its independently testable user outcome.
- Every runner test uses subprocess at the public interface boundary.
- Commit after each task or cohesive story checkpoint.
- Stop at any checkpoint to validate the increment independently.

---

## Phase 8: Convergence

- [X] T030 Display a bounded HEAD-relative refactor diff that visibly includes the staged `src/auth/service.py` to `src/auth/auth_service.py` rename alongside the test import update, and add an observable subprocess assertion in `tests/integration/test_reproducible_demo.py` per FR-007 and plan: Stable three-stage presentation (partial)

---

## Phase 9: Convergence

- [X] T031 Expand the final stable plain-language output and exact subprocess assertions to connect the ordinary source refactor, unchanged instruction, missing old-path evidence, expected CI status 1, coordinated instruction repair, and restored CI status 0 per FR-016, US1/AC4, and SC-011 (partial)
- [X] T032 Validate that audit and demo roots are allocated outside the parent repository and safely clean the exact allocated roots for supported absolute temporary bases beyond `/tmp`, with subprocess coverage for a non-`/tmp` base and rejection or safe fallback when `TMPDIR` points inside the parent per FR-002, FR-020, SC-007, and plan: Cleanup and retention (partial)
