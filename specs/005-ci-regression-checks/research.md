# Research: CI Regression Checks

## Existing comparison seam

**Decision**: Call `compare_repository(repository, base_ref)` once for both normal and CI diff modes, then pass its `ComparisonResult` to the selected formatter.

**Rationale**: The function already resolves BASE, loads shared discovery configuration, extracts both claim types, promotes BASE-valid contracts, evaluates claim survival and HEAD evidence, and returns the baseline count plus every regression. This exactly matches the required architectural flow and prevents semantic drift.

**Alternatives considered**:

- A separate CI analysis function was rejected because it would duplicate the regression pipeline.
- Spawning `instrproof diff` and parsing its text was rejected because human-readable output is not an application interface and lacks the baseline count in the passing message.
- Reconstructing contracts in the CLI was rejected because it would cross the established application/domain boundary.

## Structured result and CI classification

**Decision**: Reuse `ComparisonResult` as the completed-analysis result. Derive CI PASS or REGRESSION directly from whether `regressions` is empty; reserve status `2` for exceptions that prevent a result.

**Rationale**: `ComparisonResult` already includes `baseline_contract_count` and the full regression tuple. A second result object would repeat the same data. Named CLI constants or a small private status enum may document `0`, `1`, and `2`, but must not become another analysis model.

**Alternatives considered**:

- Adding PASS/REGRESSION/ERROR to the domain model was rejected because analysis errors are exceptional failures, not completed comparison data.
- Returning the number of regressions was rejected because multiple regressions must always map to status `1`.
- Wrapping the result in a provider-specific CI model was rejected as unnecessary indirection.

## Deterministic regression order

**Decision**: Preserve the order already produced by `compare_contracts()`: contracts are sorted by `ContractIdentity`, whose declared order is normalized source, `ContractType`, then normalized target. The representative HEAD occurrence is already chosen deterministically by line and written claim.

**Rationale**: This order satisfies the preferred stable domain fields and is already covered by mixed-contract and multiple-regression tests. Consuming the tuple as returned avoids a competing presentation order.

**Alternatives considered**:

- Sorting by diagnostic line first was rejected because line is not contract identity.
- Relying on set, map, filesystem, or extraction order was rejected because those are incidental.
- Sorting a second time in the CI formatter was rejected because the application pipeline already guarantees order.

## Diagnostic location

**Decision**: Display `head_location` when its line is available; otherwise display the normalized instruction source alone. Do not use location for deduplication or identity.

**Rationale**: The regression describes a surviving HEAD claim, so its current location is the most actionable build diagnostic. `Regression` already marks locations as comparison-excluded diagnostic fields.

**Alternatives considered**:

- Using BASE location was rejected because it may be stale after harmless instruction movement.
- Requiring a line was rejected because the model explicitly permits absent location data.
- Adding line to identity was rejected because it contradicts established semantics.

## Exact BASE resolution and missing-ref diagnostics

**Decision**: Keep the existing `git rev-parse --verify --end-of-options <ref>^{tree}` resolution. Add a narrow `BaseReferenceError` subtype that retains the exact user-supplied ref and underlying repository detail. CI formats actionable missing-ref guidance from the typed error; normal diff retains its existing generic `RepositoryError` handling and observable format.

**Rationale**: The current Git command verifies exactly the requested commit-ish/tree and already performs no merge-base guessing or network fetch. The subtype lets CI distinguish resolution failure from later repository-analysis failures without parsing Git's localized or version-dependent stderr.

**Alternatives considered**:

- Prechecking in the CLI was rejected because it would duplicate repository behavior and create a time-of-check/time-of-use split.
- Parsing Git stderr was rejected as unstable.
- Falling back to another revision or automatically fetching was rejected by the requirements.

## Error mapping and output channel

**Decision**: In CI mode, map all `RepositoryError` failures to status `2` with a concise `InstrProof` analysis-error diagnostic on stderr. Also catch unexpected exceptions at the CI boundary, emit a generic internal-analysis message without exception detail or traceback, and return `2`. Preserve the existing non-CI diff exception behavior and output when `--ci` is absent.

**Rationale**: Repository errors are already the explicit expected analysis-failure hierarchy. A final CI-boundary catch ensures an unexpected failure cannot be confused with a regression and avoids leaking sensitive details, while keeping the catch outside the regression engine.

**Alternatives considered**:

- Converting failures into an empty or synthetic regression result was rejected because it conflates incomplete analysis with PASS or REGRESSION.
- Catching exceptions inside comparison functions was rejected because it would hide domain and repository failures.
- Printing stack traces by default was rejected as noisy and potentially sensitive.

## CI text format

**Decision**: Add a pure `format_ci_result(ComparisonResult)` formatter with exact PASS and REGRESSION layouts documented in `contracts/cli.md`. Each regression is a two-line block: source with optional line, then `ContractType(normalized-target)`. Use singular/plural grammar based on the exact total.

**Rationale**: A pure formatter is easy to test, has no analysis side effects, consumes every regression once, and produces concise stable logs without dependencies.

**Alternatives considered**:

- Reusing normal output verbatim was rejected because PASS lacks the baseline count.
- ANSI color and terminal detection were rejected because build output must be equivalent across environments.
- JSON or SARIF was rejected as out of scope.

## Test organization

**Decision**: Add focused CI integration tests in `tests/integration/test_cli_ci.py`, using existing local Git fixtures and monkeypatch failure injection. Retain and run the complete existing suite. Add pure formatter tests only if they improve failure localization without duplicating integration assertions.

**Rationale**: Existing fixtures create isolated repositories with no network dependency. End-to-end `main()` tests observe exact stdout/stderr and returned status while existing unit tests continue to prove comparison semantics.

**Alternatives considered**:

- Network-backed GitHub Actions tests were rejected as flaky and unnecessary.
- A new fixture framework was rejected because existing fixtures already cover the required states.

## GitHub Actions checkout behavior

**Decision**: Document checkout with sufficient history and an explicit local `origin/main` ref before running `instrproof diff --base origin/main --ci`. State that missing refs, including shallow-checkout omissions, are status `2`; InstrProof does not fetch.

**Rationale**: This makes repository preparation an explicit workflow responsibility and avoids hidden network activity. Both statuses `1` and `2` naturally fail a required step while their meanings remain distinct.

**Alternatives considered**:

- GitHub API integrations and annotations were rejected as out of scope.
- An InstrProof-managed fetch was rejected because it expands security, credentials, and network responsibilities.
