# Feature Specification: Presentation-Ready InstrProof Demo

**Feature Branch**: `[007-presentation-ready-demo]`

**Created**: 2026-08-24

**Status**: Draft

**Input**: User description: "Create a reproducible, presentation-ready public demonstration that proves InstrProof detects a stale path instruction after an ordinary repository refactor and confirms recovery after the instruction is repaired."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See InstrProof Catch and Resolve a Stale Instruction (Priority: P1)

A reviewer runs one documented command and watches a short, clearly labelled story: a repository begins healthy, a source file is moved while its AI instruction remains stale, InstrProof reports exactly one regression, and updating the instruction restores a passing result.

**Why this priority**: This is the core product demonstration. It makes InstrProof's value understandable without requiring the reviewer to inspect source code or know its internal model.

**Independent Test**: Run the complete demonstration once and verify the baseline, broken-refactor, and repaired-instruction stages appear in order; the broken stage reports one expected path regression with status 1; and the repaired stage uses the same baseline, reports no regression, and exits 0.

**Acceptance Scenarios**:

1. **Given** an isolated demonstration repository containing one valid source file and one instruction that references it, **When** the baseline stage runs, **Then** the repository is committed as an immutable baseline and InstrProof confirms that the current instruction contract is valid.
2. **Given** the baseline repository, **When** the demonstrated refactor moves or renames the referenced source file without changing the instruction, **Then** the repository remains usable and the displayed comparison against the baseline reports exactly one `PathExists` regression for the documented instruction source and old target, with status 1.
3. **Given** the broken refactor and its expected regression, **When** the instruction is updated to the new source path without removing the instruction file or changing the baseline, **Then** the displayed comparison reports no regression and status 0.
4. **Given** a reviewer unfamiliar with InstrProof internals, **When** the demonstration finishes, **Then** the final explanation clearly connects the ordinary refactor, stale AI instruction, missing repository evidence, CI failure, coordinated repair, and CI success.

---

### User Story 2 - Run a Safe and Reproducible Live Demonstration (Priority: P2)

A presenter can run the demonstration repeatedly without changing the InstrProof checkout, relying on network access, or manually cleaning temporary state.

**Why this priority**: A live demonstration must be trustworthy and repeatable; residue, checkout mutations, or non-deterministic stages would undermine the product story.

**Independent Test**: Snapshot the parent repository state, run the demonstration three consecutive times after local setup, and verify equivalent stage ordering, diagnostics, and statuses while the parent repository remains unchanged and temporary repositories are removed.

**Acceptance Scenarios**:

1. **Given** completed local project setup, **When** the demonstration runs, **Then** it creates a separate temporary Git repository, uses a real commit or tag as the shared baseline, invokes the real local InstrProof command, and requires no network access.
2. **Given** a successful demonstration, **When** it exits normally, **Then** temporary files are removed and the parent InstrProof repository has no tracked or untracked changes caused by the run.
3. **Given** an unexpected command status, missing diagnostic, setup error, repair failure, or user interruption, **When** the demonstration stops, **Then** it returns nonzero, terminates its active work, cleans its temporary files, and leaves the parent repository unchanged.
4. **Given** the same InstrProof revision and local setup, **When** the demonstration runs three times, **Then** all runs present equivalent stage order, known source and target diagnostics, regression counts, and command statuses apart from explicitly identified temporary paths or baseline identifiers.

---

### User Story 3 - Retain and Inspect the Demonstration Repository (Priority: P3)

A curious reviewer can explicitly retain the generated repository, see where it was stored, and inspect the final demonstration state after the workflow finishes.

**Why this priority**: Retention supports deeper review and troubleshooting without weakening the safe cleanup default required for normal presentations.

**Independent Test**: Run the documented retention mode and verify the generated repository remains available at a displayed location, contains the baseline history and repaired instruction, and can be removed manually using the documented guidance.

**Acceptance Scenarios**:

1. **Given** the default cleanup behavior, **When** a user explicitly requests retention before running the demo, **Then** the generated repository is preserved and its location is clearly displayed.
2. **Given** a retained repository, **When** the user inspects its history and working tree, **Then** the original baseline remains identifiable and the final instruction refers to the moved source file.
3. **Given** the public documentation, **When** a user wants to inspect or remove retained files, **Then** concise instructions explain the retention option, generated location, expected contents, and cleanup responsibility.

---

### User Story 4 - Trust the Public Demo Contract (Priority: P4)

A maintainer receives automated protection against accidental changes to the demo's story, expected diagnostic, stage ordering, statuses, isolation, or cleanup behavior.

**Why this priority**: The demo is a public product surface. Automated execution prevents a presentation from silently drifting away from real InstrProof behavior.

**Independent Test**: Execute the automated demo checks and verify they run the complete workflow, assert every required stage and status, and fail when the expected source, target, regression count, order, cleanup, or repair outcome is altered.

**Acceptance Scenarios**:

1. **Given** the completed public demo, **When** the automated suite runs, **Then** it executes the full baseline-to-failure-to-repair workflow and verifies its observable output and statuses.
2. **Given** a change to the expected source, old target, regression count, stage order, broken-stage status, repaired-stage status, shared baseline, or cleanup outcome, **When** automated checks run, **Then** at least one focused check fails with an attributable assertion.
3. **Given** the new demo checks, **When** the complete project suite runs, **Then** all 285 pre-existing tests remain passing and existing command behavior is unchanged.

### Edge Cases

- The local InstrProof executable is missing, cannot start, or resolves outside the prepared project environment.
- Git is unavailable, repository initialization fails, or the real baseline identifier cannot be resolved.
- The expected baseline instruction contract is absent, ambiguous, or does not resolve to the known source file.
- The refactor accidentally changes or removes the instruction file, creates more than one regression, or leaves the old source path present.
- The broken comparison returns 0 or 2 instead of the expected domain status 1.
- The broken output reports the wrong instruction source, contract type, target, or regression count.
- The repaired comparison uses a different baseline, removes the instruction claim, or still returns a regression.
- A stale temporary directory or retained prior run exists before a new demonstration starts.
- Cleanup is requested after a setup or validation failure, including interruption during an important command.
- Retention is explicitly requested on a failed run; failure remains nonzero and the generated location is still made understandable to the user.
- Temporary paths or commit identifiers differ across runs while all product-relevant output remains equivalent.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST provide one documented command that runs the complete public demonstration after normal local setup.
- **FR-002**: The demonstration MUST create and operate on an isolated temporary repository and MUST NOT create, modify, or delete tracked or untracked content in the parent InstrProof repository.
- **FR-003**: The demonstration MUST create a real immutable Git baseline containing exactly the minimal evidence needed for the product story: one instruction source, one referenced source file, and repository history sufficient for comparison.
- **FR-004**: The baseline instruction MUST contain one repository-grounded path claim that resolves to the baseline source file.
- **FR-005**: The demonstration MUST invoke the real locally prepared InstrProof command and MUST exercise the existing current-contract inspection and CI comparison workflows.
- **FR-006**: The demonstration MUST visibly label the baseline, broken-refactor, and repaired-instruction stages in that order.
- **FR-007**: Before each important command or repository mutation, the demonstration MUST display the command or change and explain its role in the story.
- **FR-008**: The baseline stage MUST prove that the instruction contract is valid before the refactor begins.
- **FR-009**: The broken-refactor stage MUST move or rename the referenced source file while leaving the instruction claim unchanged and the demonstration repository otherwise usable.
- **FR-010**: The broken-refactor comparison MUST use the immutable demonstration baseline and report exactly one `PathExists` regression for the documented instruction source and old target.
- **FR-011**: Status 1 from the broken-refactor comparison MUST be presented and accepted as the expected demonstration result rather than causing premature script termination.
- **FR-012**: Any broken-stage status other than 1, missing or unexpected diagnostic, wrong regression count, or setup failure MUST cause the overall demonstration to fail with a nonzero status.
- **FR-013**: The repair stage MUST update the existing instruction claim to the moved source path without removing the instruction source.
- **FR-014**: The repaired comparison MUST use the same immutable baseline as the broken comparison, report no instruction contract regression, and return status 0.
- **FR-015**: A repair-stage nonzero status, remaining regression, changed baseline, removed instruction source, or instruction claim that does not reference the new source MUST cause the overall demonstration to fail nonzero.
- **FR-016**: The final output MUST explain the complete product story in plain language: ordinary refactor, unchanged stale AI instruction, missing evidence, CI failure, coordinated instruction repair, and CI success.
- **FR-017**: Once project dependencies are installed, the demonstration MUST complete without network access or external services.
- **FR-018**: Under the supported Linux environment, the full workflow MUST complete within 30 seconds excluding initial dependency installation.
- **FR-019**: Repeated runs from the same InstrProof revision MUST preserve user-visible stage ordering, known diagnostics, regression counts, and statuses; temporary paths and baseline identifiers may vary only when clearly identified as run-specific.
- **FR-020**: Temporary demonstration files MUST be cleaned on success, unexpected failure, and interruption unless retention was explicitly requested.
- **FR-021**: The demonstration MUST NOT leave an active child process after it finishes or is interrupted.
- **FR-022**: The project MUST provide an explicit retention option that preserves the generated repository and displays its location for inspection.
- **FR-023**: Public documentation MUST concisely state prerequisites, the one-command workflow, the expected status-1 failure and status-0 recovery, default cleanup, retention, inspection, and manual cleanup behavior.
- **FR-024**: Automated tests MUST execute the complete demonstration and verify stage order, expected source and target, exact regression count, broken and repaired statuses, shared baseline behavior, final explanation, isolation, and cleanup.
- **FR-025**: Automated tests MUST cover failure handling for unexpected statuses or diagnostics and MUST prove that such failures are observable and nonzero.
- **FR-026**: All 285 existing automated tests MUST remain passing after the demo tests are added.
- **FR-027**: Existing analysis selection, comparison semantics, output formats, and exit codes for `check`, `explain`, `diff`, and `diff --ci` MUST remain unchanged.
- **FR-028**: Public demo assets MUST remain separate from production analysis behavior and from the release-validation artifact fixtures.
- **FR-029**: The baseline demonstration content MUST remain minimal and MUST NOT require package installation for another ecosystem, external services, an LLM, hosted-service APIs, containers, or network access.
- **FR-030**: The feature MUST NOT add new instruction contract types, demonstrate package-script or multiple simultaneous regressions, publish a separate demo repository, require a production package release, add graphical or hosted integrations, benchmark large repositories, record media automatically, or add platform-specific guarantees beyond supported Linux.

### Key Entities

- **Demo Run**: One complete presentation workflow, including its isolated location, immutable baseline identity, three ordered stages, captured outcomes, cleanup choice, and final result.
- **Demo Repository**: The minimal isolated repository used to demonstrate the baseline, source refactor, stale instruction, and coordinated repair without affecting the parent project.
- **Demo Baseline**: The immutable repository revision shared by both broken and repaired comparisons.
- **Instruction Claim**: The single path reference whose evidence is present at baseline, missing after the refactor, and updated during repair.
- **Stage Result**: The user-visible label, command or change, diagnostic output, regression count, and status associated with one demonstration stage.
- **Retention Choice**: The user's explicit decision to preserve the generated repository instead of applying default cleanup.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user who has completed documented local setup can run the full demonstration with one command and reach the final success explanation without reading project source code.
- **SC-002**: In 100% of successful runs, the baseline, broken-refactor, and repaired-instruction stages appear in the documented order.
- **SC-003**: In 100% of runs, the broken stage reports exactly one expected `PathExists` regression with status 1 and the repaired stage reports zero regressions with status 0.
- **SC-004**: In 100% of runs, both comparisons use the same immutable baseline and the repaired pass is attributable to updating the instruction claim to the moved path.
- **SC-005**: The complete demonstration finishes within 30 seconds in the supported Linux environment after dependencies are available.
- **SC-006**: Three consecutive runs from the same project revision produce equivalent product-relevant stage order, diagnostics, regression counts, and statuses, excluding clearly identified run-specific paths or baseline identifiers.
- **SC-007**: Successful, failed, and interrupted default runs leave zero demo-created files in the parent repository, no unretained temporary repository, and no active demo process.
- **SC-008**: In retention mode, 100% of runs display an inspectable repository location containing the identifiable baseline and final repaired instruction state.
- **SC-009**: Automated checks detect any change to the expected instruction source, old target, regression count, stage order, broken status, repaired status, shared baseline, isolation, or cleanup behavior.
- **SC-010**: All 285 pre-existing tests and all new public-demo tests pass without observable changes to existing InstrProof command behavior.
- **SC-011**: A reviewer can determine from the final output alone what changed, why CI failed, what was repaired, and why CI then passed.

## Assumptions

- Users run the demo only after completing the project's documented local development setup, so the local InstrProof command and its development dependencies are already available.
- Git and the supported Linux command-line environment are available locally.
- The demo uses one known instruction source, one old source path, and one new source path consistently across documentation and automated checks.
- A real local Git commit is the default immutable baseline; a tag is not required if the commit identifier is displayed and reused.
- The demonstration repository's "otherwise usable" state means the moved source file remains present at its new path and no unrelated failure is introduced; executing the source file is not required to prove application behavior.
- Default runs prioritize automatic cleanup. Retention is an explicit opt-in and makes the user responsible for later manual deletion.
- Run-specific temporary paths and commit identifiers may be shown, but automated repeatability comparisons ignore only those documented values.
- Production package publication, network access after setup, and changes to release-validation fixtures are not dependencies of this feature.
