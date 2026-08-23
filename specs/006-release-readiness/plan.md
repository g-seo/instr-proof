# Implementation Plan: Release-Ready Distribution

**Branch**: `[006-release-readiness]` | **Date**: 2026-08-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-release-readiness/spec.md`

## Summary

Make the existing dependency-free Python CLI ready for manual publication and independently verifiable as both a wheel and source distribution. Extend its PEP 621/Hatchling configuration with complete metadata and Apache-2.0 licensing, retain `instrproof.__version__` as the single authored version, expose that version through argparse, and add a small fail-fast validator mirrored by distinct GitHub Actions stages. A clean dependency environment, separate artifact environments, representative `check`/`diff` comparisons, metadata/archive inspection, and copy-and-run pre/post-publication documentation prove release behavior without changing analysis semantics or automating a PyPI upload.

## Technical Context

**Language/Version**: Compatibility floor Python `>=3.12`; complete suite explicitly validated on 3.12, 3.13, and 3.14; build and artifact behavior validated on designated 3.12

**Primary Dependencies**: No runtime dependencies; Hatchling build backend; uv dependency/task runner; Twine as development-only distribution metadata validator

**Storage**: N/A; repository files and temporary build/virtual-environment artifacts only

**Testing**: pytest complete suite plus focused CLI, metadata, archive-content, isolated-install, and cross-artifact behavioral-equivalence tests

**Target Platform**: Linux for required local and GitHub Actions validation; installable Python CLI from PyPI or GitHub

**Project Type**: Single-package command-line application using the `src/instrproof` layout

**Performance Goals**: No analysis performance changes; one build per CI run and one fail-fast local command for complete pre-release validation

**Constraints**: Preserve exact analysis, output, and exit behavior for `check`, `explain`, `diff`, and `diff --ci`; keep runtime dependencies empty; no credentials or publication automation; pre-release validation may download locked dependencies but must not install/query an InstrProof production release; clean dependency and artifact tests must not reuse editable/source-tree installations

**Scale/Scope**: One pure-Python package, one console entry point, two distribution formats, three tested Python versions, and the existing 250-test compatibility baseline

## Constitution Check

*GATE: Passed before Phase 0 research and passed again after Phase 1 design.*

- **I. Simplicity & Necessity — PASS**: The design modifies the existing package and argparse parser, uses the existing Hatchling/uv toolchain, and adds one auditable shell entry point. Twine is the only planned development dependency and directly validates publishable metadata.
- **II. Correctness & Testing — PASS**: Version behavior, required metadata, archive contents, CLI compatibility, clean installation, cross-artifact output/status equality, and failure stages have explicit automated validation. Existing behavioral tests remain the regression baseline.
- **III. Architectural Boundaries — PASS**: The single-package CLI architecture remains intact. Packaging and maintenance validation stay outside analysis modules; no new application layer is introduced.
- **IV. Security & Failure Handling — PASS**: Validation uses fixed project-controlled fixtures and commands, isolated temporary directories, non-extracting archive inspection, immediate failures, no pre-release installation/query of an InstrProof production release, no upload or credentials, and distinctly named CI stages. Locked dependency resolution remains permitted.
- **V. Spec-Driven Change Discipline — PASS**: Every planned change traces to feature 006 requirements. Semantic engine changes, new contracts, publishing automation, and platform-specific guarantees remain excluded.

**Post-design re-evaluation**: The CLI, distribution, and validation contracts below preserve the same boundaries and introduce no constitution violation. The complexity table is omitted because no violation requires justification.

## Project Structure

### Documentation (this feature)

```text
specs/006-release-readiness/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   ├── distribution.md
│   └── release-validation.md
└── tasks.md                 # created by /speckit-tasks, not this phase
```

### Source Code (repository root)

```text
.
├── .github/workflows/ci.yml
├── scripts/
│   ├── inspect_artifacts.py
│   └── validate-release.sh
├── src/instrproof/
│   ├── __init__.py          # single authored version
│   ├── __main__.py
│   ├── cli.py               # global --version only
│   ├── compare.py
│   ├── discovery.py
│   ├── extract.py
│   ├── models.py
│   └── repository.py
├── tests/
│   ├── integration/
│   │   ├── test_cli_installation.py
│   │   └── test_release_validation.py
│   └── unit/
│       ├── test_artifact_inspection.py
│       ├── test_ci_workflow.py
│       ├── test_cli_version.py
│       ├── test_packaging.py
│       └── test_readme_release_docs.py
├── LICENSE
├── README.md
├── pyproject.toml
└── uv.lock
```

**Structure Decision**: Preserve the existing single `src/instrproof` package and current unit/integration test organization. Add only repository-maintenance assets under `scripts/` and CI configuration under `.github/workflows/`; packaging tests inspect public configuration and built contracts without introducing application abstractions.

## Implementation Strategy

### Package metadata and artifact selection

- Replace the duplicated static PEP 621 version with a dynamic Hatchling version read from the literal `src/instrproof/__init__.py::__version__` value.
- Add the Apache-2.0 expression and license-file declaration, complete root license text, supported Python classifiers, author information supported by repository history, and canonical Repository/Issues URLs.
- Explicitly select `src/instrproof` for the wheel and an auditable source-distribution set containing package sources, build configuration, README, LICENSE, tests, and release-validation assets.
- Retain an empty `[project].dependencies` list. Add metadata validation only to the development dependency group and refresh the lock file.

### CLI version interface and compatibility

- Import `__version__` into the existing CLI module and add argparse's root-level `action="version"`, yielding `instrproof <version>` and status 0 before subcommand validation or repository discovery.
- Do not refactor existing subcommand dispatch, formatters, analysis calls, error paths, stdout/stderr routing, or status selection.
- Test the new parser behavior and retain the existing suite as the exact-output/exit-code compatibility guard.

### Local release validation

- Implement one POSIX shell orchestration script with strict/fail-fast behavior, labelled phases, an isolated `mktemp` workspace, and cleanup on exit.
- Create a fresh locked development environment, resolving development/build dependencies from configured indexes when necessary; run the complete tests there, build exactly one wheel and one source distribution once on Python 3.12 into fresh output, run strict Twine checks, and inspect the archives without installing or querying an InstrProof production release.
- The inspector verifies required Core Metadata fields, console entry point, version consistency, package files, and Apache license presence without extracting untrusted archive paths.
- Create distinct temporary virtual environments for wheel and source distribution installation. From neutral fixture repositories with inherited source lookup disabled, invoke each environment's exact Python and `instrproof` executables to validate help, version, package import/location, representative `check`, passing `diff`, and regression-producing `diff`. Compare CLI/package versions plus captured stdout, stderr, and statuses across artifacts, treating the expected regression status 1 as domain behavior rather than orchestration failure.

### Continuous integration

- Trigger on all pull requests and pushes to `main`, with workflow permissions limited to repository-content read access.
- Run the complete test suite in a clearly named 3.12/3.13/3.14 matrix.
- Build and validate both distributions once on Python 3.12 in a separately named job, then upload both as a workflow artifact using stable-major official actions.
- In dependent, separately named wheel-validation and source-distribution-validation stages, download the built artifacts, install them cleanly, run the shared behavioral fixtures, and compare their recorded results. Keep test-matrix, build, metadata, wheel, source-distribution, and equivalence failures attributable to named jobs or steps.
- Do not add any publish job, environment, secret, token, or elevated repository permission.

### Documentation

- Split README installation into PyPI, GitHub repository, and local contributor procedures with complete commands.
- Keep the consumer GitHub Actions example distinct from project CI; fetch full history, explicitly materialize `origin/main`, select a supported Python version, install an explicitly selected published version from PyPI, and run `instrproof diff --base origin/main --ci`.
- Preserve and clarify statuses 0, 1, and 2. Document the pre-release command as independent of any published InstrProof release, the manual publication boundary, and a separate post-publication procedure that installs the exact released version from production PyPI and repeats help/version/check/diff verification.

## Validation Approach

1. Run focused unit tests for root `--version`, imported/CLI version equality, PEP 621 requirements, and stable archive invariants.
2. Run the complete existing suite on Python 3.12, 3.13, and 3.14 in CI.
3. Build both distributions once on Python 3.12 from a fresh output location and reject missing, extra-count, invalid-metadata, entry-point, version, package-content, or license failures.
4. Install each artifact separately in designated Python 3.12 environments outside the checkout and compare help/version/import plus representative check/passing-diff/regression-diff stdout, stderr, and statuses.
5. Verify pre-release validation may resolve locked dependencies but neither uploads nor installs/queries an InstrProof production release; after manual publication, run the documented exact-version PyPI check separately.
6. Run `git diff --check`, inspect `git diff`, and inspect `git status` before implementation completion.
