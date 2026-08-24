# Feature Specification: Harden Path and Instruction Discovery

**Feature Branch**: `[008-human-path-discovery]`

**Created**: 2026-08-24

**Status**: Draft

**Input**: User description: "Harden existing `PathExists` extraction for inline repository-root files and make diff instruction discovery use independent BASE and working-tree configurations without adding contract types or changing compatibility behavior."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Protect Referenced Root Files (Priority: P1)

A repository maintainer can name an existing root-level file in inline code within an instruction and have its continued existence protected by the existing path contract.

**Why this priority**: Root files such as project readmes, manifests, and build files are common instruction dependencies, yet these claims currently receive no protection.

**Independent Test**: Establish a baseline containing a supported root file and an instruction that references it in inline code, delete the file while retaining the claim, and verify the comparison reports exactly one `PathExists` regression.

**Acceptance Scenarios**:

1. **Given** BASE contains `README.md` and an instruction says ``Read `README.md`.`` outside fenced code, **When** baseline contracts are selected, **Then** one `PathExists(README.md)` contract is established.
2. **Given** that baseline contract and a surviving unchanged claim, **When** HEAD deletes `README.md`, **Then** comparison reports one confirmed path regression.
3. **Given** BASE contains `Makefile` and an instruction references ``Makefile`` in inline code, **When** baseline contracts are selected, **Then** the existing path contract protects `Makefile`.
4. **Given** BASE lacks `output.json` and an instruction says ``Write `output.json`.`` **When** baseline contracts are selected, **Then** no contract is established for `output.json`.
5. **Given** a supported spelling whose case differs from the only BASE path, **When** baseline contracts are selected, **Then** the differently cased candidate is not promoted.

---

### User Story 2 - Reject Ambiguous Inline Text (Priority: P1)

A maintainer can continue using inline code for commands, versions, placeholders, URLs, globs, and ordinary tokens without creating false path obligations.

**Why this priority**: Expanding root-file recognition is useful only if InstrProof preserves its high-precision, evidence-based selection policy.

**Independent Test**: Analyze instructions containing each supported and rejected root-level form against a repository containing tempting similarly named entries, and verify only exact, supported, existing file references become contracts.

**Acceptance Scenarios**:

1. **Given** inline tokens `pytest`, `src`, `main`, `build`, and `v1.0`, **When** instructions are analyzed, **Then** none becomes a root-level path candidate even if a matching repository entry exists.
2. **Given** an inline URL, URL fragment, query, glob, placeholder, shell expression, absolute path, whitespace-containing value, backslash-containing value, or NUL-containing value, **When** instructions are analyzed, **Then** none becomes a root-level path candidate.
3. **Given** a file-like token appears only inside fenced code, **When** instructions are analyzed, **Then** it does not become an inline-code path contract.
4. **Given** a one-segment extension-bearing basename or an explicitly supported common extensionless filename exists exactly in BASE, **When** it appears in inline code, **Then** it is eligible for evidence-based promotion.

---

### User Story 3 - Preserve Baseline Discovery Rules (Priority: P1)

A reviewer comparing BASE with the working tree receives regressions derived from the rules that actually governed BASE, even when the working-tree configuration removes or changes those rules.

**Why this priority**: Applying the current configuration retroactively lets a pull request erase baseline monitoring and hide a stale instruction.

**Independent Test**: Configure BASE to discover a custom instruction source, remove that rule in HEAD while retaining the source and stale claim, delete its referenced evidence, and verify comparison still reports the regression.

**Acceptance Scenarios**:

1. **Given** BASE configuration selects `docs/ai-rules.md`, **When** HEAD removes the rule but retains the file and stale claim while deleting referenced evidence, **Then** the surviving claim produces a regression.
2. **Given** the same BASE selection, **When** HEAD removes the rule and repairs the claim to a valid new target, **Then** the old contract is retired under coordinated-update behavior and no regression is reported for it.
3. **Given** the same BASE selection, **When** HEAD removes both the rule and instruction file, **Then** existing instruction-removal behavior is preserved.
4. **Given** HEAD adds a custom rule for a source BASE did not select, **When** comparison runs, **Then** that source creates no retroactive BASE contract.
5. **Given** BASE has configuration that HEAD deletes, **When** comparison runs, **Then** BASE discovery still uses the BASE configuration.

---

### User Story 4 - Retain Compatible and Deterministic Analysis (Priority: P2)

Existing users receive the same default discovery, coordinated-update results, diagnostics, formats, ordering, and statuses while gaining the two correctness fixes.

**Why this priority**: The feature hardens established behavior and must not expand the public contract or destabilize automated use.

**Independent Test**: Run existing and focused comparison suites repeatedly across default, overlapping-rule, malformed-config, coordinated-update, and command-output fixtures and verify unchanged compatible results.

**Acceptance Scenarios**:

1. **Given** root or nested `AGENTS.md` and `CLAUDE.md` files, **When** any applicable analysis runs, **Then** existing default discovery remains unchanged regardless of custom rules.
2. **Given** BASE and HEAD rules overlap on the same physical source, **When** each state is analyzed, **Then** that source is analyzed once per state and results remain deterministically ordered.
3. **Given** malformed BASE or working-tree configuration, **When** diff analysis runs, **Then** it ends as an analysis error with status 2.
4. **Given** check or explain analysis, **When** it runs, **Then** it uses only working-tree configuration as before.
5. **Given** unchanged existing scenarios, **When** check, explain, diff, or CI-formatted diff runs, **Then** formatting, diagnostics, ordering, contract identity, and exit-code meanings remain unchanged.

### Edge Cases

- A dotfile with a final extension, such as `.pre-commit-config.yaml`, exists at the repository root.
- A supported common extensionless filename is present with different case, such as `makefile` instead of `Makefile`.
- A token resembles a version (`v1.0`) or command but also happens to name an existing root entry.
- A filename-like candidate contains multiple dots, a leading dot, whitespace, slash, backslash, NUL, URL syntax, query syntax, fragment syntax, glob syntax, placeholder syntax, or shell-expansion syntax.
- A root-level candidate names a directory rather than a file-like repository path.
- BASE has no configuration while HEAD adds one, or BASE has configuration that HEAD deletes.
- A BASE-discovered custom source survives as a readable HEAD file but is no longer selected by any HEAD rule.
- A BASE-discovered source survives but its claim is removed, changed, duplicated, or repaired.
- Default and custom discovery rules, or multiple custom rules, select the same normalized repository-relative source path.
- BASE or HEAD configuration exists but is malformed or unreadable.
- Working-tree sources include tracked modifications and non-ignored untracked files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Inline-code path extraction MUST recognize eligible one-segment repository-root file references without requiring `/`.
- **FR-002**: A root-level inline candidate MUST contain exactly one repository path segment, contain neither `/` nor `\`, whitespace, or NUL, and be repository-relative.
- **FR-003**: Absolute paths, URLs, URL fragments, queries, globs, placeholders, shell expressions, and occurrences inside fenced code MUST NOT qualify as root-level inline candidates.
- **FR-004**: A root-level inline candidate MUST be either:
  1. a basename containing a final filename extension whose first character is an ASCII letter (`A-Z` or `a-z`); or
  2. exactly one of `Makefile`, `Dockerfile`, `Containerfile`, `Justfile`, `Procfile`, `LICENSE`, or `NOTICE`.
- **FR-005**: Root-level candidate matching and evidence lookup MUST be case-sensitive.
- **FR-006**: Arbitrary single-word directories and extensionless names outside the explicit common-file set MUST NOT qualify, including `src`, `pytest`, `main`, `v1.0`, and `build`.
- **FR-007**: An otherwise eligible root-level candidate MUST become a baseline contract only when its exact referenced path exists in BASE.
- **FR-008**: A missing BASE root-level candidate MUST NOT be promoted and therefore MUST NOT create a later regression.
- **FR-009**: Root-level inline references MUST use the existing `PathExists` contract type and existing contract identity without adding line number, written spelling, or discovery rule to identity.
- **FR-010**: Markdown local-link behavior, including resolution relative to the instruction source, MUST remain unchanged.
- **FR-011**: Nested inline paths, package-script extraction, and BASE evidence promotion MUST remain unchanged.
- **FR-012**: Diff analysis MUST resolve and use the exact selected BASE revision.
- **FR-013**: Diff analysis MUST read and validate BASE `instrproof.json` from BASE repository state independently of the working tree.
- **FR-014**: BASE instruction discovery MUST use BASE configuration together with all existing default instruction names.
- **FR-015**: Diff analysis MUST independently read and validate working-tree `instrproof.json` for normal HEAD discovery.
- **FR-016**: Normal HEAD instruction discovery MUST use working-tree configuration together with all existing default instruction names.
- **FR-017**: HEAD comparison MUST additionally inspect every BASE-discovered instruction source that still exists as a readable file in HEAD, even when working-tree configuration no longer selects it.
- **FR-018**: HEAD instruction sources MUST be deduplicated by normalized repository-relative path so each physical source is analyzed once in that state.
- **FR-019**: A surviving BASE claim whose required HEAD evidence is missing MUST remain a regression even if HEAD removed or changed the rule that originally discovered its source.
- **FR-020**: A source selected only by a newly added HEAD rule MUST NOT establish a retroactive BASE contract.
- **FR-021**: Removal of an instruction source and coordinated removal or update of a claim MUST retain existing passing behavior.
- **FR-022**: Malformed BASE configuration and malformed working-tree configuration MUST each produce an observable analysis error with status 2.
- **FR-023**: Check and explain operations MUST continue to inspect only current working-tree sources using only working-tree configuration.
- **FR-024**: Default discovery of all root and nested `AGENTS.md` and `CLAUDE.md` files MUST remain unchanged.
- **FR-025**: Working-tree analysis MUST retain inclusion of tracked modifications and non-ignored untracked files.
- **FR-026**: Contract selection, source deduplication, and reported results MUST remain deterministically sorted and repeatable.
- **FR-027**: Existing output formats, ordering, diagnostics, and exit-code meanings MUST remain unchanged: 0 for completed analysis without regressions, 1 for confirmed regression, and 2 for analysis error.
- **FR-028**: Focused automated coverage MUST verify all supported root-level extension-bearing and common extensionless forms, case sensitivity, missing BASE evidence, deletion regression, coordinated claim update, and rejection of every defined ambiguous or unsupported form.
- **FR-029**: Focused automated coverage MUST verify independent BASE and HEAD parsing, rule removal with stale and repaired claims, HEAD-only rules, BASE-only configuration, malformed configurations, overlapping-rule deduplication, and unchanged defaults.
- **FR-030**: End-to-end coverage MUST prove root-file deletion with a retained claim yields exactly one `PathExists` regression, removed HEAD discovery cannot hide a stale surviving source, and coordinated instruction updates continue to pass.
- **FR-031**: All existing automated checks and the public demo and release-validation workflows MUST continue to pass unchanged on every supported runtime version.
- **FR-032**: The feature MUST NOT add contract types, arbitrary root directories or extensionless filenames, semantic or model-based extraction, automatic rewriting or repair, replacement hints, agent-specific instruction semantics, monorepo package-script resolution, dependency or version contracts, new machine-readable output, hosted annotations, or publication/demo changes.

### Key Entities

- **Root-Level Inline Candidate**: A single-segment, repository-relative token found in inline code whose syntax is eligible for exact BASE evidence validation.
- **Instruction Source**: A normalized repository-relative readable file selected by default discovery, revision-specific custom rules, or BASE-source carry-forward for HEAD comparison.
- **Revision Configuration**: The independently validated instruction-discovery rules stored in BASE or in the current working tree.
- **Baseline Contract**: An existing contract established from a BASE-discovered claim only after required BASE repository evidence is present.
- **Surviving Claim**: A BASE claim that remains represented in a still-existing HEAD instruction source and is evaluated under existing identity and coordinated-update rules.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of specified supported root-level inline forms are selected when, and only when, the exact case-sensitive path exists in BASE.
- **SC-002**: 100% of specified ambiguous and unsupported root-level forms are rejected, including commands, ordinary single tokens, versions, URLs, globs, placeholders, shell expressions, and fenced-code occurrences.
- **SC-003**: In every covered comparison, removing a working-tree custom rule cannot erase a baseline contract from a still-existing BASE-discovered source with a surviving claim.
- **SC-004**: In every covered comparison, a working-tree-only rule creates zero retroactive baseline contracts from sources not selected in BASE.
- **SC-005**: Root-file deletion with a retained claim produces exactly one confirmed `PathExists` regression, while coordinated claim updates and instruction removals continue to produce no regression.
- **SC-006**: Malformed configuration in either compared state produces status 2 in 100% of covered cases; confirmed regressions produce status 1; completed non-regressing analyses produce status 0.
- **SC-007**: Three repeated analyses of each deterministic fixture produce identical contract selection, deduplication, ordering, diagnostics, output, and status.
- **SC-008**: All pre-existing and new automated checks pass on supported Python 3.12, 3.13, and 3.14 environments.
- **SC-009**: The reproducible public demonstration and release-validation workflows complete successfully without changes to their user-visible behavior.
- **SC-010**: Existing check, explain, diff, and CI-formatted diff snapshots or equivalent compatibility assertions show zero unintended formatting or diagnostic changes.

## Assumptions

- “Contains a filename extension” means a file-like basename has a non-empty name component and a non-empty suffix separated by a dot; version-like tokens and prohibited syntactic forms remain excluded even when they contain a dot.
- An extension-bearing root filename is eligible only when its final extension is non-empty and begins with an ASCII letter. Therefore `README.md`, `Cargo.toml`, and `archive.tar.gz` are eligible forms, while `file.1`, `v1.0`, and `python3.12` are not.
- Exact BASE evidence uses the repository's existing path-existence semantics and does not infer renames, alternatives, or case-insensitive matches.
- A BASE-discovered source carried into HEAD analysis participates only in comparison of BASE-established claims; its former discovery rule does not become part of contract identity.
- Existing coordinated-update and instruction-removal semantics determine whether a BASE claim survives; this feature does not redefine those semantics.
- Configuration validation uses the same accepted configuration format and diagnostic conventions already exposed by InstrProof.
- Supported runtime versions, default instruction names, ignored-file rules, and current CLI surfaces remain those already established by the project.
