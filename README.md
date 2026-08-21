# InstrProof

InstrProof detects repository paths in AI coding instructions that existed at a chosen BASE revision but disappeared from the current working tree while the same instruction claim remains.

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

Run the command from anywhere inside the repository to inspect:

```sh
uv run instrproof diff --base origin/main
```

BASE is read from the specified Git commit without checking it out. HEAD is the current working tree, including tracked modifications and non-ignored untracked files, so the same workflow supports local changes and clean CI checkouts.

## Supported instructions and paths

InstrProof searches repository files named `AGENTS.md` or `CLAUDE.md`. It recognizes two deliberately narrow forms:

- Repository-root-relative paths in inline code, such as `` `src/auth/service.py` ``.
- Local Markdown links, such as `[API](api.md)`, resolved relative to the instruction document containing the link.

Targets are normalized to repository-relative `/`-separated paths. Candidates that escape the repository, use absolute or external destinations, occur only in arbitrary prose or fenced code, or do not exist in BASE are not monitored. This precision boundary is deterministic and uses no LLM.

## Comparison behavior

A BASE-valid `PathExists` contract is identified by its instruction source, contract type, and normalized target. Line numbers, surrounding prose, link labels, and original path spelling are not part of identity.

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
PathExists  source=AGENTS.md  target=src/auth/service.py
```

## Exit statuses

| Status | Meaning |
|--------|---------|
| `0` | Comparison completed with no regressions. |
| `1` | Comparison completed with one or more regressions. |
| `2` | Arguments were invalid or repository inspection failed. |

Operational failures are written to stderr with an `error:` prefix and are never reported as a passing comparison.

## Testing

```sh
uv run pytest
uv run pytest tests/unit
uv run pytest tests/integration
```

Tests create repositories under pytest temporary directories; they do not modify the InstrProof repository.
