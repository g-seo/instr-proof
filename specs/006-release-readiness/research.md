# Research: Release-Ready Distribution

## Version source

**Decision**: Keep `src/instrproof/__init__.py::__version__` as the sole authored version. Declare the PEP 621 version dynamic and configure Hatchling to read that file; use the same imported value for argparse's root `--version` action.

**Rationale**: Hatchling can extract the literal without importing the package. Built metadata, package imports, and CLI output cannot drift while the existing public interface remains stable.

**Alternatives considered**: A static duplicate risks drift. `importlib.metadata` changes checkout behavior. Custom argument interception is less idiomatic than argparse's version action.

## Package metadata and licensing

**Decision**: Use the Apache-2.0 SPDX expression and explicit `LICENSE` declaration, README, supported Python classifiers, repository-evidenced author data, and canonical Repository/Issues URLs. Omit the deprecated license classifier.

**Rationale**: Modern Core Metadata identifies both the precise expression and distributed license text. The canonical remote is `https://github.com/g-seo/instr-proof`.

**Alternatives considered**: A legacy license table or classifier alone is less precise and may conflict with current standards.

## Hatchling artifact contents

**Decision**: Explicitly configure the wheel package as `src/instrproof` and define an auditable source-distribution inclusion set. Validate semantic invariants rather than every archive member.

**Rationale**: Explicit selection protects the src layout and required release files while focused assertions avoid coupling tests to harmless backend-generated files or ordering.

**Alternatives considered**: Auto-discovery is less auditable. Exact archive snapshots are brittle. Force-including existing in-tree files is unnecessary.

## Metadata and archive validation

**Decision**: Add Twine as a development-only dependency and run strict checks against both artifacts, supplemented by a standard-library ZIP/TAR and email-metadata inspector.

**Rationale**: Twine validates metadata and README rendering but not required package members, entry points, or license placement. Direct non-extracting inspection closes those gaps without a release framework.

**Alternatives considered**: Source-only validation does not prove built output. Wheel-only tools miss the source distribution. Hand-validating all metadata duplicates standards-aware tooling.

## Clean artifact installation

**Decision**: Install wheel and source distribution by explicit path into separate temporary environments. Run smoke checks from a neutral directory, remove inherited `PYTHONPATH`, invoke exact environment executables, and require the imported module to reside inside the environment.

**Rationale**: A changed directory alone cannot prevent editable installs or environment variables from masking missing artifact contents. Separate environments attribute failures correctly.

**Alternatives considered**: Reusing one environment leaves cross-artifact state. Checkout-root tests risk false positives. Metadata-only checks do not prove execution.

## Cross-artifact behavioral equivalence

**Decision**: Exercise each installed artifact against the same temporary Git fixtures: successful `check`, passing `diff` with status 0, and regression-producing `diff` with status 1. Capture and compare stdout, stderr, and status alongside help/version/import results.

**Rationale**: Import and entry-point smoke checks cannot prove that wheel and source distribution expose equivalent real commands. Fixed fixtures test the distributed analysis path without changing its semantics and allow expected domain status 1 to be distinguished from validator failure.

**Alternatives considered**: Comparing only archive members misses runtime defects. Running against the project checkout risks source leakage. Treating every nonzero command as a failed smoke test would incorrectly reject the required regression fixture.

## Pre-publication and post-publication boundaries

**Decision**: Pre-release validation may resolve locked development/build dependencies from configured indexes, but it never installs or queries an InstrProof release from production PyPI, uploads artifacts, or requires production credentials. A separate manual post-publication check installs the exact released version from PyPI and repeats representative CLI validation.

**Rationale**: The repository can guarantee the locally built artifacts without substituting an older published package. Dependency downloads are distinct from querying the product release, while actual InstrProof availability can only be verified after manual publication.

**Alternatives considered**: Testing PyPI before publication is impossible. Making CI depend on a previously published version tests the wrong artifact. Automating upload or credential setup violates scope.

## Python compatibility and validation matrix

**Decision**: Declare `requires-python >=3.12`, run the complete suite on 3.12, 3.13, and 3.14, and build/install/compare release artifacts once on designated Python 3.12.

**Rationale**: The metadata states the compatibility floor, the test matrix records versions explicitly validated by feature 006, and one designated environment is sufficient to validate a pure-Python `py3-none-any` artifact without redundant installation matrices. Later Python versions are neither rejected nor guaranteed by this matrix.

**Alternatives considered**: Capping metadata at 3.14 conflicts with the requested `>=3.12` floor. Installing artifacts on every matrix version duplicates the complete-suite coverage and the explicitly requested single-build approach.

## Clean dependency setup

**Decision**: Run the pre-release test/build phase from a newly created temporary environment synchronized from `uv.lock`, separate from both artifact smoke environments.

**Rationale**: A normal repository environment may contain stale or undeclared tools. A fresh locked environment makes the manual procedure reproducible while retaining independent wheel and source-distribution attribution.

**Alternatives considered**: Reusing `.venv` is faster but does not prove clean setup. Using unpinned tool execution can resolve moving dependency versions.

## Release validation entry point

**Decision**: Use a small POSIX `scripts/validate-release.sh` orchestrator and focused Python archive inspector, with fail-fast settings, labelled phases, `mktemp`, cleanup traps, fixed commands, and fresh output.

**Rationale**: This is auditable and locally runnable without adding a framework. Unique paths avoid stale artifacts and unsafe deletion.

**Alternatives considered**: README commands can drift. A task framework is unjustified. Repository `dist/` risks stale files or destructive cleanup.

## GitHub Actions topology

**Decision**: Use a 3.12/3.13/3.14 full-test matrix, one 3.12 build/metadata job that uploads both artifacts, and dependent, distinctly named wheel/source-distribution validation stages followed by behavioral comparison. Grant only `contents: read` and use stable-major official actions.

**Rationale**: Failures are distinguishable, pure-Python builds are not repeated, and smoke checks use transferred release candidates without publishing.

**Alternatives considered**: A monolithic job obscures failure domains. Matrix builds add time without changing a universal wheel. A publish job violates scope.

## Build equivalence

**Decision**: Compare normalized member names, bytes, and relevant modes while excluding timestamps and ordering not guaranteed by the backend.

**Rationale**: This detects content drift without claiming byte-for-byte reproducibility where container timestamps vary.

**Alternatives considered**: Raw hashes can differ only because of timestamps. Imposing a source-date epoch adds an unstated release policy.

## Existing CLI compatibility boundary

**Decision**: Preserve stdout, stderr, and statuses for `check`, `explain`, `diff`, and `diff --ci`. Add `--version` only at the root parser; direct `main(["--version"])` follows argparse with `SystemExit(0)`.

**Rationale**: Existing tests assert presentation and status. Root handling completes before repository access and works anywhere without touching analysis.

**Alternatives considered**: Refactoring dispatch raises semantic risk. Bespoke return handling diverges from argparse help/error behavior.
