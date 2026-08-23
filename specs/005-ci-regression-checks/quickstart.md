# Quickstart: Validate CI Regression Checks

## Prerequisites

- Python 3.12 or newer
- Git
- `uv`
- The feature implementation completed from the tasks derived from this plan

Install the development environment from the repository root:

```sh
uv sync --dev
```

## 1. Run focused CI tests

```sh
uv run pytest tests/integration/test_cli_ci.py
```

The focused suite must validate the exact [CLI contract](contracts/cli.md):

- no regressions: baseline count, zero-regression message, status `0`
- one PathExists regression: one diagnostic, status `1`
- one PackageScriptExists regression: one diagnostic, status `1`
- multiple mixed regressions: exact count, every item once, status `1`
- repeated identical comparisons: byte-equivalent stdout and stable identity ordering
- invalid or checkout-missing BASE: actionable stderr, status `2`
- malformed required repository data and injected repository-analysis failure: status `2`
- injected unexpected comparison failure: generic CI analysis error and status `2`

All Git repositories used by the tests are local temporary fixtures. No test may fetch from a network remote.

## 2. Run the complete compatibility suite

```sh
uv run pytest
```

All existing tests must pass unchanged, especially:

- PathExists and PackageScriptExists extraction and validation
- instruction discovery and configuration
- baseline promotion and baseline count
- contract identity and diagnostic-location independence
- claim updates/removals and survival behavior
- deterministic mixed regression ordering
- non-CI `instrproof diff` exact output
- `instrproof check` and `instrproof explain`

## 3. Manual PASS validation

From a clean repository state whose current checkout satisfies its BASE contracts:

```sh
uv run instrproof diff --base HEAD --ci
printf 'status=%s\n' "$?"
```

Expected shape:

```text
InstrProof ✓

N baseline contracts checked.
No instruction contract regressions.
status=0
```

`N` must equal the existing comparison's exact baseline-contract count.

## 4. Manual missing-BASE validation

```sh
uv run instrproof diff --base refs/remotes/origin/definitely-missing --ci
printf 'status=%s\n' "$?"
```

Expected: stderr identifies the exact unavailable ref, explains that it must exist locally, and the shell prints `status=2`. No regression count or regression diagnostic is printed.

## 5. Validate non-CI compatibility

```sh
uv run instrproof diff --base HEAD
uv run instrproof check
```

The first command must retain the established normal diff output rather than CI formatting. `check` must retain its established current-state output. Exercise an existing supported location with `explain` to verify that command is likewise unchanged.

## 6. Validate documented pull-request setup

Review the README workflow and confirm it:

1. checks out sufficient Git history,
2. makes the exact `origin/main` ref locally available,
3. installs InstrProof,
4. runs `instrproof diff --base origin/main --ci`, and
5. documents `0` as pass, `1` as confirmed regressions, and `2` as analysis failure.

The workflow is valid as a required check because both nonzero statuses fail the step while the output distinguishes their causes. InstrProof must not fetch or guess a BASE ref itself.

## Final validation

```sh
uv run pytest
git diff --check
git status --short
git diff
```

Do not claim completion unless the complete suite passes and the diff contains only feature-scoped implementation, tests, and documentation.
