# Research: Reproducible Public Demo

## Public CLI invocation from an isolated repository

**Decision**: Invoke `uv run --project <absolute-project-root> instrproof` while the current directory is the temporary repository.

**Rationale**: `--project` selects the prepared InstrProof environment without making the checkout the analyzed repository. InstrProof still discovers the temporary repository from the process working directory, matching external use without direct imports.

**Alternatives considered**: Calling `.venv/bin/instrproof` assumes an environment location. Running from project root analyzes the wrong repository. Importing CLI or analysis functions violates the boundary.

## Immutable BASE identity

**Decision**: Commit the template once, create lightweight tag `demo-base`, record the commit, and verify the tag resolves to it before both comparisons.

**Rationale**: The symbolic name is presentation-friendly and manually reusable. Object verification prevents repair from passing because BASE moved.

**Alternatives considered**: Raw hashes are less readable. `HEAD` changes meaning. Mock data does not prove the product.

## Expected nonzero handling

**Decision**: Capture the broken command in an explicit conditional, preserve its real status and streams, then validate status 1 and exact diagnostics.

**Rationale**: Strict mode must not stop on the expected result, while `|| true` would erase whether status was 1, 2, or another failure.

**Alternatives considered**: Disabling error handling broadly is unsafe. Pipelines risk losing status. Treating 1 as runner failure breaks the story.

## Stable presentation output

**Decision**: Use fixed labels and status markers, bounded diffs, no default temporary path or commit hash, and one final path only for `--keep`.

**Rationale**: Default output becomes directly comparable and understandable. Retention requires a path only when the user owns inspection.

**Alternatives considered**: Shell tracing is noisy and leaks implementation detail. Broad normalization could hide drift. Hiding all commands weakens teaching value.

## Application health proof

**Decision**: Use one standard-library `unittest` and run `python -m unittest discover -s tests` at every stage.

**Rationale**: This proves ordinary health without dependencies or network. Updating its import models a real refactor while leaving the AI instruction stale.

**Alternatives considered**: pytest adds a template dependency. Syntax-only checks are less persuasive. An unrelated shell fixture weakens the Python story.

## Template minimality

**Decision**: Store only `AGENTS.md`, `src/auth/service.py`, and `tests/test_service.py`; create Git metadata only in the copied repository.

**Rationale**: The inline claim is the only instruction evidence, making one `PathExists` contract deterministic and avoiding nested Git state.

**Alternatives considered**: Manifests and extra docs add unrelated evidence. Generating everything in the runner makes the public input hard to inspect.

## Cleanup and retention

**Decision**: Use one unique temporary root, strict target validation, exit/signal traps, default deletion, and an initialization flag that permits keep only after Git initialization succeeds.

**Rationale**: Cleanup covers every exit without broad deletion risk. The guard avoids preserving unexplained partial setup while supporting meaningful inspection.

**Alternatives considered**: Always preserve leaves residue. Always delete blocks inspection. Repository-local temporary state violates isolation.

## Parent integrity

**Decision**: Retain the before/after Git porcelain comparison and also enumerate the parent with NUL-delimited `git ls-files --cached --others --exclude-standard`, recording a canonical snapshot of every visible path, file type, SHA-256 digest of complete regular-file bytes, exact symlink target, and relevant executable mode. Compare the complete snapshot on every exit. Tests add a collision-resistant pre-existing untracked byte sentinel and a stable tracked-file byte assertion.

**Rationale**: Porcelain alone cannot detect content changes to an already-untracked file or to an already-modified tracked file whose status remains unchanged. Combining status with an argument-safe path inventory and content/type/mode identity detects creation, deletion, replacement, byte mutation, link retargeting, and executable-mode drift without depending on timestamps or sizes. Ignored caches and environments stay outside the contract unless directly targeted.

**Alternatives considered**: Requiring a clean checkout rejects normal development. Porcelain-only and tracked-only checks miss pre-existing content mutation. Modification times and sizes are not content proof. Snapshotting ignored environments and caches adds noise outside FR-002's Git-visible boundary.

## Failure-path tests

**Decision**: Use subprocess tests with test-local `PATH` shims for missing or misbehaving external commands; add no runner override.

**Rationale**: Success always exercises real Git, uv, and InstrProof while failures remain deterministic without evaluated strings or injection hooks.

**Alternatives considered**: Public command overrides expand risk. Mutating the static template risks the checkout. Unit shell fragments miss orchestration.

## Feature 006 boundary

**Decision**: Do not reuse or modify `scripts/validate-release.sh`; share only existing CLI behavior and safe temporary-directory principles.

**Rationale**: Release fixtures prove artifact behavior, while this feature tells a public product story. Independence prevents cross-purpose coupling.

**Alternatives considered**: A shared fixture library adds unjustified abstraction. Calling release validation produces the wrong scenario and output.
