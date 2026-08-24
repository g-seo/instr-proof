# Quickstart: Validate Hardened Path and Discovery Behavior

## Automated validation

Prerequisites: Python 3.12+, Git, `uv`, and the implemented feature.

```sh
uv sync --locked --dev
uv run pytest tests/unit/test_extract.py
uv run pytest tests/integration/test_repository.py
uv run pytest tests/unit/test_compare.py
uv run pytest tests/integration/test_cli_diff.py
uv run pytest
uv run pytest
uv run pytest
./scripts/run-demo.sh
./scripts/validate-release.sh
```

All commands must pass and the three complete-suite runs must be identical. Verify `.github/workflows/ci.yml` retains Python 3.12, 3.13, and 3.14 test-matrix entries; CI remains the authority for executing all three versions.

## Fixture 1: root file regression

From the InstrProof checkout, create a disposable repository:

```sh
INSTRPROOF_ROOT="$(pwd)"
DEMO_DIR="$(mktemp -d /tmp/instrproof-root.XXXXXX)"
git -C "$DEMO_DIR" init -q
git -C "$DEMO_DIR" config user.email demo@example.com
git -C "$DEMO_DIR" config user.name Demo
printf 'Read `README.md`.\n' >"$DEMO_DIR/AGENTS.md"
printf '# Demo\n' >"$DEMO_DIR/README.md"
git -C "$DEMO_DIR" add .
git -C "$DEMO_DIR" commit -qm baseline
BASE_COMMIT="$(git -C "$DEMO_DIR" rev-parse HEAD)"
rm "$DEMO_DIR/README.md"
(cd "$DEMO_DIR" && uv --directory "$INSTRPROOF_ROOT" run instrproof diff --base "$BASE_COMMIT")
```

Expected: exactly one `PathExists` regression for `README.md`, status 1.

## Fixture 2: removed rule cannot hide regression

```sh
INSTRPROOF_ROOT="$(pwd)"
DEMO_DIR="$(mktemp -d /tmp/instrproof-rule.XXXXXX)"
git -C "$DEMO_DIR" init -q
git -C "$DEMO_DIR" config user.email demo@example.com
git -C "$DEMO_DIR" config user.name Demo
mkdir -p "$DEMO_DIR/docs" "$DEMO_DIR/src"
printf '{"instructions":["docs/ai-rules.md"]}\n' >"$DEMO_DIR/instrproof.json"
printf 'Use `src/service.py`.\n' >"$DEMO_DIR/docs/ai-rules.md"
printf 'service\n' >"$DEMO_DIR/src/service.py"
git -C "$DEMO_DIR" add .
git -C "$DEMO_DIR" commit -qm baseline
BASE_COMMIT="$(git -C "$DEMO_DIR" rev-parse HEAD)"
printf '{"instructions":[]}\n' >"$DEMO_DIR/instrproof.json"
rm "$DEMO_DIR/src/service.py"
(cd "$DEMO_DIR" && uv --directory "$INSTRPROOF_ROOT" run instrproof diff --base "$BASE_COMMIT")
```

Expected: the surviving `docs/ai-rules.md` is inspected and exactly one `PathExists(src/service.py)` regression appears, status 1.

## Fixture 3: coordinated repair passes

Continue from Fixture 2:

```sh
mkdir -p "$DEMO_DIR/src"
printf 'replacement\n' >"$DEMO_DIR/src/replacement.py"
printf 'Use `src/replacement.py`.\n' >"$DEMO_DIR/docs/ai-rules.md"
(cd "$DEMO_DIR" && uv --directory "$INSTRPROOF_ROOT" run instrproof diff --base "$BASE_COMMIT")
```

Expected: no regressions, status 0; the old identity retires through the existing coordinated-update rule.

## Additional checks

- Exact supported extension-bearing/allowlist names promote only with BASE evidence.
- `v1.0`, `python3.12`, arbitrary words, globs, placeholders, URLs, and fenced code do not.
- Different valid BASE/HEAD configs select their own normal sources.
- Either malformed config yields attributable status 2.
- HEAD-only rules create no baseline contract.
- Overlapping rules load each normalized source once and repeated results are identical.

See [contracts/cli.md](contracts/cli.md) and [data-model.md](data-model.md). Remove disposable fixture directories after validation.
