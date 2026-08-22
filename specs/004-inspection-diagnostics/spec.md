# Feature Specification: Inspection and Diagnostics

**Feature Branch**: `004-inspection-diagnostics`
**Created**: 2026-08-22
**Status**: Draft

**Input**: Add `instrproof check` and `instrproof explain <source-location>` so users can inspect repository-grounded instruction contracts and understand their current evidence while reusing the existing discovery, extraction, identity, and evidence-validation behavior.

## User Scenarios & Testing

### User Story 1 - Inspect Current Verified Contracts (Priority: P1)

As a repository maintainer, I want to inspect the contracts InstrProof recognizes in the current repository so that I can understand which instruction claims are currently backed by repository evidence.

**Why this priority**: Visibility into recognized contracts is the primary new capability and helps maintainers trust the existing analysis.

**Independent Test**: Place valid path and package-script claims in multiple root, nested, and configured instruction sources, run `instrproof check`, and verify that every evidence-backed contract appears with its source, type, normalized target, evidence status, and an accurate total.

**Acceptance Scenarios**:

1. **Given** a discovered instruction contains a supported path claim whose repository target exists, **When** the user runs `instrproof check`, **Then** a verified `PathExists` contract is listed with its source, normalized target, and current evidence.

2. **Given** a discovered instruction contains a supported package-script command whose root package script exists, **When** the user runs `instrproof check`, **Then** a verified `PackageScriptExists` contract is listed with its source, normalized target, and current evidence.

3. **Given** valid contracts occur in multiple root, nested, and configured instruction sources, **When** the user runs `instrproof check`, **Then** contracts from every discovered source are listed with their correct repository-relative source paths.

4. **Given** the current repository contains verified contracts, **When** inspection completes, **Then** the summary reports the exact number of distinct verified contracts.

5. **Given** an instruction contains ambiguous or unsupported text, or a candidate lacks validating repository evidence, **When** the user runs `instrproof check`, **Then** that text is not presented as a verified contract.

---

### User Story 2 - Explain a Current Instruction Occurrence (Priority: P2)

As a repository maintainer, I want to inspect a supported instruction occurrence by source location so that I can understand what repository evidence InstrProof associates with it and whether that evidence currently exists.

**Why this priority**: A focused diagnostic helps users understand why InstrProof recognizes or rejects an instruction claim without changing regression semantics.

**Independent Test**: Create supported path and package-script occurrences, run `instrproof explain <source-location>`, and verify that the explanation identifies the occurrence, normalized target, exact repository evidence, and current evidence state.

**Acceptance Scenarios**:

1. **Given** a supported `PathExists` occurrence whose target currently exists, **When** the user explains its source location, **Then** the explanation shows the instruction source, diagnostic location, type, normalized target, exact repository-path evidence, and current state as `PRESENT`.

2. **Given** a supported `PackageScriptExists` occurrence whose script currently exists, **When** the user explains its source location, **Then** the explanation shows the instruction source, diagnostic location, type, normalized target, exact package-script evidence, and current state as `PRESENT`.

3. **Given** a supported occurrence whose repository evidence is currently missing, **When** the user explains its source location, **Then** the explanation shows the supported occurrence and current state as `MISSING` without promoting it to a verified contract.

4. **Given** a requested source location does not identify a supported occurrence, **When** the user runs `explain`, **Then** InstrProof reports an explicit not-found diagnostic.

---

### User Story 3 - Preserve Existing Contract and Regression Semantics (Priority: P3)

As a repository maintainer, I want the inspection commands to describe the existing analysis without redefining it so that diagnostics remain consistent with the established regression workflow.

**Why this priority**: The new commands are trustworthy only if they reuse the same discovery, extraction, normalization, identity, and evidence rules already used by InstrProof.

**Independent Test**: Move a claim to another line without changing its source, type, or normalized target, repeat inspection and regression checks, and verify contract identity and existing `instrproof diff` behavior remain unchanged.

**Acceptance Scenarios**:

1. **Given** a contract occurrence moves to another line while its instruction source, contract type, and normalized target remain unchanged, **When** analysis runs again, **Then** its contract identity remains unchanged while its diagnostic source location reflects the new occurrence.

2. **Given** an existing `instrproof diff` acceptance case, **When** the new inspection capabilities are present, **Then** regression detection and existing command behavior remain unchanged.

3. **Given** a candidate is rejected by existing extraction rules, **When** `check` or `explain` runs, **Then** the new commands do not promote it through a separate inference path.

## Edge Cases

* When no candidates are backed by current repository evidence, `check` reports zero verified contracts.

* Repeated occurrences in one instruction source that share instruction source, contract type, and normalized target count as one verified contract.

* Identical contract types and targets in different instruction source paths remain distinct contracts.

* Nested and configured instruction sources retain their normalized repository-relative paths.

* A requested source location that matches no supported occurrence produces an explicit not-found diagnostic.

* If multiple distinct supported occurrences exist at the requested location, all matches are shown or the result explicitly reports ambiguity. No occurrence is selected silently.

* A candidate whose evidence is successfully inspected and missing is distinguishable from an analysis operation that failed.

* Repository inspection failures are reported as analysis errors rather than as evidence states.

## Requirements

### Functional Requirements

* **FR-001**: The system MUST provide `instrproof check` to inspect contracts verified against the current repository state.

* **FR-002**: `check` MUST use the existing instruction discovery rules, including root, nested, and configured instruction sources.

* **FR-003**: `check` MUST reuse the existing candidate extraction, normalization, contract establishment, and repository evidence-validation behavior for `PathExists` and `PackageScriptExists`.

* **FR-004**: For every verified contract, `check` MUST display the instruction source, contract type, normalized target, and current evidence state.

* **FR-005**: `check` MUST preserve each nested or configured instruction source's normalized repository-relative source path.

* **FR-006**: `check` MUST report the total number of distinct verified contracts according to the existing contract identity and deduplication rules.

* **FR-007**: `check` MUST present only candidates whose current repository evidence validates successfully as verified contracts.

* **FR-008**: `check` MUST NOT characterize ambiguous text, unsupported candidates, or evidence-unvalidated candidates as verified, stale, incorrect, or regressed contracts.

* **FR-009**: The system MUST provide `instrproof explain <source-location>`, where the source location combines a repository-relative instruction source path and diagnostic line number, such as `AGENTS.md:37`.

* **FR-010**: `explain` MUST locate supported candidate occurrences using the existing discovery and extraction behavior.

* **FR-011**: For every matched occurrence, `explain` MUST display the instruction source, diagnostic location, candidate contract type, normalized target, exact repository evidence being inspected, and current evidence state.

* **FR-012**: For `PathExists`, the evidence reference MUST identify the normalized repository target whose existence is inspected.

* **FR-013**: For `PackageScriptExists`, the evidence reference MUST identify the root `package.json` script entry whose existence is inspected.

* **FR-014**: Current evidence states exposed by this feature MUST be `PRESENT` or `MISSING`.

* **FR-015**: If repository evidence cannot be inspected because analysis itself fails, InstrProof MUST report an analysis error rather than introducing a third evidence state.

* **FR-016**: A candidate with `MISSING` evidence MAY be explained as a supported candidate occurrence but MUST NOT be presented by `check` as a verified contract.

* **FR-017**: Contract identity MUST remain the combination of instruction source, contract type, and normalized target. Diagnostic source locations, including line numbers, MUST NOT participate in contract identity.

* **FR-018**: Moving an otherwise unchanged instruction claim to another line MUST preserve its contract identity.

* **FR-019**: If a requested source location matches no supported occurrence, `explain` MUST report that outcome explicitly.

* **FR-020**: If a requested source location matches multiple distinct supported occurrences, `explain` MUST display all matches or explicitly report ambiguity and MUST NOT silently choose one.

* **FR-021**: `check` and `explain` MUST reuse the existing discovery, extraction, normalization, identity, and evidence-validation pipeline and MUST NOT establish parallel analysis behavior.

* **FR-022**: `instrproof diff` MUST remain the primary regression-detection mechanism, and its existing contract selection, regression semantics, output, and completion behavior MUST remain unchanged.

* **FR-023**: This feature MUST NOT provide BASE/HEAD explanation context, Git rename or replacement hints, repairs, instruction rewriting, LLM explanations, contradiction detection, agent-specific instruction semantics, CI-specific formatting, GitHub Actions integration, or monorepo package resolution.

### Key Entities

* **Verified Contract**: An existing `PathExists` or `PackageScriptExists` contract established from a high-confidence candidate whose referenced evidence exists in the inspected repository state.

* **Supported Candidate Occurrence**: A source occurrence recognized by the existing high-precision extraction rules before current evidence validation. It may have `PRESENT` or `MISSING` evidence.

* **Source Location**: A diagnostic reference combining an instruction source path and occurrence line number. It locates an occurrence but is not part of contract identity.

* **Evidence Reference**: The exact repository target inspected for a supported occurrence: a normalized path for `PathExists`, or the root package manifest's named script entry for `PackageScriptExists`.

* **Current Evidence State**: The result of successfully inspecting an evidence reference in the current repository state: `PRESENT` or `MISSING`.

* **Contract Explanation**: A current-state diagnostic view exposing a supported occurrence, its identity-related attributes, evidence reference, and current evidence state.

## Success Criteria

### Measurable Outcomes

* **SC-001**: All required acceptance scenarios produce their specified inspection, explanation, identity, or compatibility outcomes in repeatable automated or fixture-based testing.

* **SC-002**: 100% of verified contracts in the current-state acceptance corpus display the correct source, type, normalized target, and evidence state, and the summary total equals the number of distinct contract identities.

* **SC-003**: 100% of ambiguous and unsupported examples in the precision acceptance corpus are excluded from the verified-contract listing.

* **SC-004**: 100% of supported path and package-script occurrences used in explanation acceptance tests display the correct normalized target, exact evidence reference, and current evidence state.

* **SC-005**: A supported candidate whose evidence is missing can be explained as `MISSING` but never appears in `check` as a verified contract.

* **SC-006**: Contract identity remains unchanged in all tests that alter only diagnostic line location or surrounding prose while preserving instruction source, contract type, and normalized target.

* **SC-007**: Contracts from every root, nested, and configured instruction source in the acceptance corpus retain the correct normalized source path.

* **SC-008**: The complete existing `instrproof diff` acceptance suite passes without changed expected regression results or command behavior.

* **SC-009**: Inspection of a repository containing up to 100 discovered instruction documents and 1,000 combined candidate references completes within 5 seconds under normal local operating conditions.

## Assumptions

* `check` and `explain` inspect the current working repository state.

* `explain` does not receive, retain, or infer BASE/HEAD comparison context in this feature.

* Source locations refer to diagnostic occurrence line numbers produced by the existing extraction process and may change as instruction documents are edited.

* A supported candidate may be explainable even when its current evidence is missing, but only evidence-backed candidates become verified contracts.

* Repository inspection failure is an analysis failure, not an evidence state.

* Human-readable CLI output is sufficient; machine-readable and CI-specific formats are outside scope.

* Existing rules remain authoritative for instruction discovery, supported candidate syntax, path resolution, package-script scope, normalization, contract identity, and evidence validation.
