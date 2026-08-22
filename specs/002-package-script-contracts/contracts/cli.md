# CLI Contract: Mixed Instruction Contracts

## Invocation

```text
instrproof diff --base <base-ref>
python -m instrproof diff --base <base-ref>
```

No new command or option is introduced. The command discovers the same instruction documents and evaluates promoted `PathExists` and `PackageScriptExists` contracts together. BASE is read from the requested Git tree; HEAD is the current working tree.

## Standard output

### No regressions

Existing output remains unchanged:

```text
No instruction contract regressions found.
```

### PathExists regression

PathExists analysis behavior remains unchanged; its row now includes the diagnostics required by FR-024:

```text
Found 1 instruction contract regression:
PathExists  source=AGENTS.md:4  target=src/auth/service.py  base=present  head=missing
```

### PackageScriptExists regression

The row identifies the surviving HEAD claim location and evidence transition:

```text
Found 1 instruction contract regression:
PackageScriptExists  source=AGENTS.md:4  target=typecheck  base=present  head=missing
```

The line is diagnostic metadata, not identity. Moving the claim may change the displayed line but does not create or retire the logical contract.

### Mixed regressions

Rows are sorted lexically by normalized source, contract type, and normalized target, independent of extraction or filesystem order:

```text
Found 2 instruction contract regressions:
PackageScriptExists  source=AGENTS.md:4  target=typecheck  base=present  head=missing
PathExists  source=AGENTS.md:6  target=src/auth/service.py  base=present  head=missing
```

The summary counts both types. Multiple identical claims in one source collapse to one row; different sources remain distinct.

## Standard error

Usage and operational failures retain the existing form:

```text
error: <actionable description>
```

Package evidence errors include an unreadable root manifest, invalid UTF-8, malformed JSON, a non-object document root, or a present non-object `scripts` member when package evidence is required. These errors must not be rendered as a clean comparison or missing-script regression.

A missing root manifest or a valid manifest without the referenced script is ordinary missing evidence, not an operational error.

## Exit status

| Status | Meaning |
|--------|---------|
| `0` | Comparison completed; no new PathExists or PackageScriptExists regressions exist. |
| `1` | Comparison completed; one or more regressions of either type exist. |
| `2` | Arguments are invalid or repository/instruction/required manifest evidence could not be inspected reliably. |

## Identity and compatibility guarantees

- Identity is source + contract type + normalized target.
- Line, prose, package manager, written syntax, and script command body are excluded from identity.
- `pnpm run typecheck`, `pnpm typecheck`, and a supported yarn/npm form naming `typecheck` yield the same target identity in the same source.
- A changed target or removed claim retires the old contract before evidence validation.
- Existing PathExists extraction, validation, regression decisions, summaries, and exit behavior remain compatible; rows add only the FR-024 diagnostic metadata.
- Identical repository states and arguments produce deterministic output.
