# Data Model: Require Baseline Contracts

No persistent entity, contract type, identity field, analysis value, or `models.py` change is planned.

## Diff Policy Input

An invocation-local CLI value produced by argument parsing.

| Field | Type | Default | Scope | Rule |
|-------|------|---------|-------|------|
| `require_contracts` | Boolean | `false` | `diff` only | When true, a completed result must have a positive baseline count. |
| `ci` | Existing Boolean | `false` | `diff` only | Selects the existing CI presentation, including the requirement error envelope. |
| `base` | Existing reference string | Required | `diff` only | Passed unchanged to the single repository comparison. |

Check, explain, and version never receive `require_contracts` state.

## ComparisonResult (existing and unchanged)

| Field | Feature use | Invariant |
|-------|-------------|-----------|
| `baseline_contract_count` | Sole authority for nonempty baseline coverage | Existing exact count of deduplicated promoted BASE identities. |
| `regressions` | Existing completed-comparison decision | Never modified or supplemented by the requirement. |

The feature does not reconstruct, wrap, or mutate the result.

## Derived Requirement Outcome

A transient CLI decision, not a domain model.

```text
complete ComparisonResult
 + require_contracts
 -> if enabled and baseline_contract_count == 0: requirement failure
 -> otherwise: existing result formatting and regression status
```

| Analysis | Count | Regressions | Flag | Outcome |
|----------|------:|------------:|------|---------|
| Complete | 0 | 0 | false | Existing PASS, status 0 |
| Complete | 0 | 0 | true | Requirement failure, status 2 |
| Complete | 1+ | 0 | any | Existing PASS, status 0 |
| Complete | 1+ | 1+ | any | Existing regression result, status 1 |
| Failed | unavailable | unavailable | any | Existing analysis error, status 2 |

## Contract Requirement Failure

| Attribute | Normal mode | CI mode |
|-----------|-------------|---------|
| Classification | Explicit coverage/analysis failure | Explicit coverage/analysis failure |
| Status | 2 | 2 |
| stdout | Empty | Empty |
| stderr | Lowercase `error:` diagnostic | Existing InstrProof failure heading plus `Analysis error:` |
| Regression object | None | None |
| Baseline count output | None | None |

## State transitions

```text
parse diff arguments
 -> discover repository
 -> compare_repository(repository, base) exactly once
    -> existing failure: existing diagnostic + status 2
    -> complete ComparisonResult
       -> strict and count == 0: exact requirement error + status 2
       -> otherwise: existing formatter + existing regression decision
```

## Invariants

- The policy is evaluated only for a complete result.
- Existing errors return before policy evaluation and retain precedence.
- Duplicate claims remain governed by existing promotion and identity deduplication.
- Positive counts never select a new output or status path.
- Requirement failure never creates a synthetic regression.
- The option cannot affect extraction, discovery, evidence, survival, identity, ordering, or comparison semantics.
- Wheel, source distribution, and checkout execution derive the same policy outcome from identical arguments and repository state for strict PASS, confirmed regression, zero-contract requirement failure, and pre-result analysis error.
