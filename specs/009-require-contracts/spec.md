# Feature Specification: Require Baseline Contracts

**Feature Branch**: `[009-require-contracts]`

**Created**: 2026-08-24

**Status**: Draft

**Input**: User description: "Add an opt-in baseline-contract requirement to InstrProof diff so CI cannot report success after checking zero instruction contracts."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reject Empty Baseline Coverage (Priority: P1)

A repository maintainer who expects InstrProof to protect instructions can require a completed comparison to contain at least one baseline instruction contract, preventing an empty analysis from appearing successful.

**Why this priority**: The feature's primary value is eliminating false confidence when configuration mistakes, unsupported claims, missing instruction sources, or absent BASE evidence result in zero selected contracts.

**Independent Test**: Run a completed zero-baseline comparison with the requirement enabled in normal and CI-formatted modes, then verify each produces only its specified actionable analysis error and exits with status `2`.

**Acceptance Scenarios**:

1. **Given** repository analysis completes and the comparison contains exactly zero baseline contracts, **When** normal diff runs with the requirement enabled, **Then** stderr is exactly `error: no baseline instruction contracts were found; verify instruction discovery, supported claim syntax, and BASE evidence`, stdout is empty, and status is `2`.
2. **Given** the same completed zero-contract comparison, **When** CI-formatted diff runs with the requirement enabled, **Then** stderr contains the specified failing InstrProof heading and analysis-error guidance, stdout is empty, and status is `2`.
3. **Given** a zero-contract requirement failure, **When** output is produced, **Then** no pass message, regression count, or partial-success output is displayed.

---

### User Story 2 - Preserve Optional and Nonempty Results (Priority: P1)

Users can continue allowing empty repositories by default, while users enabling the requirement receive unchanged comparison decisions whenever at least one baseline contract exists.

**Why this priority**: Opt-in compatibility is essential because repositories may intentionally have no supported instruction contracts, and strict coverage must not alter genuine comparison results.

**Independent Test**: Exercise zero-, one-, multiple-, duplicate-, and regression-containing comparisons with and without the option and compare all unaffected statuses, counts, formatting, and ordering to existing exact outputs.

**Acceptance Scenarios**:

1. **Given** a completed comparison with zero baseline contracts, **When** normal diff runs without the option, **Then** it retains the existing success message and status `0`.
2. **Given** the same comparison, **When** CI-formatted diff runs without the option, **Then** it reports exactly zero contracts checked, no regressions, and status `0` as before.
3. **Given** one or more baseline contracts and no regressions, **When** diff runs with the option, **Then** status `0` and all existing output remain unchanged.
4. **Given** one or more baseline contracts and at least one regression, **When** diff runs with the option, **Then** status `1` and all existing output, ordering, and counts remain unchanged.
5. **Given** duplicate claims promote to one contract identity, **When** the requirement is evaluated, **Then** the existing deduplicated baseline-contract count determines whether coverage is nonempty.

---

### User Story 3 - Retain Analysis Error Precedence (Priority: P1)

A maintainer receives the existing attributable diagnostic when repository or configuration analysis fails, rather than a misleading empty-coverage error.

**Why this priority**: The option can assess coverage only after a trustworthy comparison exists; masking the actual failure would make diagnosis harder and violate established error semantics.

**Independent Test**: Enable the option while inducing unavailable BASE, malformed BASE configuration, malformed HEAD configuration, unreadable required data, and unexpected CI analysis failures, then verify each retains its existing status and diagnostic without the zero-contract message.

**Acceptance Scenarios**:

1. **Given** the requested BASE is missing or invalid, **When** diff runs with the option, **Then** the existing BASE analysis error and status `2` are preserved.
2. **Given** BASE or HEAD configuration is malformed, **When** diff runs with the option, **Then** the existing attributable configuration error and status `2` are preserved.
3. **Given** an unexpected failure prevents comparison completion in CI mode, **When** diff runs with the option, **Then** the existing sanitized analysis error and status `2` are preserved.
4. **Given** analysis did not produce a complete comparison result, **When** the invocation fails, **Then** it does not emit the zero-contract requirement error.

---

### User Story 4 - Adopt Strict Coverage Safely in CI (Priority: P2)

A repository maintainer can discover and enable strict baseline coverage only for diff, using documented guidance that clearly states what the option does and does not guarantee.

**Why this priority**: Clear command scope and documentation let adopters strengthen CI without assuming that a nonempty result proves every natural-language instruction is protected.

**Independent Test**: Inspect command help and follow the documented consumer workflow, verifying the option appears only for diff, works in either supported diff ordering, and is rejected by check and explain.

**Acceptance Scenarios**:

1. **Given** a user requests diff help, **When** help is displayed, **Then** `--require-contracts` is documented under diff.
2. **Given** a user requests check or explain help, **When** help is displayed, **Then** the option is absent.
3. **Given** a user passes the option to check or explain, **When** arguments are parsed, **Then** the invocation is rejected under existing invalid-argument behavior.
4. **Given** a consumer copies the documented GitHub Actions command, **When** `instrproof diff --base origin/main --ci --require-contracts` runs, **Then** it enforces nonempty baseline coverage.
5. **Given** a maintainer reads the documentation, **When** deciding whether to enable the option, **Then** they learn that zero contracts remain allowed by default, strict empty coverage exits `2`, and nonempty coverage does not prove correctness or completeness of every instruction.

### Edge Cases

- Duplicate baseline claims deduplicate to exactly one promoted contract identity.
- Multiple distinct baseline contracts retain the existing exact count and deterministic output.
- A completed comparison contains zero contracts and zero regressions in normal or CI-formatted mode.
- A completed comparison contains contracts but no regressions, or contains one or many regressions.
- BASE cannot be resolved, or BASE or HEAD configuration is malformed.
- A required instruction source or repository datum is unreadable or malformed before comparison completion.
- An unexpected internal error occurs after partial analysis but before a complete comparison result exists.
- The option appears before or after other diff options in any ordering already accepted by argument parsing.
- Installed wheel and source-distribution commands receive identical arguments and repository state.
- Installed wheel and source-distribution commands encounter the same unavailable or invalid BASE and MUST produce identical analysis-error output and status `2`.
- Installed wheel and source-distribution commands analyze the same nonempty regression fixture with `--require-contracts` and MUST produce identical regression output and status `1`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The diff command MUST accept an opt-in `--require-contracts` option in normal and CI-formatted modes.
- **FR-002**: The option MUST belong only to diff; check and explain MUST reject it, and version behavior MUST remain unchanged.
- **FR-003**: Diff help MUST display the option, while check and explain help MUST NOT display it.
- **FR-004**: Existing argument orderings accepted for diff options MUST remain accepted when the new option is present.
- **FR-005**: The requirement MUST be evaluated only after repository analysis completes successfully and produces a complete comparison result.
- **FR-006**: A complete comparison with `baseline_contract_count` exactly zero and the option enabled MUST be classified as an analysis or explicit contract-requirement failure with status `2`.
- **FR-007**: In normal mode, the zero-contract requirement failure MUST write exactly `error: no baseline instruction contracts were found; verify instruction discovery, supported claim syntax, and BASE evidence` followed by a newline to stderr and MUST write nothing to stdout.
- **FR-008**: In CI-formatted mode, the zero-contract requirement failure MUST write exactly `InstrProof ✗`, a blank line, and `Analysis error: no baseline instruction contracts were found. Verify instruction discovery, supported claim syntax, and BASE evidence.` followed by a newline to stderr and MUST write nothing to stdout.
- **FR-009**: A zero-contract requirement failure MUST NOT print a pass message, regression count, or partial-success output.
- **FR-010**: Without the option, a completed zero-contract normal diff MUST retain its existing status `0` and exact success output.
- **FR-011**: Without the option, a completed zero-contract CI-formatted diff MUST retain its existing status `0` and exact output, including `0 baseline contracts checked.` and `No instruction contract regressions.`
- **FR-012**: With the option enabled, any complete comparison containing one or more baseline contracts and no regressions MUST retain existing status `0`, output, formatting, ordering, and counts.
- **FR-013**: With the option enabled, any complete comparison containing one or more baseline contracts and regressions MUST retain existing status `1`, output, formatting, ordering, and counts.
- **FR-014**: The requirement MUST use the comparison result's existing exact deduplicated promoted-contract count and MUST NOT recalculate or reinterpret coverage.
- **FR-015**: Missing or invalid BASE references, malformed BASE or HEAD configuration, unreadable instruction sources, malformed required repository data, and unexpected internal failures MUST retain their existing status `2` diagnostics and take precedence over the requirement.
- **FR-016**: No failure that prevents creation of a complete comparison result MAY emit the zero-contract requirement error.
- **FR-017**: Enabling the option MUST NOT change baseline selection, extraction, discovery, evidence validation, claim survival, contract identity, regression detection, comparison-result semantics, or deterministic ordering.
- **FR-018**: The feature MUST NOT add a contract type or change check, explain, version, default diff, or existing nonempty diff behavior.
- **FR-019**: Exit-code meanings MUST remain: `0` for an acceptable completed comparison without regressions, `1` for a completed comparison with confirmed regressions, and `2` for analysis or explicit contract-requirement failure.
- **FR-020**: Project documentation MUST explain that zero contracts are allowed by default and that enabling the option converts a completed zero-baseline comparison to status `2`.
- **FR-021**: Project documentation MUST recommend the option for CI workflows that expect at least one protected instruction contract.
- **FR-022**: The consumer GitHub Actions example MUST use `instrproof diff --base origin/main --ci --require-contracts`.
- **FR-023**: Documentation MUST clarify that the option verifies only nonempty baseline coverage, not the correctness or completeness of every natural-language instruction.
- **FR-024**: The public demonstration command and visible behavior MUST remain unchanged unless its fixture explicitly opts in without changing visible behavior.
- **FR-025**: Focused automated coverage MUST verify parsing and help scope; exact zero-contract normal and CI behavior with and without the option; unchanged one-, multiple-, duplicate-, passing-, and regressing-contract behavior; and all specified error-precedence cases.
- **FR-026**: Installed wheel and source-distribution artifacts MUST both support the option and produce identical stdout, stderr, and exit statuses for equivalent strict-mode inputs covering all four outcomes: zero-contract requirement failure with status `2`, non-regressing comparison with status `0`, confirmed regression with status `1`, and analysis error with status `2`.
- **FR-027**: All existing and new automated checks MUST pass on supported Python 3.12, 3.13, and 3.14 environments, and public-demo and release-validation workflows MUST remain successful.
- **FR-028**: The feature MUST NOT add default strict behavior, configuration-file or environment-variable controls, minimums greater than one, per-source minimums, coverage percentages, semantic instruction analysis, automatic instruction creation or rewriting, rename hints, annotations, machine-readable output, hosted services, publication changes, or a changed demonstration story.

### Key Entities

- **Completed Comparison Result**: The authoritative result produced only after BASE and HEAD analysis succeeds; it contains the existing exact baseline-contract count and established regressions.
- **Baseline Contract Count**: The existing deduplicated count of promoted BASE contracts evaluated by comparison; zero triggers the optional requirement and any positive value satisfies it.
- **Contract Requirement Failure**: An explicit status `2` outcome produced when a completed comparison has zero baseline contracts and strict coverage was requested; it is not a confirmed instruction regression.
- **Analysis Error**: An existing failure that prevents a complete comparison result and therefore takes precedence over evaluating baseline coverage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of completed zero-baseline comparisons with the option enabled exit with status `2`, emit the exact mode-specific actionable error on stderr, and emit no stdout or partial-success content.
- **SC-002**: 100% of completed zero-baseline comparisons without the option retain their existing status `0` output in normal and CI-formatted modes.
- **SC-003**: 100% of comparisons containing at least one baseline contract retain their existing decisions, output, formatting, ordering, exact counts, and statuses when the option is enabled.
- **SC-004**: 100% of covered BASE, configuration, repository-data, instruction-source, and unexpected internal analysis failures retain their existing diagnostics and status `2`, with zero occurrences of the contract-requirement message.
- **SC-005**: Duplicate claims promoted to one identity satisfy the requirement in 100% of covered cases, and repeated multiple-contract comparisons produce the same exact deduplicated count and deterministic output.
- **SC-006**: Help and parsing acceptance tests show the option on diff only, accept it in normal and CI-formatted diff invocations, and reject it for check and explain in 100% of covered cases.
- **SC-007**: The README provides one copy-and-run strict CI command and communicates all three required cautions: default empty coverage is allowed, strict empty coverage exits `2`, and nonempty coverage is not proof of instruction correctness or completeness.
- **SC-008**: Wheel and source-distribution installations produce identical statuses and user-visible output for zero-, passing-, regressing-, and analysis-error comparisons with the option.
- **SC-009**: The complete automated test suite passes on Python 3.12, 3.13, and 3.14, and the public demonstration and release-validation workflows complete successfully with no unintended visible changes.

## Assumptions

- The existing comparison result is the sole authority for the baseline-contract count and regressions; the option classifies a completed empty result but does not alter comparison semantics.
- “At least one contract” means any positive value of the existing deduplicated promoted-contract count; no contract type or instruction source receives special treatment.
- Existing argument-parser invalid-argument formatting and status behavior apply when the option is supplied to an unsupported subcommand.
- Exact output requirements use the project's established newline conventions, with one terminating newline after the final displayed line.
- Consumer CI environments make the requested BASE reference available according to existing documented checkout requirements.
- Existing packaging, supported runtimes, public demo, and release validation remain the compatibility baseline for this feature.
