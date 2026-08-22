# Implementation Plan: Package Script Contracts

**Branch**: `002-package-script-contracts` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-package-script-contracts/spec.md`

## Summary

Extend the existing deterministic diff pipeline with a second typed candidate and contract, `PackageScriptExists`, while retaining the same instruction discovery, BASE promotion, HEAD claim-survival, regression comparison, CLI command, and exit semantics used by `PathExists`. A narrow extractor will normalize supported npm, pnpm, and yarn command forms to script-name targets. The existing repository boundary will read and validate only root `package.json` evidence from the BASE Git tree and HEAD working tree. The comparison layer will dispatch evidence checks by contract type, preserve diagnostic locations outside identity, and emit mixed regressions in the existing deterministic order without changing current PathExists rows.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: Python standard library (`argparse`, `dataclasses`, `enum`, `json`, `pathlib`, `re`, `subprocess`); Git executable as an external prerequisite; no new runtime dependency

**Storage**: No persistent application storage; BASE instructions and root `package.json` are read from Git objects, while HEAD evidence is read from the working tree

**Testing**: pytest with existing unit-test conventions and temporary Git repository integration/CLI fixtures

**Target Platform**: Cross-platform command-line environments with Python 3.12+ and Git available

**Project Type**: Installable Python CLI application using a `src/` package layout

**Performance Goals**: Complete a comparison of 100 instruction documents and 1,000 combined candidates within 5 seconds under normal local conditions

**Constraints**: Deterministic and offline; no LLM or shell-semantic parser; no new dependency; root `package.json` only; malformed required manifest evidence is an explicit analysis error; PathExists behavior and output remain compatible; no repository mutation

**Scale/Scope**: One repository, one BASE tree, checked-out HEAD working tree, existing `AGENTS.md`/`CLAUDE.md` discovery, and mixed `PathExists` plus `PackageScriptExists` contracts

## Constitution Check

*GATE: Passed before Phase 0 and re-checked after Phase 1.*

- **Simplicity & Necessity — PASS**: The design extends the five existing modules and standard-library implementation. It adds no package-script orchestrator, registry, plugin layer, new command, or dependency.
- **Correctness & Testing — PASS**: Narrow extraction, manifest parsing, typed identity, promotion, survival, mixed comparison, diagnostics, errors, and every required acceptance outcome receive automated coverage. The existing PathExists suite remains a mandatory compatibility gate.
- **Architectural Boundaries — PASS**: Candidate recognition remains in extraction, Git/filesystem and manifest access remain in the repository evidence boundary, typed values remain in models, comparison remains infrastructure-independent through evidence callbacks, and CLI remains presentation/orchestration only.
- **Security & Failure Handling — PASS**: BASE refs continue through argument-array Git calls; manifest bytes are decoded and parsed explicitly; malformed or unreadable required evidence raises `RepositoryError`; absence is represented separately and cannot be confused with an inspection failure.
- **Spec-Driven Change Discipline — PASS**: The design traces to feature 002 and preserves feature 001. Workspace lookup, monorepo discovery, semantic shell parsing, inferred replacements, and additional commands remain excluded.

**Post-design re-check**: PASS. The data model, CLI contract, and validation guide use the current architecture, introduce only the second required typed claim/evidence path, and contain no unresolved clarifications or constitution exceptions.

## Technical Decisions

1. **Extraction boundary**: Keep `extract.py` as the single candidate-extraction module. Add `extract_package_script_claims()` beside `extract_path_claims()`, reusing fenced-block masking and line calculation. Recognize commands in ordinary instruction prose and single-backtick inline code, but continue excluding fenced blocks. The repository comparison gathers both claim types from every discovered instruction source, so no second discovery or analysis pass is introduced.
2. **Deterministic command grammar**: Match lowercase managers in exactly `npm run SCRIPT`, `pnpm run SCRIPT`, `pnpm SCRIPT`, `yarn run SCRIPT`, and `yarn SCRIPT`. `SCRIPT` is case-sensitive and matches `[A-Za-z0-9][A-Za-z0-9._:/-]*`. Before the manager require start-of-text, ASCII whitespace, a backtick, or one of `([{:`. After `SCRIPT` require end-of-text, ASCII whitespace, a backtick, one of the explicitly enumerated prose delimiters `,)]}!?.`, or the shell operators `&&`, `||`, `;`, or `|`. Whitespace and operators terminate the script token and do not invalidate the candidate; trailing text is not parsed. Any other adjacent character rejects the match rather than extracting a prefix. This is lexical boundary recognition, not shell interpretation.
3. **Shorthand exclusions**: `npm SCRIPT` is never supported. Explicit `pnpm run SCRIPT` and `yarn run SCRIPT` bypass shorthand exclusions. For bare pnpm/yarn forms, reject exact lowercase tokens in the manager-specific frozen sets documented in `research.md`; a script colliding with a built-in remains expressible through `run`. BASE root-manifest validation remains the final promotion gate.
4. **Typed target representation**: Preserve `RepoPath` for instruction sources and filesystem claims, but change `ContractIdentity.target` to a validated normalized string value rather than forcing all targets through `RepoPath`. Path identities receive `RepoPath.value`; package-script identities receive the exact script token. `ContractType` becomes a closed two-value enum (`PathExists`, `PackageScriptExists`). Equality and ordering still use source, type, and normalized target only.
5. **Claim and contract types**: Retain `PathClaim` and `PathExistsContract`; add `PackageScriptClaim` and `PackageScriptExistsContract`. Each claim carries written command and source line for diagnostics, but these fields do not enter identity. Comparison accepts the two typed unions and derives identity through one shared function; it does not introduce a plugin registry or package-specific orchestration.
6. **Manifest evidence boundary**: Extend `GitRepository` with cached methods that return the set of script keys from `package.json` at the repository root for a requested BASE tree or HEAD working tree. BASE reads use the existing Git object access; HEAD reads use the existing root filesystem boundary. The regression engine receives script-existence callbacks/sets and never parses JSON.
7. **Manifest state semantics**: An absent root `package.json`, or a valid manifest with no `scripts` member, provides ordinary missing evidence. When candidates or surviving contracts require inspection, unreadable bytes, invalid UTF-8, malformed JSON, a non-object document root, or a present non-object `scripts` member is an explicit `RepositoryError`. Script values are not interpreted; key presence alone satisfies evidence.
8. **Lazy evidence reads**: Read BASE package-script evidence only when BASE extraction produced package-script candidates. Read HEAD package-script evidence only when at least one promoted package-script identity survives HEAD claim extraction. Thus unrelated malformed manifests do not break path-only comparisons, while malformed evidence cannot be silently treated as absence when package-script analysis needs it.
9. **Promotion and survival**: Promote each BASE path claim through existing path evidence and each BASE package-script claim only when its normalized name is in BASE script keys. Deduplicate both by identity. Re-extract HEAD claims and match identities as a set; changing package-manager syntax while retaining the same target survives, while changing the target or removing the instruction retires the old contract.
10. **Regression dispatch**: For each surviving baseline identity, call the evidence check selected by its closed contract type. A missing path uses existing target semantics; a missing script key creates a package regression. Sort mixed regressions by source, contract type value, and target, preserving deterministic behavior.
11. **Diagnostic evidence**: Retain a representative BASE claim location on promoted contracts and a representative HEAD location for surviving claims. A regression records `base_evidence=present` and `head_evidence=missing` for either contract type; CLI rows expose source, current HEAD line when available, type, target, and both evidence states. Metadata never participates in equality, hashing, identity matching, or sort order.
12. **CLI compatibility**: Keep `instrproof diff --base <base-ref>` and exit codes 0/1/2 unchanged. The clean message and summary remain unchanged. Both PathExists and PackageScriptExists regression rows gain the newly specified diagnostic fields in one common row format; their analysis semantics remain compatible.
13. **Test placement**: Extend existing model, extractor, comparison, repository, CLI integration, and performance files rather than creating a parallel test hierarchy. Parameterized extraction cases cover every grammar boundary, delimiter, operator, supported spelling, and shorthand exclusion. Temporary repositories cover BASE/HEAD manifest states, identity/diagnostics, mixed contracts, deterministic ordering, malformed evidence, and root-only resolution.

## Project Structure

### Documentation (this feature)

```text
specs/002-package-script-contracts/
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
pyproject.toml           # Existing Python/package/test configuration; no dependency change
src/
└── instrproof/
    ├── __init__.py
    ├── __main__.py
    ├── cli.py           # Existing diff output and error mapping; add package regression row
    ├── compare.py       # Shared typed promotion, survival, and evidence dispatch
    ├── extract.py       # Existing path extraction plus narrow package-command extraction
    ├── models.py        # Second claim/contract type, generic normalized identity target, metadata
    └── repository.py    # Existing snapshot boundary plus cached root package.json scripts
tests/
├── conftest.py          # Existing temporary Git fixtures, extended only where shared setup helps
├── unit/
│   ├── test_compare.py  # Typed promotion, identity, survival, mixed ordering
│   ├── test_extract.py  # Supported and rejected package command grammar
│   └── test_models.py   # Contract type/target identity and diagnostic metadata exclusion
└── integration/
    ├── test_cli_diff.py # End-to-end package and mixed diff outcomes/output/errors
    ├── test_performance.py
    └── test_repository.py # BASE/HEAD root manifest access and parse failures
```

**Structure Decision**: Keep the feature-001 single-distribution layout and modify only the existing responsibility-focused modules. Package-script support is a second typed path through the established pipeline, not a new subsystem.

## Complexity Tracking

No constitution violations require justification.
