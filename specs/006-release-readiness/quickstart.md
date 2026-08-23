# Quickstart: Validate Release Readiness

## Prerequisites

- Linux, Git, uv, and Python 3.12
- A checkout of the feature implementation

Python 3.13 and 3.14 compatibility is exercised by CI and may be repeated locally when those interpreters are available.

## Run complete local validation

```sh
./scripts/validate-release.sh
```

Expected: a fresh locked dependency setup followed by successful named phases for tests, the single Python 3.12 build, metadata/archive checks, separate designated-Python-3.12 wheel and source-distribution installations, representative check/diff fixtures, and behavioral comparison, then status 0. Locked dependencies may come from configured indexes, but no InstrProof production release is installed or queried and nothing is uploaded. An unexpected failure stops at the named phase.

This proves the [distribution](contracts/distribution.md), [release validation](contracts/release-validation.md), and installed [CLI](contracts/cli.md) contracts.

## Verify CI compatibility

On a push or pull request require:

- Tests (Python 3.12)
- Tests (Python 3.13)
- Tests (Python 3.14)
- Build and validate distributions once on Python 3.12
- Validate wheel installation
- Validate source-distribution installation
- Compare artifact behavior

Expected: all existing and focused tests pass, the artifacts build once, and the transferred wheel and source distribution install separately and produce equal versions, stdout, stderr, and statuses for the shared fixtures.

## Verify an installed version directly

After installing either built artifact, change outside the repository and run:

```sh
instrproof --help
instrproof --version
python -I -c "import instrproof; print(instrproof.__version__)"
```

Expected: commands/import succeed; the CLI version after `instrproof ` equals the imported version, and the module resolves inside the clean environment.

Then use the representative fixture procedure documented by the release validator to run `check`, a passing `diff`, and a regression-producing `diff`. Expected: wheel and source-distribution environments produce identical stdout, stderr, and statuses, including the intentional regression status 1.

## Diagnose compatibility

```sh
uv sync --locked --dev
uv run pytest
```

Expected: the 250-test baseline plus focused release tests pass; existing command output/statuses match the [CLI contract](contracts/cli.md).

## Verify a manually published release

Only after a maintainer has published outside this feature, follow the README's post-publication procedure with the exact released version. It creates a clean environment, installs `instrproof==<released-version>` from production PyPI, and repeats help, version, representative check, and representative diff verification.

Expected: the installed package and CLI report the exact released version and representative commands retain their documented behavior. This check is deliberately separate from `scripts/validate-release.sh` and repository CI; neither pre-release path depends on production PyPI.

## Review public documentation

Confirm README has separate PyPI, GitHub, and local installation commands; a consumer CI example that selects a published version and materializes `origin/main`; statuses 0/1/2; a local validator independent of any published InstrProof release; a manual publication boundary; and a separate exact-version post-publication PyPI check. No credentials, Trusted Publishing, releases automation, or production upload belongs in project CI.
