# Feature Specification: Package Script Contracts

**Feature Branch**: `main`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Extend InstrProof with a second repository-grounded contract type, `PackageScriptExists`, while preserving the existing PathExists regression workflow and using the same `instrproof diff --base <base-ref>` analysis."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detect Broken Package-Script Instructions (Priority: P1)

As a repository maintainer, I want InstrProof to detect when an unchanged AI coding instruction still tells an agent to run a package script that a repository change removed or renamed, so that stale operational guidance is caught before it is merged.

**Why this priority**: This is the core new protection: a previously valid, still-present instruction must not silently point to a missing package script.

**Independent Test**: Create a BASE state whose root package manifest defines a script referenced by a supported command in an instruction, remove or rename only that script in HEAD, run `instrproof diff --base <base-ref>`, and verify that a `PackageScriptExists` regression is reported.

**Acceptance Scenarios**:

1. **Given** a supported instruction command references a script that exists in the BASE root package manifest, **When** the same claim remains in HEAD and the script still exists, **Then** the contract passes.
2. **Given** a supported instruction command references a script that exists in the BASE root package manifest, **When** the same claim remains in HEAD and the script is removed, **Then** a `PackageScriptExists` regression is reported.
3. **Given** a supported instruction command references a script that exists in the BASE root package manifest, **When** the script is renamed in the manifest but the instruction remains unchanged, **Then** a `PackageScriptExists` regression is reported for the old script name.

---

### User Story 2 - Respect Intentional Instruction Changes (Priority: P2)

As a repository maintainer, I want instruction edits and removals to retire old package-script contracts so that coordinated changes do not produce false regressions.

**Why this priority**: Maintainers need to rename scripts and update or remove instructions without being warned about claims that no longer exist.

**Independent Test**: Rename a BASE script while updating its instruction to the new script name in HEAD, and separately remove the instruction claim, then verify neither comparison reports the old contract as a regression.

**Acceptance Scenarios**:

1. **Given** a monitored instruction references a BASE script, **When** the script is renamed and that instruction source is updated to reference the new script in the same change, **Then** the old contract is not reported as a regression.
2. **Given** a monitored instruction references a BASE script, **When** the package-script claim is removed from the instruction, **Then** the old contract is not reported as a regression.
3. **Given** a monitored package-script claim, **When** only its line number or surrounding prose changes while its instruction source and normalized script name remain unchanged, **Then** it remains the same contract.

---

### User Story 3 - Monitor Only High-Confidence Script Commands (Priority: P3)

As a repository maintainer, I want only clearly identifiable package-manager commands with BASE-validated scripts monitored so that ordinary prose and already-invalid instructions do not create noisy findings.

**Why this priority**: Precision is essential for maintainers to trust the additional contract type.

**Independent Test**: Place supported npm, pnpm, and yarn commands alongside ambiguous text and commands for scripts absent from the BASE root package manifest, then verify only clear commands naming existing BASE scripts become contracts.

**Acceptance Scenarios**:

1. **Given** an instruction contains `npm run typecheck`, `pnpm typecheck`, `pnpm run typecheck`, `yarn typecheck`, or `yarn run typecheck`, **When** `typecheck` exists as a script in the BASE root package manifest, **Then** the candidate becomes `PackageScriptExists(typecheck)`.
2. **Given** a clear supported command references a script absent from the BASE root package manifest, **When** BASE contracts are established, **Then** the candidate is not monitored.
3. **Given** text that does not clearly form a supported npm, pnpm, or yarn package-script command, **When** instructions are inspected, **Then** no package-script candidate is promoted from that text.
4. **Given** a script exists only in a nested or workspace package manifest, **When** BASE contracts are established, **Then** that nested definition does not satisfy the candidate.

---

### User Story 4 - Evaluate Mixed Contracts Together (Priority: P4)

As a repository maintainer, I want path and package-script contracts evaluated by the same comparison command so that one result covers all supported instruction regressions.

**Why this priority**: The new protection must extend the established workflow without fragmenting analysis or disrupting existing behavior.

**Independent Test**: Create one comparison containing multiple `PathExists` and `PackageScriptExists` contracts with both passing and failing targets, run one diff command, and verify every contract is evaluated according to its type in the combined result.

**Acceptance Scenarios**:

1. **Given** instruction sources contain multiple valid path and package-script claims in BASE, **When** one or more claimed targets are missing in HEAD while their claims survive, **Then** one diff operation reports all and only the resulting regressions.
2. **Given** an existing PathExists acceptance case, **When** package-script support is present, **Then** its established outcome remains unchanged.

### Edge Cases

- Multiple occurrences in one instruction source that reference the same normalized script name represent one contract identity and must not create duplicate regressions.
- Identical script names referenced from different instruction sources represent distinct contracts because instruction source is part of identity.
- A package-script command found only in HEAD cannot create a regression relative to BASE because it was not a BASE-validated contract.
- A root package manifest without a `scripts` collection, or without the named script, does not validate a package-script candidate.
- Definitions in nested or workspace package manifests are ignored even when their script names match an instruction claim.
- Package-manager text embedded in ambiguous prose, unsupported command forms, or commands whose script name cannot be identified precisely is not promoted to a candidate.
- Additional command arguments or shell syntax must not be semantically interpreted to infer alternative scripts or command-body equivalence.
- A manifest script whose command body changes while its script name remains present continues to satisfy the contract.
- Failure to inspect the BASE or HEAD root package manifest must remain distinguishable from a successful comparison with no regressions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The existing `instrproof diff --base <base-ref>` workflow MUST evaluate `PackageScriptExists` contracts together with `PathExists` contracts in one comparison and one result.
- **FR-002**: Existing instruction discovery, BASE contract establishment, contract-survival comparison, regression detection, and output behavior MUST apply to both contract types rather than creating a separate user workflow.
- **FR-003**: Existing `PathExists` candidate recognition, validation, identity, survival, and regression outcomes MUST remain unchanged.
- **FR-004**: The system MUST recognize only clear package-script execution commands using npm, pnpm, or yarn as package-script candidates.
- **FR-005**: Supported npm commands MUST include the explicit `npm run <script-name>` form.
- **FR-006**: Supported pnpm commands MUST include both `pnpm <script-name>` and `pnpm run <script-name>` forms.
- **FR-007**: Supported yarn commands MUST include both `yarn <script-name>` and `yarn run <script-name>` forms.
- **FR-008**: The system MUST extract the explicitly named script from a supported command and normalize it to the target used by `PackageScriptExists(<script-name>)`.
- **FR-009**: The system MUST prioritize precision over recall and MUST NOT promote ambiguous package-manager prose, unsupported command forms, or text without a clearly identifiable script name.
- **FR-010**: Package-script evidence MUST be resolved exclusively against the repository root package manifest in each repository state.
- **FR-011**: Nested, workspace-specific, and monorepo package manifests MUST NOT be used to validate package-script candidates.
- **FR-012**: A package-script candidate MUST become a BASE contract only when the extracted script name exists under the BASE root package manifest's scripts collection.
- **FR-013**: A package-script candidate whose script name does not exist in the BASE root package manifest MUST NOT become a monitored contract.
- **FR-014**: Each package-script contract MUST be identified by instruction source, contract type, and normalized script-name target.
- **FR-015**: Package-script contract identity MUST NOT depend on line number, surrounding prose, or occurrence position.
- **FR-016**: When the same package-script claim remains in HEAD and its named script no longer exists in the HEAD root package manifest, the system MUST report a `PackageScriptExists` regression.
- **FR-017**: When a BASE package-script claim is changed in the same instruction source to reference another script in HEAD, the system MUST NOT report the old contract as a regression.
- **FR-018**: When a BASE package-script claim is removed from HEAD, the system MUST NOT report that contract as a regression.
- **FR-019**: When a monitored script name still exists in the HEAD root package manifest, the system MUST consider the contract passing regardless of changes to the script command body.
- **FR-020**: The system MUST NOT infer that a renamed script is a replacement for an old script unless the instruction claim itself is updated; an unchanged old claim therefore regresses when the old name disappears.
- **FR-021**: Each reported package-script regression MUST identify at least the instruction source, `PackageScriptExists` contract type, and normalized missing script name.
- **FR-022**: A combined comparison MUST evaluate multiple path and package-script contracts without one contract type suppressing, replacing, or changing the results of the other.
- **FR-023**: This feature MUST NOT add workspace or nested package resolution, package dependency or version validation, arbitrary manifest-key validation, semantic shell interpretation, script command-body equivalence, replacement hints, custom instruction-file configuration, `instrproof check`, `instrproof explain`, CI-specific output enhancements, or language-model analysis.
- **FR-024**: Regression diagnostics MUST report the instruction source, source location when available, contract type, normalized target, BASE evidence state, and HEAD evidence state.
- **FR-025**: Source-location and evidence-state metadata MUST be diagnostic-only and MUST NOT participate in contract identity. Contract identity MUST remain based on instruction source, contract type, and normalized target.
- **FR-026**: Package-script candidate extraction MUST use a deterministic and explicitly defined supported command grammar.
- **FR-027**: Ambiguous package-manager commands MUST NOT be promoted to package-script candidates.


### Key Entities

- **Package-Script Claim**: A clear supported npm, pnpm, or yarn command found in an instruction source, including its package manager, written command form, and normalized script-name target.
- **PackageScriptExists Contract**: A BASE-validated assertion that a named script exists in the repository root package manifest, identified by instruction source, contract type, and normalized target.
- **Root Package Manifest**: The sole package-script evidence source for a repository state; nested and workspace manifests are outside this feature.
- **Combined Comparison Result**: The outcome of evaluating surviving `PathExists` and `PackageScriptExists` contracts together, including passes, regressions, and inspection failures.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All nine required demonstration cases produce their specified pass, regression, identity, not-monitored, compatibility, or combined-evaluation outcomes in repeatable acceptance testing.
- **SC-002**: 100% of reported package-script regressions in the acceptance corpus correspond to a script that existed in the BASE root package manifest, is absent from the HEAD root package manifest, and remains claimed by the same instruction source in HEAD.
- **SC-003**: 100% of clear supported npm, pnpm, and yarn command forms naming scripts present in BASE are monitored across the acceptance corpus, while 100% of referenced scripts absent from BASE are excluded.
- **SC-004**: No ambiguous or unsupported package-manager text in the precision acceptance corpus is promoted to a package-script contract.
- **SC-005**: Contract identity remains unchanged in 100% of tests that alter only line numbers or surrounding prose while preserving instruction source, contract type, and normalized target.
- **SC-006**: 100% of the existing PathExists regression acceptance suite retains its prior outcomes after package-script contracts are added.
- **SC-007**: A maintainer can use one diff invocation to receive a complete result for a comparison containing at least one path contract and at least one package-script contract.
- **SC-008**: A comparison containing up to 100 supported instruction documents and 1,000 combined candidate references completes within 5 seconds under normal local operating conditions.

## Assumptions

- The established instruction-source discovery rules and supported instruction filenames remain authoritative and unchanged.
- Script-name normalization preserves the explicitly referenced package-manifest key while applying only the existing target-normalization conventions needed for stable identity; no synonym or rename equivalence is inferred.
- The repository root package manifest is the file named `package.json` at the repository root.
- A script exists when the extracted name is present as a key under the root manifest's `scripts` collection; its value and command semantics are outside the contract.
- BASE and HEAD are inspectable states of the same repository, with HEAD representing the state evaluated by the existing diff command.
- Existing comparison failure behavior applies when required repository-state evidence cannot be inspected.
