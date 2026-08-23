# Public Contract: Reproducible Demo Runner

## Invocation

```text
<instrproof-root>/scripts/run-demo.sh
<instrproof-root>/scripts/run-demo.sh --keep
```

Only no arguments or exactly `--keep` are accepted. Anything else prints concise usage to stderr and exits 2 without starting the demo.

## Prerequisites

Supported Linux, Git, uv, Python 3.12+, synchronized project dependencies, and the complete static demo template. Missing prerequisites fail nonzero with an attributable message. The runner performs no dependency download or published-package query.

## Stable stages

These labels appear exactly once and in order:

```text
[1/3] Baseline: instruction matches repository
[2/3] Refactor: tests pass, instruction is stale
[3/3] Repair: instruction updated
```

Important actions are preceded by compact commands or change descriptions. Routine setup, dependency logs, environment dumps, and default temporary paths are omitted.

## Baseline

After creating `demo-base`, the runner executes application tests and `instrproof check`.

Required: both status 0; exactly one verified contract; `PathExists`; source `AGENTS.md`; target `src/auth/service.py`; present evidence. Any mismatch fails.

## Broken refactor

The source moves to `src/auth/auth_service.py`, test code is updated, `AGENTS.md` remains unchanged, relevant changes are displayed, and application tests still pass. Then the runner executes:

```text
instrproof diff --base demo-base --ci
```

Required: BASE resolves to the recorded commit; application status 0; comparison status 1 displayed as `Broken comparison status: 1`; empty stderr; exactly one regression; source `AGENTS.md`; exactly one `PathExists(src/auth/service.py)`.

Status 1 is expected. Status 0, 2, another status, or diagnostic mismatch fails the overall run.

## Repair

The existing instruction target changes to `src/auth/auth_service.py`; the file, claim, and BASE remain; the instruction diff is shown; application tests pass; the same comparison runs.

Required: identical BASE; status 0 displayed as `Repaired comparison status: 0`; empty stderr; `1 baseline contracts checked.`; `No instruction contract regressions.`; new claim exists and old claim does not.

## Completion

Successful output ends by explaining that ordinary tests passed around the refactor, the unchanged AI instruction became stale, InstrProof alone produced the expected CI failure, and coordinated instruction repair restored success. Overall status is 0 only after every assertion and isolation check passes.

## Cleanup and retention

Default runs remove generated state on success, failure, and interruption, print no path, leave no process, and leave the parent/template unchanged. Parent immutability requires exact equality of both `git status --porcelain` and a canonical before/after snapshot of every tracked and non-ignored untracked path, including path set, file type, complete-byte digest, symlink target, and relevant executable mode. Ignored files are outside this comparison unless directly targeted; timestamps and sizes are not accepted as content proof.

Keep mode preserves initialized state and `demo-base`, retains failure status if applicable, and prints exactly one final line:

```text
Retained demo repository: /absolute/path
```

## Failure reporting

Unexpected failures write `Demo failed during <stage>:` with concise context to stderr and exit nonzero. Expected status 1 is captured explicitly, never hidden by unconditional success. Commands are fixed and argument-safe; user shell text is never evaluated.
