# Contributing to InstrProof

Thank you for contributing to InstrProof.

InstrProof prioritizes deterministic, repository-evidenced behavior, high precision, and compatibility over broad natural-language inference.

## Before opening a change

Use GitHub Issues to:

* report a reproducible bug;
* propose a focused improvement;
* discuss behavior that may affect compatibility.

Search existing issues before creating a new one. Do not include secrets or private repository content.

## Development setup

Requirements:

* Python 3.12 or newer
* Git
* uv

Clone and prepare the project:

```sh
git clone https://github.com/g-seo/instr-proof.git
cd instr-proof
uv sync --locked --dev
```

## Testing

Run focused tests while developing:

```sh
uv run pytest path/to/test_file.py
```

Before submitting a pull request, run:

```sh
uv run pytest
./scripts/run-demo.sh
git diff --check
```

If packaging or installed CLI behavior changes, also run:

```sh
./scripts/validate-release.sh
```

## Pull requests

Keep each pull request focused on one problem.

A pull request should include:

* the problem being solved;
* the behavior being changed;
* tests added or updated;
* validation commands and results;
* any effect on CLI output or exit statuses.

New behavior should include automated coverage.

Existing command output, deterministic ordering, and exit-status meanings must not change unintentionally.

## Commit messages

Use concise Conventional Commit-style messages where practical:

```text
feat: add behavior
fix: correct behavior
test: cover behavior
docs: clarify behavior
```

## Project scope

Before proposing a large feature, review the supported contracts and non-goals in the README.

InstrProof intentionally does not attempt to understand every natural-language instruction. Proposals should preserve deterministic, repository-grounded validation unless there is a clear reason not to.
