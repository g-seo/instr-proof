# CLI Contract: Inspection and Diagnostics

## `instrproof check`

```text
instrproof check
```

No BASE argument is accepted. Successful rows are sorted by existing ContractIdentity:

```text
Found 2 verified instruction contracts:
PackageScriptExists  source=AGENTS.md:7  target=typecheck  current=present
PathExists  source=packages/auth/AGENTS.md:3  target=src/auth/service.py  current=present
```

The source line is the deterministic representative occurrence. Repeated equal identities count once; different sources remain distinct.

Zero is successful:

```text
Found 0 verified instruction contracts.
```

| Status | Meaning |
|---|---|
| `0` | Inspection completed, including zero verified contracts |
| `2` | Invalid arguments or analysis failure |

## `instrproof explain <source>:<line>`

```text
instrproof explain AGENTS.md:37
instrproof explain packages/auth/AGENTS.md:12
```

The final colon separates the normalized full source and positive line. Exact matching returns every distinct supported identity on that line in identity order.

```text
Contract

Source
  AGENTS.md:37

Type
  PackageScriptExists

Target
  typecheck

Evidence
  package.json:scripts.typecheck

CURRENT
  MISSING
```

CURRENT is PRESENT or MISSING. A missing occurrence is explainable but absent from check. No BASE/HEAD fields appear.

| Status | Meaning |
|---|---|
| `0` | One or more occurrences explained |
| `1` | Valid location matched no supported occurrence |
| `2` | Invalid selector or analysis failure |

No-match is a clear normal user outcome. Invalid input and analysis failures follow the existing `error:` stderr convention. Failures never appear as MISSING.

## Existing diff compatibility

`instrproof diff --base <BASE_REF>` retains its exact arguments, promotion, regression semantics, output, ordering, errors, and statuses. New commands neither invoke it nor parse its output.
