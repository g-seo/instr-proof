# InstrProof

InstrProof detects repository paths and package scripts in AI coding instructions that existed at a chosen BASE revision but disappeared from the current working tree while the same instruction claim remains.

## Requirements

- Python 3.12 or newer
- Git
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
uv sync --dev
uv run pytest
```

The application has no runtime Python dependencies. Pytest is used for automated tests, and Hatchling is used only to build the installable package.

## Usage

Run commands from anywhere inside the repository. To inspect contracts whose
evidence exists in the current working tree:

```sh
uv run instrproof check
```

The output contains one deterministic row per contract identity, including its
representative diagnostic source line, type, normalized target, and
`current=present`, followed by an exact total. Claims with missing evidence and
unsupported or ambiguous text are not listed. Finding zero verified contracts
is successful.

To inspect every supported contract occurrence at an exact source line:

```sh
uv run instrproof explain AGENTS.md:37
uv run instrproof explain packages/auth/AGENTS.md:12
```

`explain` shows the source, type, normalized target, exact evidence reference,
and a current state of `PRESENT` or `MISSING`. A missing occurrence remains
explainable even though `check` does not verify it. Matching is exact against a
normalized repository-relative source and positive line; all distinct matches
on that line are shown in deterministic identity order. A valid location with
no supported occurrence reports a clear no-match result and status `1`.

These commands inspect only the current working tree and do not expose or infer
BASE/HEAD comparison state. Regression detection remains:

```sh
uv run instrproof diff --base origin/main
```

BASE is read from the specified Git commit without checking it out. HEAD is the current working tree, including tracked modifications and non-ignored untracked files, so the same workflow supports local changes and clean CI checkouts.

## Instruction discovery

By default, InstrProof discovers every repository file named `AGENTS.md` or
`CLAUDE.md`, at the repository root or at any nested depth. Each discovered
document is an independent instruction source, identified by its complete,
repository-relative `/`-separated path.

Repositories can add exact files and glob patterns with an optional root
`instrproof.json`:

```json
{
  "instructions": [
    ".claude/rules/**/*.md",
    "docs/agent-instructions.md"
  ]
}
```

The file must be UTF-8 JSON with an object root and may contain only the
optional `instructions` array of strings. Paths and patterns are
repository-relative and case-sensitive. `*`, `?`, and bracket expressions
match within one path segment; `**` as a complete segment matches zero or more
segments. Paths use `/` on every platform and cannot be absolute, escape the
repository, contain NUL or backslash characters, or contain malformed glob
expressions.

Overlapping and duplicate rules are allowed. InstrProof normalizes and
deduplicates matches by complete repository-relative path, so each physical
document is analyzed once per repository state. A valid rule matching no files
is not an error. Malformed, invalid, or unreadable configuration is an explicit
analysis error and returns status `2`.

The current working-tree configuration is read once per invocation. The same
rules discover sources independently from BASE and HEAD; neither state assumes
the other's files exist. Discovery only includes files in repository-contract
analysis and does not model any coding agent's loading, precedence, inheritance,
or scope behavior.

## Supported instruction contracts

InstrProof recognizes two deliberately narrow forms in every discovered source:

- Repository-root-relative paths in inline code, such as `` `src/auth/service.py` ``.
- Local Markdown links, such as `[API](api.md)`, resolved relative to the instruction document containing the link.

Targets are normalized to repository-relative `/`-separated paths. Candidates that escape the repository, use absolute or external destinations, occur only in arbitrary prose or fenced code, or do not exist in BASE are not monitored. This precision boundary is deterministic and uses no LLM.

InstrProof also recognizes these package-script command forms in instruction prose and inline code:

```text
npm run SCRIPT
pnpm run SCRIPT
pnpm SCRIPT
yarn run SCRIPT
yarn SCRIPT
```

`SCRIPT` is case-sensitive and matches `[A-Za-z0-9][A-Za-z0-9._:/-]*`. Whitespace, inline-code boundaries, end of text, the delimiters `, ) ] } ! ? .`, and the operators `&&`, `||`, `;`, and `|` terminate the token. Trailing arguments are not interpreted. Commands inside fenced code blocks are ignored.

The exact pnpm shorthand exclusions are:

```text
add approve-builds audit bin completion config create deploy dlx env exec fetch
help import init install link list outdated pack patch patch-commit patch-remove
prune publish rebuild remove root self-update server setup store unlink update view why
```

The exact yarn shorthand exclusions are:

```text
add bin cache completion config constraints create dedupe dlx exec explain help info
init install link npm pack patch patch-commit plugin rebuild remove search set stage
unlink unplug up upgrade version why workspace workspaces
```

Explicit `pnpm run SCRIPT` and `yarn run SCRIPT` bypass shorthand exclusions. A package-script candidate becomes a `PackageScriptExists` contract only when that exact key exists under `scripts` in BASE's repository-root `package.json`; nested/workspace manifests are not inspected.

## Comparison behavior

A BASE-valid `PathExists` or `PackageScriptExists` contract is identified by its instruction source, contract type, and normalized target. Line numbers, surrounding prose, package-manager spelling, link labels, and original claim spelling are not part of identity.

- If the same claim and target exist in HEAD, the command passes.
- If the same claim remains but the target is absent, it reports a regression.
- If the instruction changes to another target or is removed, the old contract is retired without a regression.

Passing output:

```text
No instruction contract regressions found.
```

Regression output is deterministic and sorted:

```text
Found 1 instruction contract regression:
PathExists  source=AGENTS.md:4  target=src/auth/service.py  base=present  head=missing
```

Package-script regressions use the same diagnostic fields:

```text
Found 1 instruction contract regression:
PackageScriptExists  source=AGENTS.md:7  target=typecheck  base=present  head=missing
```

Source locations and evidence states are diagnostics only and never participate in identity.

## Continuous integration

Use CI mode to run the same BASE/HEAD regression analysis with concise,
deterministic build-log output:

```sh
instrproof diff --base origin/main --ci
```

`--ci` changes only presentation and process status. It does not change which
contracts are selected or which repository changes count as regressions.

A completed comparison with no regressions exits `0` and reports the number of
baseline contracts checked:

```text
InstrProof ✓

31 baseline contracts checked.
No instruction contract regressions.
```

A completed comparison with regressions exits `1`, regardless of how many
regressions were found. Every regression is printed once in deterministic
source, contract-type, and target order:

```text
InstrProof ✗

2 instruction contract regressions

AGENTS.md:24
PathExists(src/auth/service.ts)

AGENTS.md:37
PackageScriptExists(typecheck)
```

If analysis cannot complete, CI mode writes a concise `Analysis error:` message
to stderr and exits `2`. Analysis errors are never presented as regressions.

The exact BASE passed with `--base` must resolve in the local checkout.
InstrProof does not fetch, guess, or substitute another revision. In particular,
the default shallow checkout used by many CI systems may omit `origin/main`; in
that case InstrProof exits `2` and asks you to make the requested reference
available.

### GitHub Actions

This minimal pull-request workflow fetches sufficient history and explicitly
creates the remote-tracking BASE used by InstrProof:

```yaml
name: InstrProof

on:
  pull_request:

jobs:
  instruction-contracts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install InstrProof
        run: python -m pip install instrproof
      - name: Make BASE available
        run: git fetch --no-tags origin +refs/heads/main:refs/remotes/origin/main
      - name: Check instruction contracts
        run: instrproof diff --base origin/main --ci
```

Configure the `instruction-contracts` job as a required check. Exit `0` passes;
exit `1` fails for confirmed instruction regressions; exit `2` fails because
InstrProof could not perform the comparison.

## Exit statuses

| Status | Meaning |
|--------|---------|
| `0` | Command completed successfully; for `diff`, no regressions were found, and for `check`, this includes zero contracts. |
| `1` | `diff` found one or more regressions, or `explain` found no occurrence at a valid location. |
| `2` | Arguments were invalid or repository analysis could not complete. |

Operational failures are written to stderr with an `error:` prefix and are
never represented as `MISSING` or a passing result. The existing `diff`
arguments, output, regression semantics, and completion behavior are unchanged.

## Testing

```sh
uv run pytest
uv run pytest tests/unit
uv run pytest tests/integration
```

Tests create repositories under pytest temporary directories; they do not modify the InstrProof repository.
