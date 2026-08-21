# Research: Detect Path Regressions

## CLI parsing

**Decision**: Use the Python standard library's `argparse` with a `diff` subcommand and required `--base` option.

**Rationale**: The initial interface has one subcommand and one required option. `argparse` provides validation and help without runtime dependencies, aligns with the constitution's simplicity principle, and is available on every supported Python installation.

**Alternatives considered**: Click and Typer offer decorators and richer presentation but introduce dependencies without a current requirement. Manual argument parsing would make help and error handling less reliable.

## Repository snapshot access

**Decision**: Resolve and inspect BASE directly from Git's object database; inspect HEAD as the checked-out working tree rooted by `git rev-parse --show-toplevel`.

**Rationale**: Direct BASE reads avoid checkout mutation and temporary worktrees. Working-tree HEAD lets maintainers check both committed CI changes and local changes before commit. Commands receive arguments without shell interpolation. BASE instruction discovery uses recursive tree listing; individual contents and target existence are obtained from the resolved commit/tree. HEAD discovery uses tracked plus non-ignored untracked paths and filters existing `AGENTS.md`/`CLAUDE.md` files.

**Alternatives considered**: Creating a temporary worktree is heavier and mutates Git administrative state. Comparing two commits only would ignore local changes. Parsing `.git` internals directly is complex and less portable than invoking Git.

## Runtime and development dependencies

**Decision**: Use only Python's standard library at runtime and pytest for tests, managed through uv.

**Rationale**: Regex, `pathlib`, `posixpath`, frozen dataclasses, subprocess execution, and argument parsing cover the required behavior. pytest is justified by the explicit requirement and provides isolated temporary directories and expressive parametrization.

**Alternatives considered**: Markdown parsers were rejected because this feature needs only deliberately narrow constructs, and broad Markdown interpretation could reduce precision. GitPython was rejected because the Git CLI already supplies the needed stable operations.

## Candidate extraction grammar

**Decision**: Treat a candidate as either the content of a single-backtick inline code span that has a repository-path shape, or the destination of a non-image inline Markdown link. Do not parse arbitrary prose, reference-style link definitions, autolinks, HTML, or fenced-code content in this feature.

Inline candidates must be relative, contain at least one `/`, have no whitespace, and consist of conservative filename characters (`A-Z`, `a-z`, digits, `.`, `_`, `-`, and `/`). Markdown destinations may be a relative filename such as `api.md` without `/`, because link syntax itself supplies high confidence. Angle-bracket-wrapped local destinations may be unwrapped. External schemes, network paths, root-absolute paths, fragment-only destinations, and query-bearing destinations are rejected. A local destination's fragment is ignored for `PathExists` because the contract concerns the file or directory.

**Rationale**: Explicit syntax plus conservative characters prioritizes precision. Excluding fenced code avoids treating examples as repository instructions. Markdown links can confidently identify simple sibling files that inline prose cannot.

**Alternatives considered**: Natural-language token scanning would increase recall but violates the precision requirement. A full Markdown parser adds a dependency and broader semantics that are not requested. Supporting every CommonMark edge case would expand scope without improving the seven required scenarios.

## Cross-platform repository paths

**Decision**: Represent all Git/repository paths internally as normalized relative strings with `/` separators. Resolve lexically using POSIX repository semantics, then convert the normalized target into platform-native path components only at the working-tree boundary.

**Rationale**: Git tree paths always use `/`, contract identity must be stable across hosts, and lexical normalization does not require a path to exist. Reject leading `/`, drive/UNC forms, NUL, and any normalized path equal to or beginning with `..`.

**Alternatives considered**: Using host-native `Path` values for identity can vary separators and drive rules by operating system. Calling `resolve()` follows the host filesystem and can fail for intentionally missing HEAD targets.

## Contract promotion and comparison

**Decision**: Promote resolved BASE claims only when the Git tree confirms the target exists. Build the set of resolved HEAD identities independently. For each baseline identity, report a regression exactly when it is in the HEAD claim set and its target is absent from the working tree.

**Rationale**: This directly encodes BASE validation, stable identity, claim survival, and target disappearance. Set comparison naturally ignores line/prose movement and deduplicates repeated claims.

**Alternatives considered**: Comparing line diffs makes identity unstable. Tracking all path-like candidates creates false positives. Git rename detection is explicitly out of scope.

## Error and result contract

**Decision**: Reserve exit 0 for a completed comparison without regressions, exit 1 for detected regressions, and exit 2 for usage or operational errors. Sort regression output by source, type, and target.

**Rationale**: The three states are distinct for humans and automation, errors cannot be mistaken for passes, and stable ordering makes output deterministic and testable.

**Alternatives considered**: Returning exit 1 for both regressions and failures loses important automation semantics. Structured output formats are deferred because none are required.

