# CLI Contract: Deterministic CI Diff

## Invocation

```text
instrproof diff --base BASE_REF --ci
```

`BASE_REF` is required and is resolved exactly by the existing repository comparison. `--ci` selects process-oriented presentation only. It does not change comparison inputs or regression decisions.

## Output channels

- Completed PASS and REGRESSION results are written to stdout.
- ANALYSIS ERROR diagnostics are written to stderr.
- Output contains no ANSI styling, timestamps, absolute repository paths, traversal-order data, or stack traces.

## PASS

Condition: comparison completed and `regressions` is empty.

Status: `0`

Exact layout, where `{baseline_count}` is the result's exact non-negative count:

```text
InstrProof ✓

{baseline_count} baseline contracts checked.
No instruction contract regressions.
```

The output ends with one newline. The wording remains the same for zero or one baseline contract to maximize output stability.

## REGRESSION

Condition: comparison completed and one or more regressions exist.

Status: `1`, regardless of count.

Exact layout:

```text
InstrProof ✗

{regression_count} instruction contract {regression|regressions}

{source_or_source_line}
{contract_type}({normalized_target})
```

Each additional regression is appended as another two-line block separated by one blank line. The output ends with one newline.

Field rules:

- `regression_count` is `len(result.regressions)`.
- Singular `regression` is used only for count `1`; otherwise `regressions` is used.
- `source_or_source_line` is the normalized instruction source followed by `:{head_line}` when `head_location.line` is available; otherwise it is the source alone.
- `contract_type` is the established display value (`PathExists` or `PackageScriptExists`).
- `normalized_target` is the target from `ContractIdentity` without re-normalization.
- Every tuple item is emitted exactly once.

## Deterministic ordering

The formatter preserves the order of `ComparisonResult.regressions`. The existing engine produces that tuple by ascending `ContractIdentity`:

1. normalized instruction source
2. contract type
3. normalized target

The engine's deterministic representative-occurrence selection supplies diagnostic line data. Line is not an identity field and is not a primary ordering field.

## ANALYSIS ERROR

Condition: the requested comparison does not produce a trustworthy `ComparisonResult`.

Status: `2`

For an unavailable BASE ref:

```text
InstrProof ✗

Analysis error: BASE reference '{base_ref}' is unavailable. Ensure the exact reference exists in the local checkout.
```

For another expected repository-analysis failure:

```text
InstrProof ✗

Analysis error: {actionable_repository_error}
```

For an unexpected internal analysis failure:

```text
InstrProof ✗

Analysis error: internal analysis failure.
```

Errors end with one newline and are not labeled or counted as regressions. Unexpected exception details and tracebacks are omitted from normal CI output.

## Compatibility

Without `--ci`, `instrproof diff --base BASE_REF` retains its current formatting, error handling, and statuses. `instrproof check` and `instrproof explain` do not accept or inspect CI mode and retain their existing contracts.
