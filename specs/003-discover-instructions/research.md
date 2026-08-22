# Research: Discover Instruction Documents

## Existing repository discovery extension point

**Decision**: Split pure path selection into `discovery.py`, while retaining Git and working-tree enumeration/content loading in `GitRepository`.

**Rationale**: The repository abstraction already enumerates all BASE paths through `git ls-tree` and all tracked/non-ignored HEAD paths through `git ls-files`. Its current inline filename filter is the exact extension seam. A pure selector lets both states use identical rules without giving contract extraction any discovery knowledge.

**Alternatives considered**: Putting glob logic directly in both repository methods was rejected because it duplicates rules and risks BASE/HEAD drift. Moving Git traversal into discovery was rejected because it mixes policy with infrastructure. A generic snapshot protocol was rejected because the current repository boundary already meets the feature and no second backend exists.

## Existing configuration mechanism

**Decision**: Introduce optional `instrproof.json` at the repository root with this smallest supported shape:

```json
{
  "instructions": [
    ".claude/rules/**/*.md",
    "docs/agent-instructions.md"
  ]
}
```

**Rationale**: The repository has no application configuration mechanism. JSON is supported by Python's standard library, matches the existing strict `package.json` error conventions, and represents the required string list without a parser dependency or configuration framework. A visible root filename is easy to document and locate.

**Alternatives considered**: TOML would require additional format decisions; YAML requires a new dependency; CLI flags would not be repository-local; `pyproject.toml` would incorrectly assume analyzed repositories are Python projects; multiple locations would introduce precedence outside scope.

## Configuration lifecycle across BASE and HEAD

**Decision**: Read working-tree `instrproof.json` once per invocation and apply its resolved instruction rules unchanged to both BASE and HEAD enumerations.

**Rationale**: The requirement says both states use the same discovery rules while discovering independently. Current configuration expresses the analysis requested by the invocation. Historical configuration per snapshot could yield different rules and make survival depend on an unrequested configuration transition.

**Alternatives considered**: Reading config separately from BASE and HEAD was rejected because rule sets could differ. BASE-only config would ignore current additions. Merging historical and current config would invent precedence and migration semantics.

## Configuration validation and failure behavior

**Decision**: Absence means no additional rules. If present, the file must be readable UTF-8 JSON whose root is an object containing only optional `instructions`; that member must be an array of strings. Reject invalid path/pattern strings explicitly. Duplicate rules and valid zero-match rules are allowed.

**Rationale**: Strict structure catches misspelled keys and invalid representations rather than silently reducing analysis. Duplicate and zero-match rules have deterministic set semantics and are not configuration defects.

**Alternatives considered**: Ignoring unknown fields or invalid list elements was rejected because configuration errors must be analysis errors. Requiring the file or member was rejected because zero-configuration compatibility is required.

## Glob matching semantics

**Decision**: Use whole-path, case-sensitive POSIX-style matching: `/` separates segments; `*`, `?`, and bracket expressions match within a segment; a complete `**` segment matches zero or more path segments. Exact paths and glob literals normalize repository-safe `.` and repeated separators. Absolute, drive-prefixed, NUL-containing, backslash-containing, escaping, empty, and malformed bracket patterns are invalid.

**Rationale**: These rules make `.claude/rules/**/*.md` match direct and deeper Markdown files, are deterministic on every operating system, preserve Git's `/`-separated identity, and avoid host-specific path behavior. Standard-library `fnmatchcase` can implement single-segment matching while a small recursive segment matcher handles `**`.

**Alternatives considered**: `Path.glob()` cannot operate on BASE Git trees. Python 3.12 `PurePath.match()` is not a whole-path recursive matching API. Whole-string `fnmatchcase()` allows ordinary `*` across `/`. Git pathspecs would require repeated or divergent state access.

## Path normalization and deduplication

**Decision**: Convert enumerated files and exact rules to existing `RepoPath` values; validate globs under equivalent repository-relative rules; key the union of default and configured matches by `RepoPath`; sort lexicographically.

**Rationale**: `RepoPath` already defines canonical Git-style identity and rejects repository escape. Set membership guarantees one analysis per normalized physical path, and sorting prevents rule-order effects.

**Alternatives considered**: Raw-string deduplication would preserve aliases such as `docs//guide.md`. Deduplicating after content loading would duplicate work. Rule order provides no user value.

## Repository traversal

**Decision**: Enumerate each state once, then test collected paths against all rules in memory. BASE keeps one recursive `ls-tree`; HEAD keeps one tracked/non-ignored `ls-files` call and filters actual files before selection.

**Rationale**: Existing operations already provide the complete candidates. At the required scale, straightforward matching is simpler than repeated commands, indexes, caches, or parallel work.

**Alternatives considered**: One query/traversal per glob needlessly repeats work. An index, cache, or concurrent matcher lacks demonstrated need and adds speculative complexity.

## Nested path-resolution compatibility

**Decision**: Preserve full `RepoPath` values on `InstructionSource` and make no changes to extraction resolution.

**Rationale**: Existing extraction joins Markdown links to `source.path.parent`, while inline paths bypass that join and remain repository-root-relative. The only blocker for custom filenames is `InstructionSource`'s hard-coded filename validation; discovery should own eligibility.

**Alternatives considered**: Passing source directories separately duplicates state. Re-resolving claims in discovery or comparison violates existing boundaries and risks feature 001 behavior.
