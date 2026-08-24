# Quickstart: Validate Required Baseline Contracts

## Automated validation

Prerequisites: Python 3.12+, Git, `uv`, and the implemented feature.

```sh
uv run pytest tests/integration/test_cli_diff.py
uv run pytest tests/integration/test_cli_ci.py
uv run pytest tests/integration/test_cli_installation.py
uv run pytest tests/integration/test_release_validation.py
uv run pytest tests/integration/test_reproducible_demo.py
uv run pytest tests/unit/test_readme_release_docs.py
uv run pytest
./scripts/run-demo.sh
./scripts/validate-release.sh
```

All commands must pass. Verify `.github/workflows/ci.yml` still runs the complete suite on Python 3.12, 3.13, and 3.14, and require a successful CI job for every version before completion. CI is authoritative for those distinct runtime executions; matrix inspection alone is insufficient.

## Fixture 1: default empty comparison remains successful

From the InstrProof checkout:

```sh
INSTRPROOF_ROOT="$(pwd)"
EMPTY_REPO="$(mktemp -d /tmp/instrproof-empty.XXXXXX)"
git -C "$EMPTY_REPO" init -q
git -C "$EMPTY_REPO" config user.email demo@example.com
git -C "$EMPTY_REPO" config user.name Demo
printf 'empty repository\n' >"$EMPTY_REPO/README.md"
git -C "$EMPTY_REPO" add README.md
git -C "$EMPTY_REPO" commit -qm baseline
(cd "$EMPTY_REPO" && uv --project "$INSTRPROOF_ROOT" run instrproof diff --base HEAD)
```

Expected stdout and status 0:

```text
No instruction contract regressions found.
```

Run the CI equivalent:

```sh
(cd "$EMPTY_REPO" && uv --project "$INSTRPROOF_ROOT" run instrproof diff --base HEAD --ci)
```

Expected: status 0 with exactly `0 baseline contracts checked.` and the existing PASS output.

## Fixture 2: strict empty comparison fails

Using Fixture 1:

```sh
(cd "$EMPTY_REPO" && uv --project "$INSTRPROOF_ROOT" run instrproof diff --base HEAD --require-contracts)
```

Expected: empty stdout, the exact lowercase requirement diagnostic on stderr, and status 2.

Run CI format:

```sh
(cd "$EMPTY_REPO" && uv --project "$INSTRPROOF_ROOT" run instrproof diff --base HEAD --ci --require-contracts)
```

Expected: empty stdout, the exact `InstrProof ✗` / `Analysis error:` requirement diagnostic on stderr, and status 2. Neither command prints a baseline count, regression count, or PASS text.

## Fixture 3: strict nonempty comparison preserves decisions

```sh
STRICT_REPO="$(mktemp -d /tmp/instrproof-strict.XXXXXX)"
git -C "$STRICT_REPO" init -q
git -C "$STRICT_REPO" config user.email demo@example.com
git -C "$STRICT_REPO" config user.name Demo
mkdir -p "$STRICT_REPO/src"
printf 'Use `src/app.py`.\n' >"$STRICT_REPO/AGENTS.md"
printf 'app\n' >"$STRICT_REPO/src/app.py"
git -C "$STRICT_REPO" add .
git -C "$STRICT_REPO" commit -qm baseline
(cd "$STRICT_REPO" && uv --project "$INSTRPROOF_ROOT" run instrproof diff --base HEAD --ci --require-contracts)
```

Expected: existing CI PASS output with exactly one baseline contract and status 0.

Remove the protected evidence and rerun:

```sh
rm "$STRICT_REPO/src/app.py"
(cd "$STRICT_REPO" && uv --project "$INSTRPROOF_ROOT" run instrproof diff --base HEAD --ci --require-contracts)
```

Expected: the existing single `PathExists(src/app.py)` regression output and status 1, identical to the result without the option.

## Additional checks

- Diff help contains `--require-contracts`; check and explain help do not.
- Check and explain reject the option under existing argparse behavior.
- Duplicate claims that promote to one identity satisfy the requirement with count 1.
- Multiple-contract output remains identical across three repeated invocations.
- Unavailable BASE, malformed BASE configuration, malformed HEAD configuration, unreadable instruction source, malformed required repository data, and unexpected CI failure each retain their old exact errors and never mention the zero-contract requirement.
- A strict invocation calls comparison exactly once.
- Installed wheel and source distribution produce byte-identical captured stdout/stderr and equal statuses for strict PASS (`0`), confirmed regression (`1`), zero-contract requirement failure (`2`), and unavailable-BASE analysis error (`2`).
- The README consumer workflow uses `instrproof diff --base origin/main --ci --require-contracts` while the public demo remains unchanged.

## Artifact and runtime completion gates

The release smoke fixture must install both artifacts and capture the same four strict-mode outcomes documented in [contracts/cli.md](contracts/cli.md). `./scripts/validate-release.sh` must compare every status, stdout file, and stderr file successfully; a PASS/zero-only subset is not sufficient.

After local validation, inspect the existing CI run and require successful complete-suite jobs for Python 3.12, 3.13, and 3.14. Do not mark the feature complete if any supported-version job is missing, skipped, or failing.

See [contracts/cli.md](contracts/cli.md) for exact output and [data-model.md](data-model.md) for the decision table. Disposable fixture directories may be removed after validation.
