# Data Model: Reproducible Public Demo

## Demo Template

Static input copied for every run.

- **Fields**: `AGENTS.md`; baseline target `src/auth/service.py`; replacement target `src/auth/auth_service.py`; one standard-library application test; exactly one supported `PathExists` claim.
- **Rules**: no Git metadata, nested repository, unrelated instruction source, path claim, or package-script claim; baseline test passes; baseline inspection returns the exact single contract; bytes remain unchanged.

## Demo Run

One invocation of the public runner.

- **Fields**: resolved project root, temporary/repository roots, retention flag, initialization flag, parent porcelain snapshots, canonical parent Git-visible snapshots, baseline commit, `demo-base`, current stage, overall status.
- **Relationships**: owns one Demo Repository, references one Demo Baseline, produces three ordered Stage Results, applies one Retention Choice.
- **Rules**: writes only below its temporary root; parent porcelain and canonical Git-visible state remain exactly equal on success, failure, and interruption; default exits remove state; keep preserves only initialized state and prints its path once; no child remains active.

## Parent Repository Snapshot

Canonical identity of every tracked or non-ignored untracked parent path returned by a NUL-delimited Git enumeration.

- **Fields per entry**: repository-relative path, file type, SHA-256 digest of complete regular-file bytes, exact symlink target when applicable, and relevant executable mode.
- **Aggregate fields**: exact ordered/canonical path set and the separate `git status --porcelain` output.
- **Rules**: before/after entries and porcelain output must be exactly equal; additions and deletions fail through path-set inequality; file replacement fails through type inequality; regular-file mutation fails through digest inequality; symlink retargeting fails through target inequality; executable-bit changes fail through mode inequality.
- **Exclusions**: Git-ignored files are excluded unless the runner directly targets them. Modification timestamps and file sizes are never used as equality evidence.

## Demo Repository

Mutable isolated template copy.

```text
Template copied
  -> Git initialized
  -> Baseline committed and tagged
  -> Broken refactor applied
  -> Instruction repaired
  -> Cleaned or retained
```

- `demo-base` resolves to the original baseline commit after tagging.
- Baseline: old source and old claim exist; tests pass.
- Broken: old source absent, replacement source and old claim exist, updated tests pass.
- Repaired: replacement source and new claim exist, old claim absent, tests pass.

## Instruction Claim

- **Type**: `PathExists`
- **Source**: `AGENTS.md`
- **Baseline target**: `src/auth/service.py`
- **Repaired target**: `src/auth/auth_service.py`
- **Evidence transition**: present at baseline, missing during broken refactor, present after coordinated repair.
- **Rules**: exactly one supported claim; broken comparison diagnoses the old target once; repair changes target rather than deleting source or claim.

## Stage Result

| Stage | Application test | InstrProof operation | Required result |
|---|---:|---|---|
| Baseline | 0 | `check` | One present old-target contract |
| Broken refactor | 0 | CI comparison to `demo-base` | Exactly one regression, status 1 |
| Repaired instruction | 0 | CI comparison to same BASE | No regressions, status 0 |

Each result contains its stable label, displayed change/command, test status, CLI streams/status, expected count, and BASE assertion where applicable.

## Retention Choice

- **Default**: delete all demo-created state on every exit.
- **Keep**: after repository initialization, preserve state and print one absolute location; user owns cleanup.
- **Rules**: unsupported options exit 2; keep never converts failure to success; pre-initialization failures are always cleaned.
