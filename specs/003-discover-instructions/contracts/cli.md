# CLI and Configuration Contract: Instruction Discovery

## Command

```text
instrproof diff --base <base-ref>
```

Command syntax, comparison output, deterministic order, and exit statuses remain unchanged. Discovery only broadens the source set supplied to the existing pipeline.

## Default discovery

With no configuration, each state independently includes every file whose exact basename is `AGENTS.md` or `CLAUDE.md`, at root or arbitrary depth. Discovery does not imply agent loading, precedence, inheritance, or scope.

## Repository configuration

InstrProof optionally reads repository-root `instrproof.json` from the working tree:

```json
{
  "instructions": [
    ".claude/rules/**/*.md",
    "docs/agent-instructions.md"
  ]
}
```

- Absence equals `{ "instructions": [] }`.
- The root must be an object containing only optional `instructions`.
- `instructions`, when present, must be an array of strings.
- Entries without `*`, `?`, or `[` are exact paths; others are globs.
- Duplicate and overlapping entries are allowed.
- A valid entry matching zero files is allowed.
- Configuration is read once; identical rules apply to BASE and HEAD.

## Path and glob rules

- Use `/` separators on every platform.
- Values must be non-empty and repository-relative.
- Absolute/drive paths, NULs, backslashes, malformed brackets, and escaping `..` are invalid.
- Matching is case-sensitive over the complete path.
- `*`, `?`, and brackets match within one segment.
- A complete `**` segment matches zero or more segments.

Thus `.claude/rules/**/*.md` matches `.claude/rules/local.md` and `.claude/rules/packages/auth.md`.

## Discovery result contract

For each state, InstrProof enumerates files once, applies all rules, normalizes full repository-relative paths, deduplicates by normalized path, sorts lexically, and loads every selected source once. Downstream extraction receives only source path and content.

## Identity and resolution compatibility

Identity remains `instruction source + contract type + normalized target`. Complete source paths participate, so root and nested `AGENTS.md` sources remain distinct.

- Inline repository paths resolve from repository root.
- Markdown local links resolve from their containing source directory.

`[architecture](docs/architecture.md)` in `packages/auth/AGENTS.md` therefore resolves to `packages/auth/docs/architecture.md`.

## Errors and exit statuses

Configuration failures are analysis errors on stderr with `error:` and status `2`, including unreadable configuration, invalid UTF-8/JSON/schema, and invalid entries. A zero-match glob succeeds.

| Status | Meaning |
|--------|---------|
| `0` | Comparison completed with no regressions. |
| `1` | Comparison completed with regressions. |
| `2` | Arguments, configuration, or repository inspection failed. |
