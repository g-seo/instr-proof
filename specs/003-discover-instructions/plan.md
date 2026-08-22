# Implementation Plan: Discover Instruction Documents

**Branch**: `003-discover-instructions` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-discover-instructions/spec.md`

## Summary

Extend InstrProof's repository boundary with a dedicated, deterministic instruction-discovery component. One repository-local configuration supplies optional additional file/glob rules; the same resolved rules select normalized repository-relative paths independently from the existing BASE and HEAD path listings. The repository boundary loads each selected document, and the existing extractors, evidence promotion, identity, claim-survival comparison, reporting, and `diff` CLI pipeline consume those sources unchanged. This retains complete nested source paths, naturally preserves Markdown-link context, and deduplicates overlaps before extraction.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: Python standard library (`argparse`, `dataclasses`, `enum`, `fnmatch`, `json`, `pathlib`, `re`, `subprocess`); Git executable as an external prerequisite; no new runtime dependency

**Storage**: No persistent application storage; optional repository-root `instrproof.json`, BASE Git objects, and HEAD working-tree files

**Testing**: pytest with existing unit conventions and temporary Git repository integration/CLI fixtures

**Target Platform**: Cross-platform command-line environments with Python 3.12+ and Git available; repository paths and configured patterns use normalized `/` separators

**Project Type**: Installable Python CLI application using a `src/` package layout

**Performance Goals**: Complete a comparison of 100 discovered instruction documents and 1,000 combined candidates within 5 seconds under normal local conditions

**Constraints**: Deterministic and offline; one repository path enumeration per state; no LLM, agent-loading semantics, cache/index layer, or new dependency; explicit configuration failures; existing 001/002 extraction and comparison behavior unchanged; no repository mutation

**Scale/Scope**: One repository, one BASE tree, checked-out HEAD working tree, default recursive `AGENTS.md`/`CLAUDE.md` discovery, optional explicit file/glob rules, and existing PathExists plus PackageScriptExists contracts

## Constitution Check

*GATE: Passed before Phase 0 and re-checked after Phase 1.*

- **Simplicity & Necessity — PASS**: One focused discovery module and a small standard-library JSON format solve the current requirement. Existing path listings are reused; no dependency, plugin system, index, cache, or parallel infrastructure is added.
- **Correctness & Testing — PASS**: Pure discovery rules receive focused unit coverage; repository/configuration failures and BASE/HEAD independence receive integration coverage; existing extractors and comparison behavior are exercised end to end from nested and configured sources. The complete 001/002 suite remains a compatibility gate.
- **Architectural Boundaries — PASS**: Discovery selects normalized source paths only; `GitRepository` remains the Git/filesystem access boundary; extraction consumes `InstructionSource` values without discovery knowledge; comparison and CLI responsibilities remain unchanged.
- **Security & Failure Handling — PASS**: Configuration is decoded and structurally validated at the repository boundary, patterns cannot be absolute, backslash-based, NUL-containing, or repository-escaping, Git remains argument-array based, and read/parse failures become explicit `RepositoryError` outcomes.
- **Spec-Driven Change Discipline — PASS**: The plan implements feature 003 and explicitly preserves features 001 and 002. Agent loading, precedence, inheritance, semantic scope, contradiction detection, additional commands, and optimization infrastructure remain excluded.

**Post-design re-check**: PASS. Research, the data model, the configuration/CLI contract, and the quickstart retain the existing architecture and contain no unresolved clarifications or constitution exceptions.

## Technical Decisions

1. **Discovery boundary**: Add `discovery.py` containing the immutable discovery configuration and pure selection/glob logic. Its public operation accepts an iterable of repository-relative `RepoPath` file paths and returns a sorted, unique tuple of `RepoPath` instruction sources. It does not read Git, the filesystem, file content, or contract claims.
2. **Default rules**: Select any repository file whose final path component is exactly `AGENTS.md` or `CLAUDE.md`. This covers root and arbitrary nesting without encoding agent precedence or scope.
3. **Configuration format**: Add optional repository-root `instrproof.json` with one optional `instructions` array of strings. Each string is a repository-relative exact path or glob. An absent file means an empty additional list and preserves zero-configuration behavior. Unknown top-level keys are rejected so configuration mistakes remain observable and the first format version stays narrow.
4. **Configuration state**: Read configuration once from the current working tree before BASE/HEAD source discovery and apply that identical resolved rule set to both states. Configuration chooses the analysis performed by the current invocation; it is not itself a historical contract source. BASE and HEAD therefore differ only by which files exist in each enumerated snapshot, not by silently using different rule sets.
5. **Configuration failures**: Unreadable bytes, invalid UTF-8, malformed JSON, non-object root, unknown keys, non-array `instructions`, or non-string entries raise `RepositoryError` and map to existing CLI exit 2. Empty strings, absolute/drive paths, NULs, backslashes, and patterns that normalize outside the repository are invalid. Duplicate entries are accepted. A valid rule matching zero paths is not an error.
6. **Pattern classification**: A configured string containing `*`, `?`, or `[` is a glob; otherwise it is an exact repository-relative path. Exact paths use `RepoPath` normalization. Glob patterns normalize safe literal `.` segments and repeated separators while retaining metacharacters, reject repository escape, and use `/` regardless of host OS.
7. **Glob semantics**: Match the entire repository-relative path, segment by segment. `*`, `?`, and bracket expressions apply within one segment; `**` as a complete segment matches zero or more complete path segments. Matching is case-sensitive to align with Git path identity and is independent of host path-library behavior. Invalid/unclosed bracket syntax is rejected rather than treated as a literal typo.
8. **Single traversal per state**: Reuse `git ls-tree -rz --name-only <snapshot>` for BASE and `git ls-files -z --cached --others --exclude-standard` plus `is_file()` filtering for HEAD. Each method forms its complete normalized file list once, gives it to discovery once, then reads only selected sources. Do not invoke one Git/filesystem scan per configured rule.
9. **Deduplication and order**: Combine default and configured matches in a set keyed by normalized `RepoPath`, then return lexicographically sorted paths. A file matched by defaults, exact entries, repeated patterns, or overlapping globs is read and analyzed once per state.
10. **Source model**: Relax `InstructionSource` validation from two hard-coded filenames to any valid `RepoPath`; discovery now owns eligibility. Preserve the full path in every source. No extraction model, claim model, `ContractIdentity`, or diagnostic identity rule changes.
11. **Repository integration**: `GitRepository` loads and validates discovery configuration, enumerates each state, delegates selection, and loads UTF-8 content for the selected paths. Existing `base_instruction_sources()` and `head_instruction_sources()` remain the downstream interface, extended to accept the resolved discovery configuration.
12. **Comparison orchestration**: `compare_repository()` loads discovery configuration once and passes it to BASE and HEAD source access. All comprehensions invoking `extract_path_claims()` and `extract_package_script_claims()`, evidence callbacks, promotion, survival, regression sorting, and output remain structurally unchanged.
13. **Resolution compatibility**: Existing `extract._resolve()` already joins Markdown links to `source.path.parent` and leaves inline paths rooted at the repository. Keeping the complete nested `RepoPath` through discovery is sufficient; add regression tests but no special path-resolution branch.
14. **CLI and documentation**: Keep `instrproof diff --base <ref>` and exit codes 0/1/2. Document `instrproof.json`, defaults, matching/deduplication, BASE/HEAD behavior, and explicit errors in README and `contracts/cli.md`; do not add configuration flags or commands.
15. **Test placement**: Add `tests/unit/test_discovery.py`; extend `test_models.py` for additional source filenames; extend `test_repository.py` for configuration parsing, default/configured selection, deduplication, zero matches, and independent state discovery; extend `test_cli_diff.py` for nested PathExists, nested PackageScriptExists, distinct source identities, deletion/update survival, and error mapping; retain and rerun all existing tests and performance coverage.

## Project Structure

### Documentation (this feature)

```text
specs/003-discover-instructions/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md             # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
README.md                # Document defaults and instrproof.json
pyproject.toml           # Existing package/test configuration; no dependency change
src/
└── instrproof/
    ├── __init__.py
    ├── __main__.py
    ├── cli.py           # Existing command/output/error mapping unchanged
    ├── compare.py       # Load one rule set; existing contract pipeline unchanged
    ├── discovery.py     # New pure path selection, validation, glob matching
    ├── extract.py       # Existing path and package-script extraction unchanged
    ├── models.py        # Allow any discovered RepoPath as InstructionSource
    └── repository.py    # Configuration and snapshot file-access boundary
tests/
├── conftest.py
├── unit/
│   ├── test_compare.py
│   ├── test_discovery.py # Default/configured matching, normalization, deduplication
│   ├── test_extract.py
│   └── test_models.py
└── integration/
    ├── test_cli_diff.py  # Nested/configured end-to-end contracts and survival
    ├── test_performance.py
    └── test_repository.py # Config errors and independent BASE/HEAD discovery
```

**Structure Decision**: Keep the existing single-distribution layout. The one new module isolates the newly required source-selection responsibility; all established feature-001/002 modules retain their current responsibility and are extended only at the discovery integration seam.

## Complexity Tracking

No constitution violations require justification.
