# Quickstart: Validate Instruction Discovery

## Automated validation

Prerequisites are Python 3.12+, Git, `uv`, and the completed feature implementation. From repository root:

```sh
uv sync --dev
uv run pytest
```

Focused runs:

```sh
uv run pytest tests/unit/test_discovery.py tests/unit/test_models.py
uv run pytest tests/integration/test_repository.py
uv run pytest tests/integration/test_cli_diff.py
uv run pytest tests/integration/test_performance.py
```

All feature 001 and 002 tests must retain their outcomes.

## Manual setup

In a disposable Git repository, create root and nested `AGENTS.md`/`CLAUDE.md`, `.claude/rules/testing.md`, `.claude/rules/packages/auth.md`, and `docs/agent-instructions.md`. Add:

```json
{
  "instructions": [
    ".claude/rules/**/*.md",
    "docs/agent-instructions.md",
    "packages/auth/AGENTS.md"
  ]
}
```

The explicit nested `AGENTS.md` deliberately overlaps default discovery. Put distinct BASE-valid claims in all sources, commit, and run:

```sh
uv run instrproof diff --base HEAD
```

Expected: status `0`; all default/configured sources participate, both recursive-glob files match, and overlap does not duplicate analysis. A valid zero-match glob also succeeds.

## Deduplication and identity

Put one equal claim in root `AGENTS.md` and `packages/auth/AGENTS.md`, retain the overlapping config entry, commit valid evidence, then remove the target.

Expected: exactly two regressions, one per complete source path. The nested source appears once.

## Nested path resolution

In `packages/auth/AGENTS.md`, add:

```markdown
See [architecture](docs/architecture.md).
Use `docs/root-policy.md`.
```

Create `packages/auth/docs/architecture.md` and `docs/root-policy.md`, commit BASE, then remove both without changing claims.

Expected: PathExists regressions target `packages/auth/docs/architecture.md` and `docs/root-policy.md`, proving Markdown-link locality and root-relative inline behavior.

## Nested PackageScriptExists

Add `Run pnpm typecheck.` to a nested/configured source and define `typecheck` in root `package.json` before BASE. Remove the root script in HEAD.

Expected: one PackageScriptExists regression whose source is the complete nested/configured path. Nested manifests remain irrelevant.

## Independent BASE and HEAD discovery

With one unchanged config, verify:

- deleting a BASE instruction and evidence retires its claim;
- updating a BASE claim to a new target retires the old claim;
- a HEAD-only instruction creates no BASE regression;
- an unchanged source/claim with removed evidence regresses.

These outcomes use existing claim-survival behavior without file lifecycle special cases.

## Configuration failures

Separately try malformed JSON, non-array `instructions`, a non-string entry, an unknown key, an absolute entry, and `../outside.md`.

Expected for each: no normal result, an `error:` diagnostic, and status `2`. See [contracts/cli.md](contracts/cli.md).
