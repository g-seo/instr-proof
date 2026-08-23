# CLI Contract: Global Version and Compatibility

## New global option

```text
instrproof --version
```

- Writes exactly `instrproof <VERSION>` plus one newline to stdout.
- Writes nothing to stderr and exits 0.
- Performs no repository discovery or analysis.
- `<VERSION>` equals `instrproof.__version__` and installed distribution metadata.
- Works from arbitrary directories and appears in root argparse help.

## Existing command compatibility

These interfaces remain unchanged:

```text
instrproof check
instrproof explain SOURCE:LINE
instrproof diff --base BASE_REF
instrproof diff --base BASE_REF --ci
```

No formatter, analysis selection, evidence rule, comparison rule, or command-specific exit decision changes. Existing stdout/stderr and statuses remain: 0 for successful check/explain or regression-free diff; 1 for explain no-match or diff regressions; 2 for invalid arguments or incomplete analysis. Missing subcommands and required arguments retain argparse status 2. CI mode changes presentation only.

## Installed-command validation

For each artifact, invoke its environment-local help/version commands and isolated Python import from outside the repository. Require equal CLI, package, and distribution versions, and require the module path to reside in the artifact environment.

Against identical temporary Git fixtures, also run a successful `check`, a passing `diff` with status 0, and a regression-producing `diff` with status 1. Wheel and source-distribution installations MUST produce equal stdout, stderr, and statuses for each case. Expected domain status 1 is captured for comparison and is not treated as validator failure.
