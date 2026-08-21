# CLI Contract: `instrproof diff`

## Invocation

```text
instrproof diff --base <base-ref>
python -m instrproof diff --base <base-ref>
```

The command runs from anywhere inside the Git working tree. `<base-ref>` is passed to Git as one opaque argument and must resolve to a commit/tree that can be inspected. HEAD is the current working tree, including tracked modifications and non-ignored untracked files.

## Standard output

### No regressions

```text
No instruction contract regressions found.
```

### Regressions found

Regression rows are sorted lexically by normalized source, contract type, and normalized target.

```text
Found 1 instruction contract regression:
PathExists  source=AGENTS.md  target=src/auth/service.ts
```

Plural summary for multiple results:

```text
Found 2 instruction contract regressions:
PathExists  source=AGENTS.md  target=src/auth/service.ts
PathExists  source=docs/CLAUDE.md  target=docs/api.md
```

Line numbers and surrounding prose are intentionally absent from identity output.

## Standard error

Usage and operational failures use a concise diagnostic:

```text
error: <actionable description>
```

Examples include not being inside a Git work tree, an unresolvable BASE ref, Git inspection failure, and an instruction document that cannot be read or decoded. Git command details may be summarized, but raw tracebacks are not printed during normal CLI operation.

## Exit status

| Status | Meaning |
|--------|---------|
| `0` | Comparison completed; no new regressions exist. |
| `1` | Comparison completed; one or more new regressions exist. |
| `2` | Arguments are invalid or comparison could not be completed reliably. |

## Determinism guarantees

- Identical repository states and arguments produce identical results.
- Output order does not depend on filesystem enumeration order.
- No network service or language model participates in extraction or comparison.

