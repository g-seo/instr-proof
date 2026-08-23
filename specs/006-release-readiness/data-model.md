# Data Model: Release-Ready Distribution

This feature introduces no persistent application data. These release-domain records describe configuration, built artifacts, and validation evidence.

## Package Manifest

Represents the authoritative release declaration.

### Fields

- `name`: exactly `instrproof`
- `version_source`: literal `instrproof.__version__`
- `description`, `readme`, and repository/issue URLs
- `requires_python`: `>=3.12`
- `license_expression`: `Apache-2.0`; `license_files` includes root `LICENSE`
- `authors_or_maintainers`, Python compatibility-floor metadata, and explicitly tested-version classifiers
- `runtime_dependencies`: empty
- `console_entry_point`: `instrproof` mapped to the existing CLI main function

### Validation rules

- All required identity, description, compatibility, licensing, URL, and entry-point fields exist.
- Metadata declares `>=3.12`; validation evidence records 3.12, 3.13, and 3.14 as explicitly tested without imposing an upper bound.
- The authored version exists in exactly one source location.
- Metadata, imported-package, and CLI versions are equal.
- No runtime dependency is introduced.

## Distribution Artifact

Represents one installable wheel or source distribution.

### Fields

- `format`, `name`, and `version`
- `core_metadata` and `entry_point`
- `package_members` and `license_members`

### Relationships and validation

- One Package Manifest produces exactly one wheel and one source distribution.
- Both artifacts have equal identity, version, CLI entry point, functionality, and license identity.
- The wheel contains package code, entry-point metadata, Core Metadata, and license.
- The source distribution contains build configuration, sources, README, complete license, tests, and intended validation assets.
- Archive inspection reads members without extracting them.

## Artifact Installation

Represents verification of one artifact in a clean environment.

### Fields

- `artifact_format`, unique `environment_path`, and neutral `working_directory`
- selected `python_version`, exact `cli_path`, and resolved `module_path`
- `cli_version`, `package_version`, resolved module path, and per-command stdout/stderr/status outcomes

### Validation rules

- Artifact formats use separate environments and explicit local artifact paths.
- Artifact installations use designated Python 3.12; the complete-suite matrix separately validates Python 3.12, 3.13, and 3.14 compatibility.
- Source-checkout leakage such as `PYTHONPATH` is absent.
- The module resides in the environment, not the repository.
- Help, version, and import succeed; versions are equal.
- Both environments run the same successful-check, passing-diff, and regression-diff fixtures and produce equal stdout, stderr, and expected statuses.

## Validation Run

Represents one complete local or automated pre-release assessment.

### Fields

- Clean dependency setup, complete test matrix, single build, metadata, archive inspection, installation, and behavioral-equivalence results
- `publication_performed`: always false

### State transitions

```text
Started -> CleanDependenciesReady -> TestsPassed -> ArtifactsBuilt -> MetadataValidated
        -> ArtifactsInspected -> WheelInstalledAndSmoked
        -> SourceDistributionInstalledAndSmoked -> BehaviorCompared -> Complete
```

Any failed stage transitions immediately to `Failed(stage)` and prevents later stages. CI groups these into separately named test, build/metadata, and installation/smoke jobs.

## Post-Publication Check

Represents a manual verification after the release candidate is uploaded outside this feature.

### Fields and validation

- Exact expected version and production PyPI source
- Clean environment and neutral representative repository
- PyPI installation, help, version, successful check, and representative diff results
- Installed and CLI versions MUST equal the exact released version; no upload or credential action is part of the check
