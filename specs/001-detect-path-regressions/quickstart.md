# Quickstart: Validate Path Regression Detection

## Prerequisites

- Python 3.12 or newer
- Git
- uv

## Install and test

From the repository root:

```sh
uv sync --dev
uv run pytest
```

The automated suite creates temporary Git repositories and must not modify the InstrProof repository. It covers the seven required scenarios plus invalid BASE and repository failures.

## Run the CLI

Inside a repository containing committed BASE instruction documents:

```sh
uv run instrproof diff --base origin/main
```

See [contracts/cli.md](contracts/cli.md) for exact output and exit behavior and [data-model.md](data-model.md) for contract identity rules.

## End-to-end validation matrix

Each scenario starts with a committed BASE, mutates the temporary working tree to represent HEAD, and invokes the command with the BASE commit identifier.

| Scenario | BASE | HEAD change | Expected |
|----------|------|-------------|----------|
| Existing target | `AGENTS.md` contains `` `src/auth/service.py` `` and target exists | Target remains | Exit 0; no regression |
| Broken target | Same | Remove or rename only target | Exit 1; one `PathExists` regression |
| Updated instruction | Same | Rename target and update claim to new path | Exit 0; old contract retired |
| Removed instruction | Same | Remove claim or instruction document | Exit 0; old contract retired |
| Prose/line movement | Same | Move line or edit surrounding prose only | Contract identity unchanged; target determines pass/regression |
| Invalid BASE target | Claim points to nonexistent path | Leave or remove claim | Candidate is not monitored; exit 0 |
| Nested Markdown link | `docs/CLAUDE.md` contains `[API](api.md)` and `docs/api.md` exists | Remove `docs/api.md` only | Exit 1; target is `docs/api.md` |

## Focused checks

```sh
uv run pytest tests/unit
uv run pytest tests/integration
```

The integration suite should also assert stable stdout/stderr and exit statuses 0, 1, and 2 as specified by the CLI contract.

