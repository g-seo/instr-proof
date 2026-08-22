# Quickstart: Validate Inspection and Diagnostics

## Automated validation

Prerequisites: Python 3.12+, Git, `uv`, and the completed implementation.

```sh
uv sync --dev
uv run pytest
```

Focused runs:

```sh
uv run pytest tests/unit/test_models.py tests/unit/test_compare.py
uv run pytest tests/integration/test_cli_inspection.py
uv run pytest tests/integration/test_cli_diff.py
uv run pytest tests/integration/test_repository.py tests/integration/test_performance.py
```

Record the existing 195 tests as the pre-feature baseline; the final suite must contain those unchanged cases plus new feature tests.

## Current analysis outcomes

Use supported path and package-script claims with present evidence, repeat with missing evidence, and include ambiguous/unsupported prose.

Expected: structured analysis contains PRESENT and MISSING supported occurrences, excludes unsupported text, and raises an analysis error for malformed required evidence rather than returning another state.

## Check

Create valid claims in root, nested, and configured sources, including duplicate identities and equal targets in different sources. Run `instrproof check`.

Expected: only PRESENT identities appear, one row per identity, different sources remain distinct, source paths/representative lines are correct, order is deterministic, and total is exact. A repository with only missing/unsupported candidates reports zero and status 0.

## Explain

Run exact locations for present and missing path/script occurrences:

```sh
instrproof explain AGENTS.md:1
instrproof explain packages/auth/AGENTS.md:1
```

Expected: source/location, type, normalized target, exact evidence reference, and CURRENT PRESENT or MISSING. Missing matches remain absent from check.

## Lookup boundaries

- Multiple distinct candidates on one line all appear once in identity order.
- Repeated equal claims on different lines count once in check, but either line is explainable.
- Moving a claim changes lookup location, never identity.
- Nested/configured full paths match exactly; basenames do not cross-match.
- Missing source, unsupported-text line, or no occurrence returns clear status 1.
- Malformed, absolute, escaping, nonnumeric, or zero-line selectors return error status 2.

## Errors and lazy evidence

Use malformed root package data with a package occurrence that requires inspection: expect an analysis error and status 2, never MISSING. A path-only operation must not parse unrelated malformed package data.

## Deterministic performance fixture

Use the integration fixture that creates exactly 100 discovered instruction documents and 1,000 combined supported candidates on local temporary storage. The test records elapsed monotonic time and requires completion within 5 seconds; document the Python/Git/platform details in failure output so slower environments can diagnose rather than silently weaken the criterion.

## Diff compatibility

Run existing passing, regression, mixed-contract, discovery, error, and performance cases with `instrproof diff --base HEAD`.

Expected: all pre-feature expected output and statuses remain unchanged, and new outputs contain no BASE/HEAD context.
