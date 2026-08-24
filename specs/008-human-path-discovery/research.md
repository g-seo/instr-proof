# Research: Harden Path and Instruction Discovery

## Root-level filename grammar

**Decision**: Preserve nested `_INLINE_PATH` and add a pure one-segment classifier. Accept only a final extension beginning with an ASCII letter or exact `Makefile`, `Dockerfile`, `Containerfile`, `Justfile`, `Procfile`, `LICENSE`, or `NOTICE`.

**Rationale**: This supports `README.md`, `Cargo.toml`, `package.json`, `pyproject.toml`, and `.pre-commit-config.yaml` while rejecting arbitrary tokens and numeric pseudo-extensions such as `v1.0` and `python3.12`. Case stays significant.

**Alternatives considered**: An arbitrary single-token regex was rejected for false positives. `Path.suffix` alone accepts numeric suffixes. Filesystem-driven reinterpretation violates lexical/evidence separation.

## Candidate validation boundary

**Decision**: Reject slash, backslash, whitespace, NUL, absolute path, URL/query/fragment, glob, placeholder, and shell-expression forms before `_resolve`; keep fenced masking first and use existing `_resolve`/`RepoPath` afterward.

**Rationale**: Syntax identifies a supported claim; exact BASE evidence alone promotes it. Existing normalization remains authoritative.

**Alternatives considered**: Filesystem access in `extract.py`, shell parsing, semantic analysis, and Markdown-link changes were rejected as boundary, precision, determinism, or compatibility violations.

## Independent configuration snapshots

**Decision**: Load BASE `instrproof.json` from the exact resolved Git tree and HEAD configuration from the working tree. Absence yields empty additional rules in that state.

**Rationale**: BASE contracts reflect historical selection; HEAD removal cannot erase it, and HEAD-only rules cannot create history.

**Alternatives considered**: Reusing HEAD for BASE, merging both configurations, and BASE-only discovery were rejected because each changes ownership or retroactivity.

## Shared parser and diagnostics

**Decision**: One internal parser accepts raw bytes and `BASE instrproof.json` or `HEAD instrproof.json`. It enforces identical UTF-8, JSON object, supported-key, string-array, and rule validation and raises labelled `RepositoryError`.

**Rationale**: One parser prevents schema drift; state labels make status-2 failures attributable without CLI changes.

**Alternatives considered**: Duplicate parsers, a dependency/new format, or unlabelled errors were rejected.

## Exact BASE access

**Decision**: Test for root config existence in the resolved tree and read its blob through Git, never checkout or mutate the working tree. Cache only by exact snapshot if needed.

**Rationale**: Resolved trees are immutable and the repository already uses object access for BASE sources.

**Alternatives considered**: Checkout/worktree mutation and reading the HEAD file after resolving BASE were rejected; ref-keyed caches are unsafe because refs move.

## Preserving BASE-discovered sources

**Decision**: Retain sorted BASE source `RepoPath` values. For comparison only, union normal HEAD discovery with readable working-tree versions of those paths, deduplicate/sort by `RepoPath`, then load/extract each once.

**Rationale**: This preserves stale claims after rule removal without adding provenance or state to identity. Set semantics prevent overlapping-rule reads.

**Alternatives considered**: Identity changes, reusing BASE content as HEAD, and an alternate comparison engine were rejected as incompatible or unnecessary.

## Source lifecycle

**Decision**:

- Removed HEAD rule + surviving unchanged claim + missing evidence: regression.
- Removed rule + repaired/removed claim: existing coordinated-update PASS.
- Deleted instruction source: existing instruction-removal PASS.
- HEAD-only rule: no baseline contract.
- Malformed BASE or HEAD config: labelled analysis error, status 2.

**Rationale**: These outcomes follow existing identity and survival rules once correct state source sets are supplied.

**Alternatives considered**: Treating rule removal as claim removal, source deletion as regression, or HEAD claim promotion were rejected as semantic changes.

## Current-only compatibility

**Decision**: `analyze_current_repository`, `check`, and `explain` use only HEAD config and normal current discovery. Keep `compare_contracts`, representatives, identity, Markdown links, nested paths, package scripts, sorting, formatting, and statuses unchanged.

**Rationale**: Historical carry-forward exists only to compare BASE contracts; applying it to current inspection changes the public meaning.

**Alternatives considered**: Sharing union logic across all commands and exposing rule provenance were rejected.

## Verification strategy

**Decision**: Test first at extraction, repository, and orchestration boundaries; use an explicit call counter to prove the comparison union loads each physical HEAD source once; add real-Git and exact CLI fixtures; run the suite three times, verify the unchanged Python 3.12–3.14 CI matrix, then run the unchanged demo and release validation.

**Rationale**: Real repositories prove snapshot ownership and no mutation; a call-count assertion directly verifies read-once orchestration; three repetitions satisfy the deterministic success criterion; matrix inspection prevents supported-version coverage from silently narrowing.

**Alternatives considered**: Unit-only or snapshot-only testing cannot prove the core Git-state behavior.
