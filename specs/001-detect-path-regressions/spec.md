# Feature Specification: Detect Path Regressions

**Feature Branch**: `main`

**Created**: 2026-08-21

**Status**: Draft

**Input**: User description: "Build the first end-to-end capability of InstrProof: detect when a repository change breaks a path referenced by an unchanged AI coding instruction."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect Broken Instruction Paths (Priority: P1)

As a repository maintainer, I want to compare a proposed repository state with a base revision so that I learn when an unchanged AI coding instruction now points to a missing repository target.

**Why this priority**: This is the core protection InstrProof provides: preventing repository changes from silently making coding instructions stale.

**Independent Test**: Create a base revision containing an instruction that references an existing file, remove or rename only that file in the compared revision, run `instrproof diff --base <base-ref>`, and verify that a new regression is reported.

**Acceptance Scenarios**:

1. **Given** an inline repository path is referenced by an instruction and exists in BASE, **When** the same instruction claim remains in HEAD but the target is absent, **Then** the comparison reports a `PathExists` regression identifying the instruction source and target.
2. **Given** a local Markdown link is referenced by an instruction and resolves to an existing target in BASE, **When** the same instruction claim remains in HEAD but the target is absent, **Then** the comparison reports a `PathExists` regression.
3. **Given** a monitored instruction target exists in both BASE and HEAD, **When** the comparison runs, **Then** no regression is reported for that contract.

---

### User Story 2 - Avoid Stale-Claim False Positives (Priority: P2)

As a repository maintainer, I want InstrProof to recognize instruction edits and removals so that intentional documentation updates are not reported as regressions.

**Why this priority**: A useful regression check must distinguish an actual broken claim from a claim that was deliberately changed or removed.

**Independent Test**: Rename a referenced target while updating the instruction to the new path, and separately remove the instruction, then verify each comparison reports no regression for the old contract.

**Acceptance Scenarios**:

1. **Given** an instruction references a target that exists in BASE, **When** the target is renamed and the instruction is updated in HEAD to reference the new existing target, **Then** the old contract is not reported as a regression.
2. **Given** an instruction references a target that exists in BASE, **When** that instruction claim is removed in HEAD, **Then** its contract is not reported as a regression.
3. **Given** a monitored claim remains but its line number or surrounding prose changes, **When** its normalized target and instruction source remain the same, **Then** it remains identifiable as the same contract.

---

### User Story 3 - Monitor Only Validated Paths (Priority: P3)

As a repository maintainer, I want only high-confidence path references monitored so that ordinary path-like prose does not create noisy results.

**Why this priority**: Precision is required for maintainers to trust and act on the command's output.

**Independent Test**: Include both resolvable and unresolvable inline paths and Markdown links in root and nested instruction documents, then verify only targets that exist in BASE become contracts and that links use their containing document as the resolution location.

**Acceptance Scenarios**:

1. **Given** path-like text whose resolved target does not exist in BASE, **When** contracts are identified, **Then** that text does not become a monitored contract.
2. **Given** an inline repository path in an instruction document, **When** its target is resolved, **Then** it is interpreted relative to the repository root.
3. **Given** a local Markdown link in a nested instruction document, **When** its target is resolved, **Then** it is interpreted relative to the directory containing that instruction document.
4. **Given** prose that is not an explicit supported path form, **When** the instruction is inspected, **Then** no contract is inferred from that prose.

### Edge Cases

- A target exists in BASE but is replaced in HEAD by a directory or file at the same normalized path; the path-existence contract remains satisfied because this feature asserts existence, not target kind or content.
- Multiple occurrences in one instruction source that normalize to the same target represent the same contract identity and must not create duplicate regressions.
- A relative Markdown link containing `.` or `..` segments is normalized after resolving it from the containing instruction document.
- A reference that would resolve outside the repository is not a repository target and must not become a contract.
- An external, absolute, fragment-only, or non-local Markdown destination is not a supported local Markdown path and must not become a contract.
- A supported instruction document present only in HEAD may yield current claims, but cannot create a new regression relative to BASE because its targets were not validated in BASE.
- If BASE cannot be resolved or inspected, the command must fail clearly rather than claim that no regressions exist.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an `instrproof diff --base <base-ref>` workflow that compares the named BASE repository state with HEAD.
- **FR-002**: The system MUST inspect `AGENTS.md` and `CLAUDE.md` instruction documents located within the repository in BASE and HEAD.
- **FR-003**: The system MUST recognize explicit inline repository-relative paths, such as `src/auth/service.ts`, as candidate path claims.
- **FR-004**: The system MUST recognize local Markdown link destinations, such as the destination in `[API](api.md)`, as candidate path claims.
- **FR-005**: The system MUST resolve inline repository paths relative to the repository root.
- **FR-006**: The system MUST resolve local Markdown link destinations relative to the directory containing the instruction document.
- **FR-007**: The system MUST normalize resolved repository targets so equivalent path spellings yield the same target identity.
- **FR-008**: The system MUST reject candidate references that resolve outside the repository.
- **FR-009**: A candidate path claim MUST become a monitored `PathExists` contract only when its resolved target exists in BASE.
- **FR-010**: Path-like text whose resolved target does not exist in BASE MUST NOT become a monitored contract.
- **FR-011**: The system MUST prioritize precision by limiting detection to the two supported explicit path forms and MUST NOT infer paths from arbitrary natural-language references.
- **FR-012**: Each contract MUST be identified by instruction source, contract type, and normalized target.
- **FR-013**: Contract identity MUST NOT depend on line number, surrounding prose, or the path claim's occurrence position.
- **FR-014**: When the same contract claim remains in HEAD and its target no longer exists in HEAD, the system MUST report it as a new regression.
- **FR-015**: When a BASE contract's claim is changed in HEAD to a different target, the system MUST NOT report the old contract as a regression.
- **FR-016**: When a BASE contract's claim is removed from HEAD, the system MUST NOT report that contract as a regression.
- **FR-017**: When a BASE contract's target continues to exist in HEAD, the system MUST consider that contract passing.
- **FR-018**: The comparison result MUST clearly state whether new instruction contract regressions exist.
- **FR-019**: Each reported regression MUST identify at least the instruction source, contract type, and normalized missing target so a maintainer can locate and understand it.
- **FR-020**: The command MUST return a distinguishable unsuccessful outcome when one or more new regressions exist and a successful outcome when comparison completes with none, enabling automated change checks.
- **FR-021**: The command MUST report an explicit failure when the requested BASE state or either repository state cannot be inspected; such failure MUST NOT be represented as a passing comparison.
- **FR-022**: The feature MUST NOT validate package scripts, provide `instrproof check` or `instrproof explain`, generate rename or replacement hints, analyze semantic instruction quality or contradictions, use language-model analysis, rewrite instructions, model agent-specific loading semantics, or perform monorepo package resolution.

### Key Entities

- **Instruction Source**: A supported AI coding instruction document, identified by its normalized repository-relative location.
- **Path Claim**: An explicit supported reference found in an instruction source, including its form, written target, and resolved normalized repository target.
- **PathExists Contract**: A BASE-validated assertion that a normalized repository target exists, identified by instruction source, contract type, and normalized target.
- **Comparison Result**: The outcome of comparing BASE contracts with HEAD claims and targets, including passing contracts, new regressions, and inspection failures.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All seven specified demonstration cases produce the expected pass, regression, identity, or not-monitored outcome in repeatable acceptance testing.
- **SC-002**: 100% of reported path regressions correspond to a target that existed in BASE, is absent in HEAD, and is still claimed by the same instruction source in HEAD across the required acceptance corpus.
- **SC-003**: 100% of supported references that resolve to nonexistent BASE targets are excluded from monitoring across the required acceptance corpus.
- **SC-004**: Contract identity remains unchanged in 100% of tests that alter only line numbers or surrounding prose while preserving instruction source, contract type, and normalized target.
- **SC-005**: Maintainers can run one documented command and determine from its displayed result and completion status whether the change introduces instruction path regressions.
- **SC-006**: A repository comparison containing up to 100 supported instruction documents and 1,000 candidate path references completes within 5 seconds under normal local operating conditions.

## Assumptions

- BASE and HEAD refer to inspectable states of the same repository, and HEAD means the repository state being evaluated by the command.
- Repository target existence is the only property asserted by `PathExists`; content, target type, and semantic suitability are outside this feature.
- Instruction sources are selected by the supported filenames `AGENTS.md` and `CLAUDE.md` anywhere in the repository; agent-specific precedence, scope, and loading behavior are intentionally ignored.
- Equivalent paths are compared after lexical normalization relative to their required resolution location.
- Local Markdown links refer to repository-local filesystem destinations; external URLs, absolute destinations, and fragment-only destinations are excluded.
- The user running the workflow has permission to read the repository and the requested BASE state.

