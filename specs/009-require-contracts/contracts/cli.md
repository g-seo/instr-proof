# CLI Contract: Require Baseline Contracts

## Command grammar

Accepted:

```text
instrproof diff --base BASE_REF --require-contracts
instrproof diff --base BASE_REF --ci --require-contracts
```

The option is boolean, disabled by default, belongs only to diff, appears only in diff help, and follows existing argparse ordering rules for diff options.

Rejected under existing invalid-argument behavior:

```text
instrproof check --require-contracts
instrproof explain AGENTS.md:1 --require-contracts
```

Root help, check help, explain help, and `--version` retain existing behavior. No configuration-file or environment-variable equivalent exists.

## Evaluation contract

`compare_repository(repository, BASE_REF)` runs exactly once. Only after it returns a complete `ComparisonResult` does the CLI evaluate:

```text
require_contracts and baseline_contract_count == 0
```

The count is the result's existing exact deduplicated promoted-contract count. The requirement does not inspect claims, identities, evidence, or regressions independently.

## Exact zero-contract behavior

Without the option, existing behavior is unchanged.

Normal stdout, status 0:

```text
No instruction contract regressions found.
```

CI stdout, status 0:

```text
InstrProof ✓

0 baseline contracts checked.
No instruction contract regressions.
```

With the option, normal stdout is empty, stderr is exactly the following plus one terminating newline, and status is 2:

```text
error: no baseline instruction contracts were found; verify instruction discovery, supported claim syntax, and BASE evidence
```

With the option, CI stdout is empty, stderr is exactly the following plus one terminating newline, and status is 2:

```text
InstrProof ✗

Analysis error: no baseline instruction contracts were found. Verify instruction discovery, supported claim syntax, and BASE evidence.
```

Neither requirement-failure form prints a PASS message, baseline count, regression count, or partial result.

## Nonzero behavior

| Baseline contracts | Regressions | Flag | Status | Output |
|-------------------:|------------:|------|-------:|--------|
| 1+ | 0 | absent or enabled | 0 | Existing normal or CI PASS output unchanged |
| 1+ | 1+ | absent or enabled | 1 | Existing normal or CI regression output unchanged |

Exact baseline counts, regression decisions, formatting, locations, ordering, and diagnostics remain those of the existing formatters and completed result.

## Error precedence

If repository discovery or comparison does not return a complete result, the requirement is not evaluated. Existing behavior remains authoritative for:

- unavailable or invalid BASE references;
- malformed BASE configuration;
- malformed HEAD configuration;
- unreadable instruction sources;
- malformed required repository data;
- unexpected internal analysis failures.

Each retains its existing normal or sanitized CI diagnostic and status 2. None emits the zero-contract text.

Focused precedence validation separately covers unavailable BASE, malformed BASE configuration, malformed HEAD configuration, unreadable instruction source, malformed required repository data, and unexpected CI failure. Tests that cannot portably induce unreadability may substitute the existing repository-error boundary while retaining the exact established diagnostic.

## Installed artifact equivalence

The installed wheel and source distribution MUST receive identical arguments and repository state for each strict-mode outcome below. Their captured status, stdout, and stderr MUST be byte-identical:

| Outcome | Required status | Fixture |
|---------|----------------:|---------|
| Non-regressing comparison | 0 | One promoted baseline contract with present HEAD evidence |
| Confirmed regression | 1 | One promoted baseline contract with missing HEAD evidence |
| Contract requirement failure | 2 | Complete comparison with zero baseline contracts |
| Analysis error | 2 | Unavailable requested BASE reference |

Release validation compares all four result captures. Passing only archive inspection or a subset of outcomes does not satisfy artifact equivalence.

## Compatibility boundary

- No default behavior changes.
- Check, explain, and version are unchanged.
- `ComparisonResult`, contract types, identity, selection, extraction, discovery, evidence validation, claim survival, and regression detection are unchanged.
- Requirement failure is not a regression and introduces no regression record.
- Existing deterministic ordering is unchanged.
- Wheel, source distribution, and source checkout expose identical grammar, streams, and statuses.
- Feature completion requires successful complete-suite CI results on Python 3.12, 3.13, and 3.14; workflow-matrix inspection alone is not execution evidence.
- The public demo command and visible behavior remain unchanged.
