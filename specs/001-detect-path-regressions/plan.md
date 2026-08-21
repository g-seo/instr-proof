# Implementation Plan: Detect Path Regressions

**Branch**: `001-detect-path-regressions` | **Date**: 2026-08-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-detect-path-regressions/spec.md`

## Summary

Build a deterministic Python 3.12+ CLI that discovers explicit path claims in `AGENTS.md` and `CLAUDE.md`, promotes only BASE-validated claims to `PathExists` contracts, and reports contracts whose claims survive in the checked-out HEAD working tree while their targets do not. Use standard-library argument parsing, immutable Git-object access for BASE, ordinary filesystem access for HEAD, small frozen data records for domain values, and pytest fixture repositories for unit and end-to-end coverage.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: Python standard library only at runtime; pytest as the sole development dependency; Git executable as an external prerequisite

**Storage**: No persistent application storage; BASE data is read from Git objects and HEAD data from the working tree

**Testing**: pytest with unit tests and temporary Git repository integration/CLI tests

**Target Platform**: Cross-platform command-line environments with Python 3.12+ and Git available

**Project Type**: Installable Python CLI application using a `src/` package layout

**Performance Goals**: Complete a comparison of 100 instruction documents and 1,000 candidate references within 5 seconds under normal local conditions

**Constraints**: Deterministic and offline; no LLM; minimal dependencies; paths represented with repository-standard `/` separators; explicit failures for invalid repository/base state; no mutation of the inspected repository

**Scale/Scope**: One repository, one user-provided BASE ref, checked-out HEAD working tree, `AGENTS.md` and `CLAUDE.md`, and `PathExists` contracts only

## Constitution Check

*GATE: Passed before Phase 0 and re-checked after Phase 1.*

- **Simplicity & Necessity — PASS**: One package, five responsibility-focused modules, standard-library CLI/parsing/path primitives, and no general plugin framework. The only non-runtime dependency is required for automated tests.
- **Correctness & Testing — PASS**: Pure extraction/comparison functions receive unit coverage; temporary Git repositories exercise all seven acceptance cases, failures, output, and exit codes end to end.
- **Architectural Boundaries — PASS**: CLI presentation, Git/filesystem evidence access, extraction, and comparison are separated. The domain layer does not invoke Git or print output.
- **Security & Failure Handling — PASS**: Git is invoked with argument arrays, not a shell; refs and paths remain distinct arguments; paths are lexically normalized and repository escapes rejected; Git and decoding failures are surfaced explicitly.
- **Spec-Driven Change Discipline — PASS**: The design implements only requirements in `spec.md`; PackageScriptExists and other excluded capabilities receive no implementation design.

**Post-design re-check**: PASS. The Phase 1 model and CLI contract retain the same boundaries, add no dependency or speculative abstraction, and trace every state and outcome to the feature requirements.

## Technical Decisions

1. **CLI approach**: Use `argparse` and a console-script entry point. The command surface is too small to justify a CLI framework; standard-library parsing supplies required arguments, help, and stable exit handling.
2. **BASE and HEAD access**: Read BASE through `git rev-parse`, `git ls-tree`, and `git show`/`git cat-file` without checking it out. Read HEAD from the current working tree, using Git to locate the repository root and enumerate tracked plus non-ignored untracked files, then the filesystem for contents and existence. This includes local changes and behaves identically in a clean CI checkout.
3. **PathExists representation**: A frozen `PathExistsContract` value contains a `ContractIdentity`; evidence such as original spelling or line is optional diagnostic metadata on a separate `PathClaim`, never identity.
4. **Identity representation**: `ContractIdentity(source: RepoPath, contract_type: "PathExists", target: RepoPath)`, with source and target normalized to repository-relative POSIX-style strings. Frozen value equality and hashing provide deduplication; line and prose are excluded.
5. **Path resolution**: Recognize paths only inside inline code spans and local non-image Markdown links. Inline code paths resolve from repository root. Markdown link paths resolve from the instruction source's parent. Normalize `.`/`..` lexically, convert separators to `/`, and reject absolute paths, URLs, fragment-only links, empty destinations, and repository escapes. A file-plus-fragment Markdown link resolves to the file path; query-bearing links are rejected for precision.
6. **BASE validation**: Extract BASE candidates, resolve each path, and promote it only if the normalized target is present as a blob or tree in the BASE Git tree. Deduplicate by contract identity.
7. **HEAD claim survival**: Extract and resolve claims afresh from HEAD instruction sources. A baseline contract survives only if HEAD contains the same identity tuple. A regression exists only when that identity survives and the normalized target does not exist in the HEAD working tree. Changed or removed claims therefore disappear rather than regress.
8. **Module boundaries**: `models.py` holds immutable domain values; `extract.py` recognizes/resolves claims; `repository.py` supplies BASE/HEAD evidence; `compare.py` promotes and compares contracts; `cli.py` parses, orchestrates, formats, and maps outcomes to exit codes. No registry or generic contract plugin layer is introduced.
9. **Test strategy**: Unit-test normalization, extraction, identity, promotion, and comparison with in-memory inputs. Integration and CLI tests initialize repositories under pytest `tmp_path`, configure local Git identity, commit BASE fixtures, mutate the working tree into HEAD scenarios, and invoke the CLI without altering this repository.
10. **Output and exit behavior**: A clean comparison prints `No instruction contract regressions found.` and exits 0. Regressions print a summary followed by one stable, sorted line per regression containing `PathExists`, source, and target, and exit 1. Usage errors, invalid refs, non-repositories, unreadable/invalid instruction content, or Git failures print an `error:` message to stderr and exit 2.

## Project Structure

### Documentation (this feature)

```text
specs/001-detect-path-regressions/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md
```

### Source Code (repository root)

```text
pyproject.toml
src/
└── instrproof/
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    ├── compare.py
    ├── extract.py
    ├── models.py
    └── repository.py
tests/
├── conftest.py
├── unit/
│   ├── test_compare.py
│   ├── test_extract.py
│   └── test_models.py
└── integration/
    ├── test_cli_diff.py
    └── test_repository.py
```

**Structure Decision**: Use a conventional single-distribution `src/` layout. Five small modules reflect currently required boundaries; unit and integration test directories distinguish pure logic from temporary-repository behavior. `__main__.py` delegates to the same CLI entry point exposed by the installed `instrproof` command.

## Complexity Tracking

No constitution violations require justification.
