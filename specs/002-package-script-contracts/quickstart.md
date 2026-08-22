# Quickstart: Validate Package Script Contracts

## Prerequisites

- Python 3.12 or newer
- Git
- uv

## Install and run all checks

From the repository root:

```sh
uv sync --dev
uv run pytest
```

The full suite is the compatibility gate: all existing PathExists cases must remain green alongside the new package-script cases. Tests use temporary Git repositories and do not modify this repository.

Focused checks:

```sh
uv run pytest tests/unit/test_extract.py tests/unit/test_models.py tests/unit/test_compare.py
uv run pytest tests/integration/test_repository.py tests/integration/test_cli_diff.py
uv run pytest tests/integration/test_performance.py
```

See [contracts/cli.md](contracts/cli.md) for exact output and error behavior and [data-model.md](data-model.md) for identity and evidence rules.

## End-to-end validation matrix

Each scenario creates a committed BASE in a temporary repository, mutates its working tree as HEAD, and runs:

```sh
uv run instrproof diff --base HEAD
```

| Scenario | BASE | HEAD | Expected |
|----------|------|------|----------|
| Script retained | Instruction contains `pnpm typecheck`; root manifest defines `typecheck` | Script key remains | Exit 0; pass |
| Script removed | Same | Remove `typecheck` key; claim unchanged | Exit 1; PackageScriptExists regression |
| Script renamed only | Same | Rename key to `check-types`; claim unchanged | Exit 1 for target `typecheck` |
| Coordinated rename | Same | Rename key and change claim to `pnpm check-types` | Exit 0; old contract retired |
| Instruction removed | Same | Remove claim or source; remove script | Exit 0; old contract retired |
| Missing in BASE | Claim names `typecheck`; BASE root manifest lacks it | Any HEAD state | Candidate not monitored; exit 0 |
| Syntax-only change | `pnpm run typecheck` | Claim becomes `pnpm typecheck`; script removed | Same identity survives; exit 1 |
| Prose/line movement | Valid claim and BASE script | Move claim and edit prose; remove script | Same identity; exit 1 with new diagnostic line |
| Command body change | Script value is `tsc --noEmit` | Value changes but key remains | Exit 0 |
| Root-only evidence | Root lacks script; nested manifest defines it | Claim unchanged | Not monitored; exit 0 |
| Mixed contracts | Valid path and package claims | Remove both evidence targets | Exit 1; one row of each type |
| Multiple scripts | Several valid package claims | Remove multiple keys | Exit 1; stable deterministic rows |

Every regression row exposes the instruction source, current source line when available, contract type, normalized target, and `base=present head=missing`. These diagnostic fields do not affect identity. Mixed rows sort by source, contract type, and target.

## Extraction matrix

Unit tests verify exact normalization:

| Instruction command text | Result |
|-------------------------|--------|
| `npm run typecheck` | `PackageScriptExists(typecheck)` candidate |
| `pnpm test:unit` | `PackageScriptExists(test:unit)` candidate |
| `pnpm run test:unit` | Same normalized target |
| `pnpm build/client` | `PackageScriptExists(build/client)` candidate |
| `yarn lint-fix`, `yarn build_docs`, `yarn docs.build` | Exact respective targets |
| `yarn typecheck` | `PackageScriptExists(typecheck)` candidate |
| `yarn run typecheck` | Same normalized target |
| `npm typecheck` | Ignored |
| `pnpm install`, `yarn add` | Ignored by the exact shorthand exclusion sets |
| `pnpm run install`, `yarn run add` | Candidates; explicit `run` bypasses shorthand exclusions |
| `pnpm typecheck --watch` | `typecheck`; whitespace terminates the script token |
| `pnpm typecheck && yarn test:unit` | Two candidates; `&&` terminates the first token |
| `pnpm typecheck || yarn test`, `pnpm typecheck; yarn test`, `pnpm typecheck | tool` | The specified operator terminates `typecheck` |
| `pnpm typecheck@next`, `pnpm "typecheck"`, `xpnpm typecheck` | Ignored occurrence when its required boundary or token adjacency is invalid |
| A supported-looking command inside a fenced block | Ignored consistently with existing extraction |

## Error validation

With a surviving package-script contract, replace HEAD root `package.json` with malformed JSON and rerun the command. Expected result:

- exit 2;
- no success or regression output on stdout;
- concise `error:` diagnostic on stderr.

Repeat with malformed BASE root `package.json` and a BASE package candidate. It must also exit 2. By contrast, a valid manifest whose `scripts` object lacks the target is ordinary missing evidence: it prevents BASE promotion or causes a HEAD regression according to the pipeline stage.
