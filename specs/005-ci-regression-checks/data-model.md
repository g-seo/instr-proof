# Data Model: CI Regression Checks

This feature reuses the existing immutable comparison and regression values. CI classification and output are derived views; they do not alter contract identity or regression analysis.

## Existing entities reused unchanged

### ComparisonResult

Represents a successfully completed BASE/HEAD comparison.

| Field | Type | Rules |
|-------|------|-------|
| `baseline_contract_count` | non-negative integer | Exact number of distinct promoted BASE contracts evaluated by the existing engine |
| `regressions` | ordered tuple of `Regression` | Contains every regression; empty means completed analysis with no regressions |

Validation remains `baseline_contract_count >= 0`. The result is constructed only after analysis completes; errors do not produce a partial `ComparisonResult`.

### Regression

Represents one confirmed regression from the existing engine.

| Field | Type | CI use |
|-------|------|--------|
| `identity` | `ContractIdentity` | Required source, type, and target; authoritative order |
| `base_location` | optional `SourceLocation` | Existing diagnostic; not needed for CI identity or primary location |
| `head_location` | optional `SourceLocation` | Supplies current line when available |
| `base_evidence` | optional `EvidenceState` | Existing diagnostic; CI does not reinterpret it |
| `head_evidence` | optional `EvidenceState` | Existing diagnostic; CI does not reinterpret it |

Diagnostic fields remain excluded from equality and identity.

### ContractIdentity

The established identity and ordering key.

| Ordered field | Meaning |
|---------------|---------|
| `source` | Normalized repository-relative instruction source |
| `contract_type` | `PathExists` or `PackageScriptExists` |
| `target` | Normalized contract target |

The existing declared ordering is the CI ordering. Source line is not added.

## Narrow error extension

### BaseReferenceError

A subtype of the existing `RepositoryError`, raised only when exact BASE resolution cannot complete.

| Field | Type | Rules |
|-------|------|-------|
| `requested_ref` | string | Exact nonempty CLI value supplied to `--base`; retained for actionable CI output |
| `detail` | string | Underlying repository/Git failure context; normal error behavior may preserve it, while CI emits stable guidance |

This entity does not represent missing evidence and never appears in `ComparisonResult.regressions`.

## Derived CI classification

CI classification is not persisted and does not require a new analysis result model.

| State | Derivation | Exit status |
|-------|------------|-------------|
| PASS | A `ComparisonResult` exists and `regressions` is empty | `0` |
| REGRESSION | A `ComparisonResult` exists and `regressions` is nonempty | `1` |
| ANALYSIS ERROR | No trustworthy result exists because analysis raised an expected repository failure or unexpected exception | `2` |

Regression quantity never changes the REGRESSION status.

## Relationships

```text
requested BASE ref
       |
       v
exact repository resolution --failure--> BaseReferenceError --> ANALYSIS ERROR (2)
       |
       v
existing compare_repository pipeline
       |
       v
ComparisonResult --empty regressions----> PASS (0)
       |
       +-----------nonempty regressions--> REGRESSION (1)
                                              |
                                              v
                                  ordered CI diagnostic blocks
```

## Invariants

1. CI and non-CI modes consume the same `ComparisonResult` for the same successful comparison.
2. `--ci` is never passed into discovery, extraction, promotion, survival, validation, or comparison functions.
3. Every regression appears exactly once and in the tuple order returned by the existing engine.
4. The baseline count is read from `ComparisonResult`; it is never reconstructed in the formatter.
5. Analysis errors produce no PASS or REGRESSION classification and no partial regression listing.
6. Diagnostic line movement may change displayed location but never identity, regression selection, or primary ordering.

## State transitions

```text
START
  -> BASE_RESOLVED
  -> ANALYSIS_COMPLETED
       -> PASS        when regression count = 0
       -> REGRESSION  when regression count >= 1

START or BASE_RESOLVED
  -> ANALYSIS_ERROR   when required analysis cannot complete
```

PASS and REGRESSION are terminal completed-analysis states. ANALYSIS ERROR is a distinct terminal incomplete-analysis state.
