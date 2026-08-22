# Feature Specification: Discover Instruction Documents

**Feature Branch**: `main`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Extend InstrProof's instruction discovery so repository teams can monitor root and nested AGENTS.md and CLAUDE.md files, plus explicitly configured instruction files and patterns, while preserving existing contract behavior and claim-survival semantics."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover Repository Instruction Documents (Priority: P1)

As a repository maintainer, I want InstrProof to find standard instruction documents throughout my repository so that contracts in nested team and package guidance receive the same protection as contracts in root guidance.

**Why this priority**: Broader default discovery is the core user value and ensures instructions owned by different parts of a repository participate in analysis.

**Independent Test**: Create a repository containing root and nested `AGENTS.md` and `CLAUDE.md` documents, place a valid existing contract claim in each, and verify all four categories are independently analyzed.

**Acceptance Scenarios**:

1. **Given** a repository has a root `AGENTS.md`, **When** instruction discovery runs, **Then** that document is included as an instruction source.
2. **Given** a repository has a root `CLAUDE.md`, **When** instruction discovery runs, **Then** that document is included as an instruction source.
3. **Given** a repository has `AGENTS.md` documents below the repository root, **When** instruction discovery runs, **Then** every matching nested document is included as an independent instruction source.
4. **Given** a repository has `CLAUDE.md` documents below the repository root, **When** instruction discovery runs, **Then** every matching nested document is included as an independent instruction source.

---

### User Story 2 - Add Repository-Specific Instruction Sources (Priority: P2)

As a repository maintainer, I want to add specific instruction files or file patterns so that my repository's own Markdown guidance conventions participate in contract analysis.

**Why this priority**: Teams commonly store guidance outside the default filenames and need an explicit, bounded way to include it.

**Independent Test**: Configure one exact Markdown file and one pattern matching multiple Markdown files, then verify each matching file is analyzed exactly once alongside the default sources.

**Acceptance Scenarios**:

1. **Given** a repository configures `docs/agent-instructions.md`, **When** discovery runs and the file exists, **Then** it is included as an instruction source.
2. **Given** a repository configures `.claude/rules/**/*.md` and multiple files match, **When** discovery runs, **Then** every matching file is included as an independent instruction source.
3. **Given** the same file matches a default rule, an explicit file entry, or multiple patterns, **When** discovery runs, **Then** the file is analyzed only once in that repository state.
4. **Given** two different instruction documents contain identical claims, **When** contracts are established, **Then** the claims remain distinct because their instruction sources differ.

---

### User Story 3 - Resolve Claims from Their Correct Context (Priority: P3)

As a repository maintainer, I want claims in nested instruction documents resolved according to the established path rules so that valid links and paths are neither missed nor checked against the wrong location.

**Why this priority**: Nested discovery is only trustworthy when each document's claims preserve their intended resolution context.

**Independent Test**: Put both a repository-relative inline path and a local Markdown link in a nested instruction document and verify the inline path resolves from the repository root while the link resolves from its containing document.

**Acceptance Scenarios**:

1. **Given** a nested instruction document contains a repository-relative inline path, **When** the path claim is evaluated, **Then** it resolves from the repository root.
2. **Given** `packages/auth/AGENTS.md` contains `[architecture](docs/architecture.md)`, **When** the link claim is evaluated, **Then** it resolves to `packages/auth/docs/architecture.md`.
3. **Given** any discovered instruction source contains a valid PathExists or PackageScriptExists claim, **When** analysis runs, **Then** the existing extraction and evaluation behavior for that contract type applies unchanged.

---

### User Story 4 - Preserve State-Aware Regression Semantics (Priority: P4)

As a repository maintainer, I want BASE and HEAD to discover instructions independently under the same rules so that added, updated, and removed instruction documents follow the existing claim-survival behavior.

**Why this priority**: Expanded discovery must remain compatible with the established comparison model and avoid false regressions during coordinated instruction changes.

**Independent Test**: Compare BASE and HEAD states in which instruction documents are respectively unchanged, updated, removed, and newly added, and verify contracts survive or retire according to the existing identity and claim-survival rules.

**Acceptance Scenarios**:

1. **Given** an instruction claim exists in a BASE-discovered document, **When** the same identified claim remains in the corresponding HEAD-discovered document and its target regresses, **Then** the existing regression behavior applies.
2. **Given** an instruction document or its claim is removed in HEAD, **When** BASE and HEAD are compared, **Then** its old contracts do not survive and are not reported as regressions.
3. **Given** a claim is updated to a different normalized target in HEAD, **When** BASE and HEAD are compared, **Then** the old contract does not survive under the existing identity model.
4. **Given** an instruction document appears only in HEAD, **When** BASE and HEAD are compared, **Then** it does not create a regression for a contract absent from BASE.
5. **Given** existing feature 001 and 002 acceptance cases, **When** expanded instruction discovery is present, **Then** their established outcomes remain unchanged.

### Edge Cases

- A file matched by any number of default, explicit-file, and pattern rules is one instruction source and is analyzed once per repository state.
- Different source paths containing the same contract type and normalized target remain separate contract identities.
- A configured exact file that does not exist contributes no instruction source and does not prevent other sources from being analyzed.
- A configured pattern that matches no files contributes no instruction source and does not prevent other sources from being analyzed.
- Discovery results are independent of whether any coding agent would load, inherit, or prioritize a matched document.
- Nested documents at arbitrary repository depth remain eligible under the default filename rules.
- Markdown local links using parent-directory or current-directory segments are resolved relative to the containing instruction document under existing normalization rules.
- Repository-relative inline paths in nested documents do not change their resolution base to the containing directory.
- BASE and HEAD may yield different source sets because files can be added or removed, even though both states use the same discovery rules.
- An inaccessible or uninspectable repository state retains the existing explicit failure behavior rather than being treated as an empty discovery result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: By default, the system MUST discover the repository-root `AGENTS.md` as an instruction source when it exists.
- **FR-002**: By default, the system MUST discover the repository-root `CLAUDE.md` as an instruction source when it exists.
- **FR-003**: By default, the system MUST discover every nested file named `AGENTS.md` anywhere within the repository.
- **FR-004**: By default, the system MUST discover every nested file named `CLAUDE.md` anywhere within the repository.
- **FR-005**: Users MUST be able to explicitly add a repository-relative instruction file to discovery.
- **FR-006**: Users MUST be able to explicitly add a repository-relative file pattern that can match one or more instruction documents.
- **FR-007**: Every file matched by a configured additional file or pattern MUST be treated as an instruction source independently of the default filename conventions.
- **FR-008**: The system MUST analyze a discovered file at most once per repository state, even when that file matches multiple default or configured discovery rules.
- **FR-009**: Each discovered instruction document MUST be treated as an independent instruction source for candidate extraction, contract establishment, survival comparison, evaluation, and diagnostics.
- **FR-010**: Contract identity MUST continue to consist of instruction source, contract type, and normalized target.
- **FR-011**: Identical contract types and normalized targets from different instruction source paths MUST remain distinct contracts.
- **FR-012**: Existing identity behavior within one instruction source MUST remain unchanged, including deduplication of repeated occurrences whose identity components are equal.
- **FR-013**: Repository-relative inline path claims MUST continue to resolve from the repository root regardless of the containing instruction document's location.
- **FR-014**: Markdown local links MUST continue to resolve relative to the instruction document containing the link.
- **FR-015**: Relative-link resolution MUST use each nested instruction document's own location rather than the repository root or another instruction source.
- **FR-016**: Existing PathExists candidate extraction, BASE validation, normalized targets, identity, survival, evaluation, and reporting behavior MUST apply unchanged across every discovered instruction source.
- **FR-017**: Existing PackageScriptExists candidate extraction, BASE validation, normalized targets, identity, survival, evaluation, and reporting behavior MUST apply unchanged across every discovered instruction source.
- **FR-018**: BASE and HEAD MUST independently discover their instruction documents using the same default and configured discovery rules.
- **FR-019**: A BASE contract MUST survive into HEAD only according to the existing claim-survival rules after HEAD instruction discovery and analysis.
- **FR-020**: Removing an instruction document or removing or updating its claim in HEAD MUST continue to retire the old contract according to existing claim-survival semantics.
- **FR-021**: A newly discovered instruction document or claim in HEAD MUST NOT retroactively create a BASE contract or a regression relative to BASE.
- **FR-022**: Discovery MUST mean only inclusion in InstrProof's repository-contract analysis and MUST NOT depend on whether Codex, Claude, or any other coding agent would load the file.
- **FR-023**: Existing feature 001 PathExists behavior and existing feature 002 PackageScriptExists behavior MUST remain unchanged except that their established analysis applies to the expanded set of discovered instruction sources.
- **FR-024**: Discovery MUST NOT introduce agent-specific loading semantics, precedence or inheritance, contradiction detection, semantic scope interpretation, arbitrary convention-based discovery, multi-agent synchronization, instruction rewriting, language-model analysis, rename hints, `instrproof check`, `instrproof explain`, or CI-specific output enhancements.
- **FR-025**: A configured exact file or pattern that produces no match in a repository state MUST contribute no source in that state without changing the analysis of successfully discovered sources.
- **FR-026**: The source path used for contract identity and diagnostics MUST identify the discovered instruction document within the repository consistently across BASE and HEAD.

### Key Entities

- **Instruction Discovery Rule**: A default filename rule, an explicitly configured file, or an explicitly configured file pattern used to select instruction documents within a repository state.
- **Instruction Source**: One uniquely discovered instruction document participating independently in contract analysis, identified by its repository-relative source path.
- **Discovery Set**: The deduplicated collection of instruction sources found for one repository state under all active discovery rules.
- **Repository Contract**: An established PathExists or PackageScriptExists assertion identified by instruction source, contract type, and normalized target.
- **Repository State**: The independently inspected BASE or HEAD snapshot to which the same discovery rules and existing analysis semantics apply.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 13 required demonstration cases produce their specified discovery, deduplication, identity, resolution, contract, survival, or compatibility outcomes in repeatable acceptance testing.
- **SC-002**: 100% of root and nested `AGENTS.md` and `CLAUDE.md` files in the acceptance corpus are included by default, regardless of nesting depth.
- **SC-003**: 100% of existing configured additional files and files matched by configured patterns in the acceptance corpus are included in analysis.
- **SC-004**: Every physical instruction document in the acceptance corpus is analyzed exactly once per repository state even when it matches two or more discovery rules.
- **SC-005**: Identical claims from different source paths produce distinct contract identities in 100% of identity acceptance cases.
- **SC-006**: 100% of nested-document Markdown local-link cases resolve relative to the containing document, while 100% of repository-relative inline-path cases continue to resolve from the repository root.
- **SC-007**: 100% of existing PathExists and PackageScriptExists acceptance cases retain their established outcomes when repeated across root, nested, and configured instruction sources.
- **SC-008**: 100% of instruction removal, claim removal, claim update, and HEAD-only addition cases retain the existing claim-survival outcomes when BASE and HEAD discover sources independently.
- **SC-009**: The complete existing feature 001 and 002 regression suites pass without changed expected outcomes.
- **SC-010**: A repository containing up to 100 discovered instruction documents and 1,000 combined candidate references completes one comparison within 5 seconds under normal local operating conditions.

## Assumptions

- Additional instruction files and patterns are explicitly supplied through InstrProof's repository configuration; the exact configuration representation is a planning decision.
- Explicit files and patterns are repository-relative and apply identically when inspecting BASE and HEAD.
- Configured additional instruction sources are Markdown documents, consistent with the stated examples and the existing instruction-analysis domain.
- Repository-relative source paths are normalized using the project's established path conventions before deduplication and contract identity comparison.
- Default recursive discovery covers files within the inspected repository state and does not infer external, generated, ignored, inherited, or agent-specific sources beyond matching the stated rules.
- Existing handling of malformed documents, invalid claims, unavailable repository states, path normalization, and diagnostics remains authoritative unless a requirement above explicitly changes discovery participation.
