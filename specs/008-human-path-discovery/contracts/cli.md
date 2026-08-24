# CLI and Behavior Contract: Root Paths and Revisioned Discovery

## Public commands

`instrproof check`, `instrproof explain <source:line>`, `instrproof diff --base <ref>`, and `diff --ci` keep their commands, arguments, output, ordering, and statuses. No provenance output is added.

## Root-level inline `PathExists`

Inline code outside fences accepts a complete one-segment token when its final extension begins with an ASCII letter, or it exactly equals `Makefile`, `Dockerfile`, `Containerfile`, `Justfile`, `Procfile`, `LICENSE`, or `NOTICE`.

Accepted examples: `README.md`, `Cargo.toml`, `package.json`, `pyproject.toml`, `.pre-commit-config.yaml`, and every exact allowlist name.

Rejected examples: `pytest`, `src`, `main`, `build`, `README`, `v1.0`, `python3.12`, `*.md`, `${CONFIG}`, absolute paths, URLs/fragments/queries, placeholders, shell expressions, whitespace, NUL, slash, and backslash forms.

Matching is case-sensitive. Lexical acceptance becomes an existing `PathExists` baseline contract only when the exact normalized path exists in BASE. Nested inline paths, source-relative Markdown links, fenced masking, package scripts, normalization, and identity remain unchanged.

## Configuration ownership

- BASE reads `instrproof.json` from the exact resolved Git tree.
- HEAD reads the current working-tree file.
- Absence means no additional rules in that state.
- Default root/nested `AGENTS.md` and `CLAUDE.md` discovery applies in both.
- Both use the same existing schema and validation.

HEAD rules never apply retroactively to BASE. BASE rules do not replace normal HEAD rules.

## Comparison-only preservation

Diff HEAD sources are the sorted unique union of normal HEAD discovery and readable working-tree files at BASE-discovered source paths.

- Removed HEAD rule cannot hide an unchanged stale surviving claim.
- Repaired/removed claim retains coordinated-update PASS.
- Deleted instruction source retains instruction-removal PASS.
- HEAD-only rule creates no BASE contract.
- Overlap analyzes one physical source once.

`check` and `explain` use only current defaults and HEAD config.

## Errors and identity

Both configs require readable UTF-8 JSON, object root, supported optional `instructions` string array, and valid rules. Failures use attributable `BASE instrproof.json` or `HEAD instrproof.json` context, produce no comparison, and exit 2.

Identity remains `instruction source + contract type + normalized target`; line, spelling, form, rule, and state are excluded.

| Status | Meaning |
|--------|---------|
| `0` | Completed with no diff regressions; existing command success semantics apply. |
| `1` | Diff regression, or explain no-match. |
| `2` | Argument, configuration, or repository analysis error. |

Normal and CI diff compare identical contracts; `--ci` changes presentation only.
