# Research: Require Baseline Contracts

## Argument ownership

**Decision**: Add `--require-contracts` as a `store_true` option on the existing diff subparser only.

**Rationale**: Subparser ownership automatically exposes the option in diff help, accepts normal argparse ordering among diff options, and rejects it for check and explain without custom validation. The default remains false.

**Alternatives considered**: A root-level option would incorrectly expose it to every command. A configuration file or environment variable is out of scope and would create precedence rules.

## Policy evaluation boundary

**Decision**: Evaluate the option in `cli.main()` immediately after the existing `compare_repository()` call and its exception handlers, before normal or CI result formatting.

**Rationale**: At this point one complete `ComparisonResult` exists, existing failures have already returned status 2, and the CLI can choose presentation/status without changing analysis. The comparison is invoked exactly once.

**Alternatives considered**: Passing the flag into comparison would mix CLI policy with domain analysis. Checking before analysis cannot know the promoted count. Running a second analysis wastes work and could produce inconsistent snapshots.

## Authoritative coverage count

**Decision**: Read `ComparisonResult.baseline_contract_count` directly and require only that it be nonzero.

**Rationale**: The field already represents the exact deduplicated promoted-contract count. Recounting claims or regressions would change semantics and mishandle duplicate identities.

**Alternatives considered**: Counting extracted claims includes unpromoted or duplicate claims. Counting regressions says nothing about baseline coverage. A new coverage model is unnecessary.

## Failure representation and output

**Decision**: Treat zero count under the option as a CLI analysis/policy failure returning 2, not a regression. Print the specified normal literal or reuse `format_ci_error()` with the specified sentence for CI; write only to stderr and return before `format_result()` or `format_ci_result()`.

**Rationale**: This preserves regression meaning and guarantees no PASS, count, or partial-success output. Reusing the established CI error envelope preserves presentation consistency while yielding the exact required text.

**Alternatives considered**: A synthetic regression corrupts contract semantics and status 1. Printing then overriding the status leaks success output. A new formatter abstraction is unnecessary for one fixed policy error.

## Error precedence

**Decision**: Leave all existing BASE, repository/configuration, and unexpected-error handlers unchanged and place the policy check after them.

**Rationale**: Exceptions never produce a result, so they cannot reach the count check. Normal mode retains its existing exception behavior, including current handling of unexpected failures; CI retains sanitized internal-error output.

**Alternatives considered**: Catching more broadly for this feature changes existing behavior. Inferring zero coverage from an exception masks the attributable cause.

## Concrete analysis-failure fixtures

**Decision**: Cover unavailable BASE, malformed BASE configuration, malformed HEAD configuration, unreadable instruction source, malformed required repository data, and unexpected CI failure as separately named strict-mode cases. Use existing real-repository fixtures where they already expose the failure and narrow CLI-boundary stubs for failures that cannot be portably induced through filesystem permissions.

**Rationale**: Naming each required cause prevents a generic “representative failure” from silently omitting a precedence case. Boundary stubs preserve deterministic cross-platform tests while still proving that no incomplete analysis reaches the zero-contract policy.

**Alternatives considered**: One generic `RepositoryError` fixture does not demonstrate the required breadth. Permission-bit-only unreadability tests are unreliable across platforms and privileged test environments.

## Nonempty compatibility

**Decision**: For every positive baseline count, fall through to the exact existing formatter and regression-based return expression.

**Rationale**: No duplicated PASS/regression logic means output, ordering, exact counts, and statuses remain identical with or without the option.

**Alternatives considered**: Separate strict-mode formatting creates snapshot drift. Rebuilding a result risks semantic changes.

## Determinism and single-analysis verification

**Decision**: Use existing deterministic repository fixtures, repeat representative multi-contract output three times, and add a monkeypatched call counter for a strict invocation.

**Rationale**: Exact repeated output proves the flag introduces no ordering branch; a direct call count proves comparison remains single-pass.

**Alternatives considered**: Timing or indirect mock assertions cannot reliably prove one invocation. Repeating every suite three times would add cost without more focused evidence.

## Distribution equivalence

**Decision**: Extend the existing wheel/sdist smoke capture with the same four strict-mode scenarios: non-regressing status 0, confirmed-regression status 1, zero-contract requirement status 2, and unavailable-BASE analysis-error status 2. Capture status, stdout, and stderr for every scenario, then use the current recursive result-directory comparison.

**Rationale**: Executing installed console scripts validates parser and runtime behavior across every defined outcome, while byte-for-byte captured outputs and statuses prove artifact equivalence.

**Alternatives considered**: PASS and zero-only smoke coverage misses regression fall-through and pre-result error precedence. Archive inspection alone cannot verify command behavior. Separate artifact expectations could drift without direct comparison.

## Supported-runtime completion evidence

**Decision**: Retain the existing Python 3.12, 3.13, and 3.14 CI matrix and require a successful complete-suite result for every matrix entry before feature completion.

**Rationale**: Local execution on one interpreter and static workflow inspection prove neither syntax nor behavior on the other supported runtimes. Successful matrix jobs provide the required evidence without changing CI structure.

**Alternatives considered**: Merely confirming version strings in the workflow is insufficient. Adding a new local multi-interpreter harness or changing CI structure is unnecessary.

## Documentation and demo compatibility

**Decision**: Explain default empty success, strict status 2, recommended CI use, and the nonempty-only guarantee in README; update only the consumer GitHub Actions command. Keep `scripts/run-demo.sh` and its displayed commands unchanged and run its existing exact-output test.

**Rationale**: Adopters receive a copy-and-run strict workflow without altering the public demonstration story.

**Alternatives considered**: Enabling strict mode in the demo is unnecessary and risks visible output changes. Describing the option as coverage completeness would overstate its guarantee.

## Validation scope

**Decision**: Add focused CLI parsing, normal/CI behavior, nonzero compatibility, deduplication, separately named precedence failures, single-call, documentation, and four-outcome artifact tests; then run the full suite, unchanged demo, release validation, and require successful existing Python 3.12–3.14 matrix jobs.

**Rationale**: This covers every observable requirement at the closest existing boundary and produces distribution/runtime evidence without modifying CI structure.

**Alternatives considered**: Unit-only parser tests miss streams and installed entry points. Changing the CI matrix is unnecessary because all supported versions are already present.
