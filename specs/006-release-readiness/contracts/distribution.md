# Distribution Contract

## Package identity

Both artifacts MUST declare name `instrproof`, the version authored in `instrproof.__version__`, Python `>=3.12`, Apache-2.0, a non-empty summary and README, canonical repository and issue URLs, the existing console command, and zero runtime dependencies.

## Wheel invariants

- Exactly one pure-Python wheel is emitted by a clean build.
- It contains the package, metadata, entry-point declaration, and Apache license.
- Explicit local-path installation provides a runnable command and importable package without repository files and passes the representative behavioral fixture set.

## Source-distribution invariants

- Exactly one source distribution is emitted.
- It contains package source, `pyproject.toml`, README, complete root LICENSE, tests, and configured release-validation assets.
- Its identity/version equal the wheel's, and local-path installation produces equal help/version/import plus representative check/diff stdout, stderr, and statuses.

## Failure conditions

Validation fails for invalid or missing metadata, incorrect artifact counts/formats, absent license/package/entry point, version disagreement, installation failure, command failure outside an explicitly expected status, or behavioral inequality. Checks compare stable semantic contents, not ordering or timestamps unless guaranteed by the backend.
