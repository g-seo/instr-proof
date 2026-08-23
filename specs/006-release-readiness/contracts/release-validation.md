# Release Validation Contract

## Local entry point

```sh
./scripts/validate-release.sh
```

## Ordered phases

1. Create a fresh temporary development environment and synchronize locked dependencies, allowing resolution from configured package indexes but never installing or querying an InstrProof production release.
2. Run complete pytest suite.
3. Build exactly one wheel and source distribution into fresh temporary output.
4. Run standards-aware metadata validation.
5. Inspect archives for metadata, version, entry point, package, and license.
6. Install/smoke the wheel in a unique clean designated Python 3.12 environment outside the checkout, including help/version/import and representative check/diff fixtures.
7. Install/smoke the source distribution in a separate clean designated Python 3.12 environment with the same fixtures.
8. Compare package versions and all captured stdout, stderr, and statuses across the two installations.

The command stops at the first unexpected failure, names the phase, returns nonzero, cleans its explicit temporary workspace, and neither uploads nor installs/queries an InstrProof production release. Locked dependency resolution from configured indexes is allowed. Expected fixture status 1 is captured rather than treated as orchestration failure. The command does not delete or trust repository build output.

## CI mapping

- **Tests (Python 3.12/3.13/3.14)**
- **Build and validate distributions (Python 3.12, once)**
- **Validate wheel installation**
- **Validate source-distribution installation**
- **Compare artifact behavior**

Pull requests and pushes to `main` trigger the workflow. Permissions are read-only; there is no secret or publish step.

## Security invariants

Commands and paths are fixed by project configuration, archives are inspected without extraction, temporary paths are safely generated, smoke processes exclude checkout imports, and production credentials remain outside the interface.

## Post-publication interface

After a separate manual publication, documentation provides an exact-version command sequence that creates a clean environment, installs `instrproof==<released-version>` from production PyPI, and verifies help, version, representative check, and representative diff behavior. This sequence is not invoked by pre-release validation or CI.
