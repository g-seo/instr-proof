# Feature Specification: CI Regression Checks

**Feature Branch**: `005-ci-regression-checks`

**Created**: 2026-08-23

**Status**: Draft

**Input**: User description: "Add production-ready CI behavior to InstrProof so repositories can run instruction-contract regression checks reliably in pull-request workflows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gate Pull Requests on Regressions (Priority: P1)

As a repository maintainer, I want to run the existing BASE-to-HEAD instruction-contract comparison in CI so that pull requests pass when no regressions exist and fail when one or more regressions exist.

**Why this priority**: A reliable pass-or-fail result is the core value required to use InstrProof as a required pull-request check.

**Independent Test**: Run `instrproof diff --base <base-ref> --ci` against comparisons containing zero, one, and multiple established regressions, then verify the result status and concise output without changing any regression decision made by the existing comparison.

**Acceptance Scenarios**:

1. **Given** a resolvable BASE and a completed comparison with no regressions, **When** CI mode runs, **Then** it reports success, the number of baseline contracts checked, zero regressions, and exits with status `0`.
2. **Given** one surviving `PathExists` contract whose evidence is missing in HEAD, **When** CI mode runs, **Then** it reports that regression and exits with status `1`.
3. **Given** one surviving `PackageScriptExists` contract whose evidence is missing in HEAD, **When** CI mode runs, **Then** it reports that regression and exits with status `1`.
4. **Given** multiple regressions in one comparison, **When** CI mode runs, **Then** it reports every regression and exits with status `1` rather than deriving the status from the regression count.
5. **Given** an instruction is updated or removed together with its repository change, **When** the existing regression rules determine that the old contract does not survive, **Then** CI mode reports no regression for that contract.

---

### User Story 2 - Receive Stable, Actionable Build Output (Priority: P2)

As a maintainer investigating a failed check, I want concise and deterministic diagnostics so that I can identify every broken instruction contract from build logs and receive equivalent results when rerunning the same comparison.

**Why this priority**: CI results must be understandable and stable enough for maintainers to trust, compare, and act on them.

**Independent Test**: Run the same BASE/HEAD comparison repeatedly with mixed regressions and verify equivalent output, stable ordering, complete totals, and required diagnostic fields.

**Acceptance Scenarios**:

1. **Given** a successful comparison, **When** CI output is displayed, **Then** it clearly identifies InstrProof success, the exact baseline-contract count, and zero instruction-contract regressions.
2. **Given** a comparison with regressions, **When** CI output is displayed, **Then** it clearly identifies failure, the exact regression total, and each regression's instruction source, contract type, and normalized target.
3. **Given** a regression has a diagnostic source location, **When** it is displayed, **Then** that location is included without making location part of contract identity.
4. **Given** the same repository state and BASE/HEAD pair are analyzed repeatedly, **When** CI results are displayed, **Then** regression ordering and user-visible content are equivalent across runs.

---

### User Story 3 - Distinguish Analysis Failure from Regression (Priority: P3)

As a CI operator, I want comparison failures reported separately from confirmed regressions so that infrastructure or repository-state problems are not misdiagnosed as broken instruction contracts.

**Why this priority**: A required check is only trustworthy when it distinguishes a completed negative result from an analysis that never completed.

**Independent Test**: Run CI mode with invalid and unavailable BASE references and with representative repository-analysis and internal failures, then verify each produces an actionable analysis error and status `2`, never status `1`.

**Acceptance Scenarios**:

1. **Given** the requested BASE reference is invalid or cannot be resolved locally, **When** CI mode runs, **Then** it identifies that requested reference in a concise analysis error and exits with status `2` without selecting another revision.
2. **Given** a CI-style checkout does not contain the requested BASE reference, **When** CI mode runs, **Then** it explains that the reference must be made available and exits with status `2`.
3. **Given** required repository state cannot be inspected or required repository data is malformed, **When** analysis cannot complete, **Then** CI mode reports the cause as an analysis error and exits with status `2`.
4. **Given** an unexpected internal failure prevents completion, **When** CI mode handles the result, **Then** it reports an analysis error and exits with status `2`, never status `1`.

---

### User Story 4 - Adopt CI Without Disrupting Existing Commands (Priority: P4)

As a repository maintainer, I want a minimal pull-request workflow example and unchanged interactive commands so that I can adopt CI safely without altering established local usage.

**Why this priority**: Adoption depends on clear checkout requirements and compatibility with existing `diff`, `check`, and `explain` workflows.

**Independent Test**: Follow the documented GitHub Actions example with an available `origin/main`, and run existing non-CI command acceptance suites to verify their observable behavior remains unchanged.

**Acceptance Scenarios**:

1. **Given** a pull-request workflow checkout in which `origin/main` is available, **When** the documented `instrproof diff --base origin/main --ci` step runs, **Then** statuses `0`, `1`, and `2` behave as a normal passing or failing required check.
2. **Given** the documented workflow, **When** a maintainer reads its checkout guidance, **Then** it clearly states that the requested BASE must be locally available and that InstrProof neither fetches nor guesses it.
3. **Given** the same repository scenarios used before CI mode was added, **When** `instrproof diff --base <base-ref>` runs without `--ci`, **Then** its existing output and completion behavior remain unchanged.
4. **Given** existing `instrproof check` and `instrproof explain` scenarios, **When** those commands run after this feature is added, **Then** their existing behavior remains unchanged.

### Edge Cases

- A completed comparison containing many regressions still reports every regression and exits with status `1`.
- Regressions with identical types and targets but different instruction sources remain separately reported according to existing contract identity.
- A regression without an available diagnostic location still reports its instruction source, contract type, and normalized target.
- A requested BASE name that resembles another locally available revision is not substituted, shortened, or otherwise guessed.
- A shallow or single-revision checkout is an analysis error when it does not contain the exact requested BASE reference.
- Zero baseline contracts is a successful completed comparison when analysis succeeds; output reports that zero contracts were checked and zero regressions were found.
- Errors encountered after partial analysis do not produce a partial regression result; the invocation is reported as an analysis failure with status `2`.
- Diagnostic ordering remains stable when multiple occurrences map to established distinct regressions, using only deterministic properties of the comparison result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept `--ci` on `instrproof diff --base <base-ref>`.
- **FR-002**: CI mode MUST use the same BASE/HEAD comparison result as the existing non-CI diff workflow.
- **FR-003**: Enabling CI mode MUST NOT change instruction discovery, candidate extraction, baseline contract promotion, contract identity, claim survival, evidence validation, contract selection, or regression semantics.
- **FR-004**: A completed CI comparison with zero regressions MUST exit with status `0`.
- **FR-005**: A completed CI comparison with one or more regressions MUST exit with status `1`.
- **FR-006**: The CI exit status for regressions MUST remain `1` regardless of the number of regressions.
- **FR-007**: A CI comparison that cannot complete MUST exit with status `2`.
- **FR-008**: Analysis failure MUST remain distinct from both a successful no-regression result and a completed result containing regressions.
- **FR-009**: Successful CI output MUST clearly identify success, the exact number of baseline contracts checked, and zero regressions.
- **FR-010**: Regression CI output MUST clearly identify failure and the exact total number of regressions.
- **FR-011**: Regression CI output MUST report every regression returned by the completed comparison rather than stopping after the first.
- **FR-012**: Every reported regression MUST include its instruction source, contract type, and normalized target.
- **FR-013**: Every reported regression MUST include its diagnostic location when that location is available.
- **FR-014**: CI output and regression ordering MUST be deterministic for the same repository state and BASE/HEAD pair.
- **FR-015**: CI output MUST be concise and suitable for non-interactive build logs.
- **FR-016**: When the requested BASE reference cannot be resolved exactly, CI mode MUST fail analysis with status `2` and MUST NOT compare against a guessed or substituted revision.
- **FR-017**: An unresolved BASE error MUST identify the requested reference and provide concise guidance that the reference must be available in the local checkout.
- **FR-018**: Failures to perform the repository comparison, inspect required repository state, or process required repository data MUST be reported as analysis errors with status `2`.
- **FR-019**: Unexpected internal failures that prevent completed analysis MUST be reported as analysis errors with status `2`, never as regressions.
- **FR-020**: CI mode MUST NOT automatically fetch a missing BASE reference.
- **FR-021**: Existing non-CI `instrproof diff` behavior MUST remain unchanged when `--ci` is absent.
- **FR-022**: Existing `instrproof check` and `instrproof explain` behavior MUST remain unchanged.
- **FR-023**: Existing `PathExists`, `PackageScriptExists`, and instruction-discovery behavior MUST remain unchanged.
- **FR-024**: The project documentation MUST include a minimal pull-request workflow using `instrproof diff --base origin/main --ci`.
- **FR-025**: The documented workflow MUST ensure or explain that `origin/main` is available in the checkout environment before InstrProof runs.
- **FR-026**: The documentation MUST explain that status `0` passes, while statuses `1` and `2` fail the check for different reasons.
- **FR-027**: This feature MUST NOT add hosted services, GitHub App behavior, Checks API annotations, pull-request comments, automatic fixes, instruction rewriting, rename or replacement hints, language-model analysis, semantic instruction-quality analysis, contradiction detection, monorepo package-script resolution, or additional machine-readable output formats.

### Key Entities

- **CI Comparison Result**: A presentation of the existing completed comparison containing the baseline-contract count and zero or more established regressions; it does not recalculate or reinterpret regressions.
- **CI Regression Diagnostic**: A build-log entry for one established regression containing instruction source, optional diagnostic location, contract type, and normalized target.
- **Analysis Error**: A failure that prevents a trustworthy completed comparison, including unresolved BASE references, unavailable repository state, malformed required repository data, and unexpected internal failures.
- **Requested BASE Reference**: The exact revision name supplied by the user; it must be locally resolvable and is never replaced with a guessed alternative.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All acceptance scenarios defined in User Stories 1–4 produce their specified pass, regression, analysis-error, compatibility, or unchanged-semantics outcomes in repeatable acceptance testing.
- **SC-002**: 100% of completed no-regression acceptance cases exit with status `0`, report the exact baseline-contract count, and report zero regressions.
- **SC-003**: 100% of completed regression acceptance cases exit with status `1`, including cases with one `PathExists`, one `PackageScriptExists`, and multiple mixed regressions.
- **SC-004**: 100% of regressions in each completed comparison are present in the corresponding CI output with correct source, type, normalized target, and location when available.
- **SC-005**: Repeating an unchanged BASE/HEAD comparison at least three times produces the same regression ordering and equivalent user-visible CI output on every run.
- **SC-006**: 100% of invalid BASE, unavailable BASE, repository-analysis, malformed-data, and induced internal-failure acceptance cases exit with status `2`, and none are labeled as instruction-contract regressions.
- **SC-007**: 100% of existing regression acceptance cases retain identical PASS/FAIL decisions when exercised through CI mode, including coordinated instruction updates and removals.
- **SC-008**: 100% of existing non-CI `diff`, `check`, `explain`, PathExists, PackageScriptExists, and instruction-discovery compatibility tests retain their prior observable outcomes.
- **SC-009**: A maintainer can copy the documented minimal pull-request workflow, make the requested BASE reference available, and obtain a normal required check whose three outcomes are distinguishable from its logs and status.
- **SC-010**: For an acceptance comparison containing at least 100 regressions, one CI invocation reports all 100 regressions with status `1`.

## Assumptions

- The existing regression engine is the sole authority for selecting baseline contracts and determining regressions; CI mode only presents and classifies its outcomes.
- HEAD retains the meaning established by the existing diff workflow.
- The baseline-contract count represents the distinct BASE contracts evaluated by the existing comparison.
- Human-readable build-log output is sufficient; no separate machine-readable format is required.
- GitHub Actions treats every nonzero process status as a failed step, while the displayed CI message explains whether status `1` or `2` caused the failure.
- Workflow authors are responsible for configuring checkout history or fetching the exact BASE reference before invoking InstrProof; InstrProof itself performs no network retrieval.
- Equivalent output permits environment-controlled line-ending differences but not differences in reported content or ordering for the same comparison.
