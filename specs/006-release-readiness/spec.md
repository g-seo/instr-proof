# Feature Specification: Release-Ready Distribution

**Feature Branch**: `[006-release-readiness]`  
**Created**: 2026-08-23  
**Status**: Draft  
**Input**: User description: "Make InstrProof release-ready so users can install it and validate it in open-source projects."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare and Install a Release Candidate (Priority: P1)

As an open-source project maintainer, I can build and install a release candidate in a clean supported environment before publication, so I can prove that users will receive a working package without relying on the source checkout.

**Why this priority**: A locally verifiable release candidate is the foundation for safe manual publication and external adoption.

**Independent Test**: In separate clean designated Python 3.12 environments outside the repository, install each newly built artifact and exercise the CLI against representative repositories. Separately, run the complete suite on Python 3.12, 3.13, and 3.14, and install from the GitHub repository URL in a clean Python 3.12-or-later environment.

**Acceptance Scenarios**:

1. **Given** a clean designated Python 3.12 environment outside the source repository, **When** a user installs either validated release artifact, **Then** installation succeeds without requiring repository files at runtime.
2. **Given** an artifact installation, **When** the user runs `instrproof --help` or `instrproof --version`, **Then** the command starts successfully and reports the expected interface and release version.
3. **Given** an artifact installation and a representative Git repository, **When** the user runs `instrproof check` or `instrproof diff`, **Then** each command retains its existing analysis, output, and exit-code behavior.
4. **Given** a clean supported environment, **When** a user installs InstrProof directly from its GitHub repository URL, **Then** the same command-line entry point is available outside the repository.
5. **Given** that a maintainer has manually published a release, **When** the exact released version is installed from production PyPI in a clean environment, **Then** the documented post-publication checks pass.

---

### User Story 2 - Verify Distribution Artifacts (Priority: P2)

As a maintainer, I can build, install, and compare both release artifact types locally before publication, so broken or inconsistent releases are detected without uploading anything to PyPI.

**Why this priority**: Publishing is unsafe unless maintainers can prove that every distributed artifact is installable, executable, consistently versioned, correctly licensed, and behaviorally equivalent.

**Independent Test**: Follow the documented pre-release procedure to run all tests, build both artifacts once, install the wheel and source distribution into separate clean environments, run representative `check` and `diff` fixtures, compare their outputs and statuses, and inspect artifact metadata and licensing.

**Acceptance Scenarios**:

1. **Given** a clean source checkout, **When** the maintainer performs the documented build on the designated Python 3.12 build environment, **Then** one source distribution and one platform-independent wheel are produced successfully.
2. **Given** either built artifact, **When** it is installed into its own clean supported environment outside the source checkout, **Then** `instrproof --help`, `instrproof --version`, `instrproof check`, and `instrproof diff` are available without relying on the source tree.
3. **Given** separate wheel and source-distribution installations, **When** representative passing and regression-producing repositories are analyzed, **Then** both installations report the same version and produce equivalent stdout, stderr, and exit statuses.
4. **Given** a release candidate with invalid metadata, a missing license declaration, unequal artifact behavior, or a non-executable installed command, **When** pre-release validation runs, **Then** validation fails before publication and identifies the failed stage.

---

### User Story 3 - Trust Automated Project Validation (Priority: P3)

As a contributor or prospective adopter, I can see automated validation on every pull request and every push to `main`, so I can determine whether InstrProof's tests, packaging, installation, and executable release behavior are healthy.

**Why this priority**: Visible, repeatable CI establishes confidence in the project and prevents packaging regressions from reaching a release.

**Independent Test**: Open a pull request or push a commit to `main` and observe a Python 3.12-3.14 test matrix plus distinct stages for the designated artifact build, metadata validation, clean wheel validation, and clean source-distribution validation.

**Acceptance Scenarios**:

1. **Given** a pull request or a push to `main`, **When** repository automation starts, **Then** it runs the complete test suite on Python 3.12, 3.13, and 3.14.
2. **Given** the test matrix succeeds, **When** the designated Python 3.12 build job runs, **Then** it builds one wheel and one source distribution and validates their metadata and contents.
3. **Given** successfully built artifacts, **When** automated artifact validation continues, **Then** each artifact is installed independently outside the source checkout and representative CLI behavior is compared.
4. **Given** a failure in testing, building, wheel validation, or source-distribution validation, **When** automation reports the result, **Then** the failing stage is identifiable without inspecting unrelated steps.

---

### User Story 4 - Follow Accurate Public Documentation (Priority: P4)

As a user or maintainer, I can choose among local development, PyPI, GitHub, pre-publication, and post-publication procedures, so I can install or release InstrProof using the procedure appropriate to my situation.

**Why this priority**: Accurate documentation must distinguish what can be proven before publication from what can only be confirmed after a manual production release.

**Independent Test**: Execute the local, GitHub, and artifact-based procedures before publication. After a manual release, execute the production-PyPI verification procedure against the exact published version.

**Acceptance Scenarios**:

1. **Given** the README, **When** a user looks for installation instructions, **Then** separate copy-and-run procedures are available for local source, PyPI, and GitHub URL installation.
2. **Given** the README's consumer GitHub Actions example and an available published release, **When** it runs in a workflow, **Then** it installs a pinned or explicitly selected published package version and executes InstrProof reproducibly.
3. **Given** the documented pre-release procedure, **When** a maintainer runs it locally, **Then** tests, builds, both artifact installations, and behavioral checks complete without a PyPI upload.
4. **Given** a manually published release, **When** the maintainer follows the documented post-publication procedure, **Then** the exact version is installed from production PyPI and its CLI and representative analysis behavior are verified.

### Edge Cases

- Installation and behavioral validation run from directories with no repository source files and no repository path added to the import search path.
- Stale build artifacts exist before validation and could otherwise mask a missing or malformed newly built artifact.
- The source distribution and wheel contain different version information or produce different stdout, stderr, or exit statuses.
- Package metadata is syntactically valid but omits a required project URL, supported-version declaration, description, or Apache-2.0 license information.
- A distribution builds successfully but its installed CLI entry point is absent or cannot start.
- `diff` returns status `1` for a deliberate regression fixture; validation recognizes this as expected domain behavior rather than an installation failure.
- `check` or `diff` is accidentally imported or executed from an editable or source-tree installation instead of the artifact under test.
- A user attempts installation on a Python version older than 3.12 and receives an explicit incompatibility result.
- No InstrProof release exists on production PyPI during pre-release validation; local and automated validation still validate the locally built artifacts while dependency resolution may use configured package indexes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: InstrProof MUST produce validated release artifacts and metadata suitable for manual publication to PyPI under the package name `instrproof` with a Python compatibility floor of `>=3.12`; the complete suite MUST explicitly validate Python 3.12, 3.13, and 3.14.
- **FR-002**: Installation from either validated release artifact MUST provide an `instrproof` command that functions from arbitrary directories without access to the repository source tree.
- **FR-003**: The installed command MUST support `instrproof --help`, `instrproof --version`, `instrproof check`, and `instrproof diff`.
- **FR-004**: Users MUST be able to install InstrProof directly from the project's GitHub repository URL.
- **FR-005**: The project MUST produce both a source distribution and a platform-independent wheel, and each artifact MUST install successfully in its own clean designated Python 3.12 environment.
- **FR-006**: The source distribution and wheel MUST expose the same CLI functionality, package version, stdout, stderr, and exit statuses for the representative validation cases.
- **FR-007**: Package metadata MUST identify the project description, supported Python versions, repository URL, issue tracker URL, and Apache-2.0 licensing.
- **FR-008**: The repository root MUST contain a license file with the complete Apache License 2.0 text.
- **FR-009**: Each distributed artifact MUST include identifiable Apache-2.0 license information.
- **FR-010**: The README MUST provide separate copy-and-run instructions for local source installation, PyPI installation, and GitHub URL installation.
- **FR-011**: The README MUST include a reproducible consumer GitHub Actions example that installs a published `instrproof` version and runs InstrProof.
- **FR-012**: Repository automation MUST run on every pull request and every push to the `main` branch.
- **FR-013**: Automated validation MUST run the complete automated test suite on Python 3.12, 3.13, and 3.14. It MUST build one source distribution and one platform-independent wheel once in a designated Python 3.12 build job rather than rebuilding them for every matrix version.
- **FR-014**: Automated validation MUST install the newly built wheel and source distribution into separate clean environments that neither import from nor execute an editable or source-tree copy of InstrProof.
- **FR-015**: For both artifact installations, automated validation MUST run `instrproof --help`, `instrproof --version`, a representative `check`, a passing `diff`, and a regression-producing `diff`; it MUST compare package versions, stdout, stderr, and exit statuses for equivalence.
- **FR-016**: Automated failures MUST clearly distinguish the test-matrix, package-build, metadata-validation, wheel-validation, and source-distribution-validation stages.
- **FR-017**: Automated validation MUST reject invalid required package metadata, missing license information, behaviorally unequal artifacts, and artifacts whose installed command is missing or cannot execute.
- **FR-018**: The project MUST document one pre-release validation procedure that may resolve development and build dependencies from configured package indexes but MUST NOT install or query an InstrProof release from production PyPI, upload artifacts, or require production credentials.
- **FR-019**: The pre-release procedure MUST cover the complete test suite, both distribution builds, separate clean installation of both artifacts, metadata and license checks, representative CLI behavior, version verification, and artifact-equivalence comparison.
- **FR-020**: Existing analysis semantics, output formats, and exit codes for `check`, `explain`, `diff`, and `diff --ci` MUST remain unchanged.
- **FR-021**: All 250 existing automated tests MUST continue to pass; new release-readiness tests may increase the total.
- **FR-022**: The feature MUST NOT create or configure package-index credentials, automatically upload to production PyPI, make CI depend on production PyPI, create GitHub Releases, add tag-driven version increments, configure Trusted Publishing, register a Marketplace action, add a demo repository, add rename-to-failure demonstrations, add contract types, change analysis-engine semantics, or add dedicated Windows/macOS guarantees.
- **FR-023**: After a maintainer manually publishes a release, the documented post-publication procedure MUST install the exact released version from production PyPI in a clean environment and verify `instrproof --help`, `instrproof --version`, representative `check`, and representative `diff` behavior.

### Key Entities

- **Release Candidate**: The versioned source distribution and wheel that have passed all pre-publication checks and are suitable for manual publication.
- **Published Package**: The manually published `instrproof` release identified by name, exact version, supported Python range, description, project links, license, and CLI entry point.
- **Distribution Artifact**: Either the source distribution or wheel created for one release; both represent the same package version, functionality, metadata, and license obligations.
- **Validation Run**: A local or automated execution that records separate outcomes for the test matrix, artifact build, metadata checks, clean artifact installations, and behavioral equivalence.
- **Installation Path**: One of the documented ways users obtain InstrProof: local source, built artifact, PyPI, or the GitHub repository URL.
- **Post-Publication Check**: A manual clean-environment verification of the exact version published to production PyPI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of designated pre-publication validation runs, both locally built artifacts install in clean isolated environments and start InstrProof without using the source checkout. After manual publication, the exact released version installs from production PyPI and passes the documented post-publication check.
- **SC-002**: The wheel and source distribution report identical versions and produce equivalent stdout, stderr, and exit statuses for `--help`, `--version`, representative `check`, passing `diff`, and regression-producing `diff` cases.
- **SC-003**: Every pull request and push to `main` receives visible results for the Python 3.12-3.14 test matrix, the single Python 3.12 artifact build, metadata validation, clean wheel validation, and clean source-distribution validation.
- **SC-004**: A deliberately invalid required metadata field, missing license declaration, unequal artifact result, or non-executable installed command causes validation to fail in the corresponding named stage on every attempt.
- **SC-005**: All 250 existing automated tests pass with no change to observable semantics, output formats, or exit codes of `check`, `explain`, `diff`, and `diff --ci`.
- **SC-006**: A maintainer can complete one documented local pre-release procedure, including tests, one build of both artifacts, separate clean installations, metadata checks, and behavioral comparison, without installing or querying an InstrProof production release, uploading artifacts, or requiring production credentials.
- **SC-007**: The local, GitHub URL, artifact, and consumer-CI instructions can be copied into their stated environments without undocumented repository setup; after manual publication, the separate PyPI procedure validates the exact released version.
- **SC-008**: The repository, wheel, and source distribution each provide clearly identifiable Apache-2.0 license information, with the repository license containing the complete license text.

## Assumptions

- Production PyPI publication is a manual maintainer action. This feature proves pre-publication readiness and defines a mandatory post-publication check but does not manage credentials or automate the upload.
- The package compatibility floor is Python `>=3.12`. Feature 006 CI explicitly validates the complete suite on Python 3.12, 3.13, and 3.14; this neither rejects nor guarantees later Python versions.
- The project produces a platform-independent `py3-none-any` wheel, so artifacts are built once on designated Python 3.12 and behaviorally validated rather than rebuilt for every matrix version.
- GitHub remains the canonical source repository and issue tracker host, using the project's canonical URLs.
- Clean installation means an isolated environment with no editable installation, repository path injection, or command execution from inside the source checkout.
- Representative artifact fixtures include a successful `check`, a passing `diff` with status `0`, and a regression-producing `diff` with status `1`.
- Existing domain-specific nonzero statuses are expected fixture outcomes when specified and do not by themselves indicate packaging failure.
- The existing count of 250 tests is the acceptance baseline; newly added packaging checks may increase the total.
- Linux is the required validation environment; dedicated Windows and macOS behavior remains out of scope.
