# InstrProof

> Regression testing for AI coding instructions.

InstrProof detects stale repository references in `AGENTS.md`, `CLAUDE.md`, and other AI coding instruction files.

* **Path & Link Contracts** — recognizes repository paths and local Markdown links backed by repository evidence.
* **Package Script Contracts** — recognizes referenced `npm`, `pnpm`, and `yarn` scripts.
* **Regression Detection** — catches BASE-valid instruction references that become stale after code changes.
* **Deterministic CI Checks** — uses repository evidence instead of LLM interpretation.

## Why?

AI coding instructions depend on repository facts. After a refactor, those references can become stale even while application tests continue to pass.

```text
src/auth/service.py
        ↓ refactor
src/auth/auth_service.py

Application tests   ✓
AGENTS.md            stale
InstrProof           ✗
```

InstrProof turns these repository-backed references into regression-testable contracts.

## Example

`AGENTS.md`:

```markdown
Authentication logic is implemented in `src/auth/service.py`.
```

Before the refactor:

```text
$ instrproof check

Found 1 verified instruction contract:
PathExists  source=AGENTS.md:1  target=src/auth/service.py  current=present
```

After moving the file without updating `AGENTS.md`:

```text
$ instrproof diff --base demo-base --ci

InstrProof ✗

1 instruction contract regression

AGENTS.md:1
PathExists(src/auth/service.py)
```

After updating the instruction:

```text
$ instrproof diff --base demo-base --ci

InstrProof ✓

1 baseline contracts checked.
No instruction contract regressions.
```

Run the complete scenario:

```bash
./scripts/run-demo.sh
```

The demo script requires `uv` and a Unix-like shell environment.

## Usage

```bash
python -m pip install instrproof

instrproof check
instrproof explain AGENTS.md:1
instrproof diff --base origin/main
instrproof diff --base origin/main --ci --require-contracts
```

Python 3.12+ and Git are required.

## GitHub Actions

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0

- uses: actions/setup-python@v5
  with:
    python-version: "3.12"

- run: python -m pip install instrproof

- run: instrproof diff --base origin/main --ci --require-contracts
```

## License

Apache License 2.0
