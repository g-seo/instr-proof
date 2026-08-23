# Tasks: Release-Ready Distribution

**Input**: Design documents from `/specs/006-release-readiness/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Focused automated tests are required by the specification. Story-specific test tasks precede their implementation tasks.

**Organization**: Tasks are grouped by user story so release-candidate installation, artifact equivalence, CI, and documentation remain independently verifiable increments.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it targets different files and does not depend on incomplete behavior
- **[Story]**: Maps to a prioritized user story in spec.md
- Every task names exact repository paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the repository-level license required by every release path.

- [X] T001 Add the complete unmodified Apache License 2.0 text to `LICENSE`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish one authoritative package manifest shared by all installation, artifact, CI, and documentation work.

**⚠️ CRITICAL**: Complete this phase before user-story work because every later check consumes the manifest and lock file.

- [X] T002 Configure PEP 621 description, README, dynamic version sourcing from `src/instrproof/__init__.py`, Python requirement/classifiers, author data, canonical Repository/Issues URLs, Apache-2.0 expression/license files, empty runtime dependencies, development-only Twine, and explicit Hatchling wheel/sdist selection in `pyproject.toml`
- [X] T003 Regenerate and verify the locked development dependency graph after the manifest change in `uv.lock`

**Checkpoint**: The repository has a licensed, dependency-free, single-version-source package manifest and reproducible development tool lock.

---

## Phase 3: User Story 1 - Prepare and Install a Release Candidate (Priority: P1) 🎯 MVP

**Goal**: Produce a locally installable release candidate with compatibility floor `>=3.12`, explicit complete-suite validation on 3.12–3.14, and designated Python 3.12 artifact behavior outside the checkout, including through a VCS installation path.

**Independent Test**: Run the complete suite on Python 3.12, 3.13, and 3.14; then build once, install each artifact in its own clean designated Python 3.12 environment outside the repository, run help/version/import and representative check/diff commands, and prove the VCS path with an isolated local Git URL on Python `>=3.12` without network access.

### Tests for User Story 1

- [X] T004 [P] [US1] Add failing tests for exact root `--version` stdout, stderr, status, root-help visibility, and absence of repository discovery in `tests/unit/test_cli_version.py`
- [X] T005 [P] [US1] Add package-manifest tests for identity, one dynamic version source, `>=3.12` compatibility floor, explicitly tested 3.12–3.14 classifiers without an upper bound, zero runtime dependencies, entry point, description, URLs, artifact selection, and Apache licensing in `tests/unit/test_packaging.py`
- [X] T006 [P] [US1] Add designated-Python-3.12 clean installed-command coverage for wheel and source distribution plus a local Git VCS URL on Python `>=3.12`, including arbitrary-working-directory help/version/import and representative existing check/diff output/status behavior in `tests/integration/test_cli_installation.py`

### Implementation for User Story 1

- [X] T007 [US1] Add argparse's root-level `instrproof --version` action backed by `instrproof.__version__` without changing existing subcommand dispatch in `src/instrproof/cli.py`
- [X] T008 [US1] Build and install both artifacts by explicit paths in designated Python 3.12 environments plus the checkout through a local Git VCS URL, resolving defects only in `pyproject.toml`, `src/instrproof/__init__.py`, `src/instrproof/cli.py`, and `src/instrproof/__main__.py`
- [X] T009 [US1] Run the focused version, package-manifest, installed-command, and existing CLI compatibility suites in `tests/unit/test_cli_version.py`, `tests/unit/test_packaging.py`, `tests/integration/test_cli_installation.py`, and `tests/integration/test_cli_*.py`

**Checkpoint**: The release candidate is installable without source-tree imports and the public CLI/version contract works; this is the MVP.

---

## Phase 4: User Story 2 - Verify Distribution Artifacts (Priority: P2)

**Goal**: Provide one clean, fail-fast local command that builds once, inspects both artifacts, installs them separately, and compares real CLI behavior without substituting an InstrProof production release.

**Independent Test**: Run `scripts/validate-release.sh`; confirm a fresh locked environment may download dependencies from configured indexes, performs one Python 3.12 build, validates separate designated-3.12 artifact environments and behavioral equality, cleans safely, and never installs/queries an InstrProof production release, uploads, or requires credentials.

### Tests for User Story 2

- [X] T010 [P] [US2] Add failing unit tests with synthetic archives for valid artifacts, missing metadata/license/entry point/package files, mismatched versions, unexpected counts, and timestamp/order-insensitive normalization rules in `tests/unit/test_artifact_inspection.py`
- [X] T011 [P] [US2] Add failing behavioral tests for named phases, fresh development and designated-3.12 artifact environments, cleanup, explicit paths, checkout isolation, expected status 1, cross-artifact comparison, permitted locked dependency resolution, and absence of InstrProof production-release query/install, upload, or credential commands in `tests/integration/test_release_validation.py`

### Implementation for User Story 2

- [X] T012 [US2] Implement non-extracting wheel/sdist inspection and stable metadata/content/version/entry-point/license comparison using only the Python standard library in `scripts/inspect_artifacts.py`
- [X] T013 [US2] Implement fresh locked dependency setup with configured-index downloads allowed, complete tests, one Python 3.12 `uv build`, strict Twine checks, separate designated-3.12 artifact installs, neutral fixtures, command-result capture/comparison, labelled failures, safe cleanup, and no InstrProof production-release query/install, upload, or credentials in `scripts/validate-release.sh`
- [X] T014 [US2] Make the validator executable and run its complete contract end-to-end, fixing only release-related failures in `scripts/validate-release.sh`, `scripts/inspect_artifacts.py`, and `pyproject.toml`

**Checkpoint**: Both local artifacts are independently installed and behaviorally equivalent without uploading to or reading a released package from production PyPI.

---

## Phase 5: User Story 3 - Trust Automated Project Validation (Priority: P3)

**Goal**: Provide visible, distinguishable test-matrix, build/metadata, wheel, source-distribution, and equivalence results on pull requests and `main` pushes.

**Independent Test**: Validate the workflow contract, then observe Python 3.12/3.13/3.14 tests, one Python 3.12 build/upload, separate downloaded-artifact installations, representative CLI results, and behavioral comparison under read-only permissions with no publishing step.

### Tests for User Story 3

- [X] T015 [US3] Add failing workflow contract tests for required triggers, read-only permissions, 3.12–3.14 matrix, locked complete tests, one designated build, strict metadata/content checks, artifact transfer, separate wheel/sdist validation, equivalence comparison, stable-major actions, and absence of publishing/secrets in `tests/unit/test_ci_workflow.py`

### Implementation for User Story 3

- [X] T016 [US3] Add pull-request and `main` push automation with named test-matrix, single Python 3.12 build/validate/upload, wheel validation, source-distribution validation, and artifact-equivalence stages in `.github/workflows/ci.yml`
- [X] T017 [US3] Reuse the local artifact-validation behavior in CI while retaining distinct failure attribution and transferred-artifact paths in `.github/workflows/ci.yml` and `scripts/validate-release.sh`
- [X] T018 [US3] Run workflow contract tests and verify all committed workflow commands and dependencies in `tests/unit/test_ci_workflow.py` and `.github/workflows/ci.yml`

**Checkpoint**: Repository CI exposes every required release-health domain without production publication or credentials.

---

## Phase 6: User Story 4 - Follow Accurate Public Documentation (Priority: P4)

**Goal**: Give users and maintainers copy-and-run installation, consumer CI, pre-release, manual publication-boundary, and post-publication verification guidance.

**Independent Test**: Execute local, GitHub, and artifact-based instructions before publication; statically validate the consumer workflow; after a manual release exists, execute the exact-version production-PyPI procedure separately.

### Tests for User Story 4

- [X] T019 [US4] Add failing documentation contract tests for separate installation paths, selected consumer version, BASE availability, statuses 0/1/2, allowed dependency downloads, pre-release independence from published InstrProof, manual-only publication, and exact-version post-publication verification in `tests/unit/test_readme_release_docs.py`

### Implementation for User Story 4

- [X] T020 [US4] Replace the combined setup section with separate copy-and-run PyPI, canonical GitHub repository, built-artifact, and local contributor installation sections in `README.md`
- [X] T021 [US4] Update the consumer GitHub Actions example to fetch sufficient history, use supported Python, install an explicitly selected published InstrProof version, materialize `origin/main`, and run `instrproof diff --base origin/main --ci` in `README.md`
- [X] T022 [US4] Document statuses 0/1/2, dependency downloads versus published-InstrProof independence in `scripts/validate-release.sh`, artifact expectations, manual publication boundary, and conditional exact-version post-publication PyPI help/version/check/diff procedure in `README.md`
- [X] T023 [US4] Run documentation contract tests and copy-and-run pre-publication checks, resolving documentation-only failures in `tests/unit/test_readme_release_docs.py` and `README.md`

**Checkpoint**: Public guidance clearly separates locally provable readiness from the verification performed only after manual publication.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Prove compatibility, artifact integrity, quickstart accuracy, and repository scope before implementation handoff.

- [X] T024 [P] Add an end-to-end comparison of two independently built artifact sets using T010's normalization rules to compare stable member bytes/modes while ignoring unsupported ordering/timestamps in `tests/unit/test_artifact_inspection.py`
- [X] T025 Run all automated tests and confirm the original 250-test compatibility baseline plus new release tests pass using `tests/`
- [X] T026 Run all pre-publication quickstart and local validation scenarios, recording and resolving contract mismatches in `specs/006-release-readiness/quickstart.md`, `scripts/validate-release.sh`, and `scripts/inspect_artifacts.py`
- [X] T027 Inspect `git diff --check`, `git diff`, and `git status`; remove only feature-created residue and confirm changes stay within `specs/006-release-readiness/plan.md` scope

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup** starts immediately.
- **Foundation** depends on Setup and blocks every story.
- **US1** depends on Foundation and establishes the installable release-candidate MVP.
- **US2** depends on Foundation and uses the CLI/version contract completed by US1 for full behavioral comparison.
- **US3** depends on US2 because CI invokes the artifact inspection and validation interfaces.
- **US4** depends on stable US1–US3 command and workflow interfaces so its copy-and-run procedures do not drift.
- **Polish** depends on all selected stories.

### User Story Dependency Graph

```text
Setup -> Foundation -> US1 (MVP)
                    -> US2 -> US3 -> US4
                         \----------> US4
Completed stories -> Polish
```

- **US1 (P1)**: Independently proves release-candidate installation after Foundation.
- **US2 (P2)**: Can start its test/inspector work after Foundation; complete behavior comparison consumes US1's version option.
- **US3 (P3)**: Requires US2's validator and inspector.
- **US4 (P4)**: Documents finalized interfaces; post-publication execution remains conditional on an external manual release.

### Within Each User Story

- Add focused failing tests before story-specific behavior.
- Implement the smallest change that satisfies the relevant contract.
- Run focused tests and the independent scenario before the checkpoint.
- Never change semantic-engine modules merely to satisfy packaging validation.

## Parallel Opportunities

- T004, T005, and T006 target separate test files and can be authored concurrently.
- T010 and T011 can be authored concurrently before T012/T013.
- US1 test authoring and US2 test authoring can overlap after Foundation.
- T024 can be prepared after T012 while documentation verification proceeds.

## Parallel Example: User Story 1

```text
Task T004: Add version tests in tests/unit/test_cli_version.py
Task T005: Add manifest tests in tests/unit/test_packaging.py
Task T006: Add clean installed-command tests in tests/integration/test_cli_installation.py
```

## Parallel Example: User Story 2

```text
Task T010: Add archive-inspector tests in tests/unit/test_artifact_inspection.py
Task T011: Add release-validation behavior tests in tests/integration/test_release_validation.py
```

## Parallel Example: User Story 3

```text
Task T015: Define workflow contract assertions in tests/unit/test_ci_workflow.py
Review: Compare .github/workflows/ci.yml design with specs/006-release-readiness/contracts/release-validation.md before T016
```

## Parallel Example: User Story 4

```text
Task T019: Define README contract assertions in tests/unit/test_readme_release_docs.py
Review: Prepare copy-and-run checks from specs/006-release-readiness/quickstart.md before T020
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundation.
2. Complete US1 tests and implementation.
3. Stop and validate both local artifacts, VCS installation, help/version/import, and representative commands outside the checkout.
4. Treat this as the release-candidate MVP; production upload remains manual and out of scope.

### Incremental Delivery

1. **US1**: Installable, versioned release candidate.
2. **US2**: One clean local build/inspection/install/equivalence command.
3. **US3**: Multi-version tests and visible transferred-artifact CI validation.
4. **US4**: Accurate pre-publication and conditional post-publication guidance.
5. **Polish**: Full test, quickstart, reproducibility, diff, and status validation.

### Scope Guardrails

- Do not edit `src/instrproof/compare.py`, `discovery.py`, `extract.py`, `models.py`, or `repository.py` unless a newly discovered requirement is first recorded in the Spec Kit artifacts.
- Do not add runtime dependencies, credentials, automated uploads, GitHub Releases, Trusted Publishing, Marketplace registration, demo feature 007, rename-to-failure demonstrations, new contract types, semantic changes, or platform-specific guarantees.
- Pre-release dependency downloads from configured indexes are allowed, but tests and validation must not query/install an InstrProof production release; the exact-version production check is manual and conditional after publication.

## Notes

- `[P]` marks tasks that can execute concurrently without file conflicts or incomplete dependencies.
- Story labels map to the four prioritized scenarios in `spec.md`.
- Temporary dependency/build/install environments must use safely generated paths and explicit cleanup targets.
- Expected regression status 1 is a captured fixture result, not an orchestration failure.
- Commit after each task or cohesive task group and stop at story checkpoints for independent validation.

## Phase 8: Convergence

- [X] T028 Add synthetic wheel and source-distribution rejection tests for missing METADATA/PKG-INFO, invalid required metadata fields, and missing required package files in `tests/unit/test_artifact_inspection.py` per T010, FR-017, and SC-004 (partial)
- [X] T029 Add executable validator failure-path tests proving a missing installed CLI and unequal captured artifact results return nonzero with attributable errors in `tests/integration/test_release_validation.py` per US2/AC4, FR-017, SC-004, and Constitution II (partial)
- [X] T030 Split CI distribution building from metadata/content validation into separately named steps while reusing auditable `scripts/validate-release.sh` interfaces in `.github/workflows/ci.yml`, `scripts/validate-release.sh`, and `tests/unit/test_ci_workflow.py` per FR-016, US3/AC4, and plan: Continuous integration (partial)

## Phase 9: Convergence

- [X] T031 Align clean artifact-build and VCS-install tests with permitted configured-index build-dependency resolution, removing the empty-cache `--offline` contradiction or explicitly provisioning locked Hatchling before offline execution in `tests/integration/test_cli_installation.py`, `tests/integration/test_release_validation.py`, and `tests/unit/test_artifact_inspection.py`, then rerun all 285 tests and `scripts/validate-release.sh` per FR-018, FR-021, SC-005, and US1/AC1-4 (partial)
