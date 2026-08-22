# Implementation Plan: Inspection and Diagnostics

**Branch**: `004-inspection-diagnostics` | **Date**: 2026-08-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-inspection-diagnostics/spec.md`

## Summary

Add one shared, presentation-neutral current-evidence inspection primitive beneath existing contract promotion. It consumes the existing extracted PathClaim and PackageScriptClaim values plus the existing type-specific repository callbacks, evaluates evidence once per established identity, and returns supported occurrences with `PRESENT` or `MISSING`. Existing `promote_contracts()` delegates to this primitive and continues producing the same PathExistsContract and PackageScriptExistsContract values. A current repository operation reuses discovery, extraction, and this inspection result; `check` filters PRESENT occurrences into existing verified contracts, while `explain` selects all supported occurrences at an exact source line, including MISSING ones. CLI formatting remains separate and `diff` behavior stays unchanged.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: Python standard library (`argparse`, `dataclasses`, `enum`, `pathlib`); Git executable; no new runtime dependency

**Storage**: No persistent storage; current working-tree files and optional root `instrproof.json`; Git trees remain used only by existing diff

**Testing**: pytest with existing pure unit tests and temporary-Git-repository integration/CLI fixtures

**Target Platform**: Cross-platform CLI environments with Python 3.12+ and Git; normalized paths use `/`

**Project Type**: Installable Python CLI using a `src/` package layout

**Performance Goals**: Inspect 100 discovered instruction documents and 1,000 combined candidates within 5 seconds under a documented local test fixture

**Constraints**: Deterministic/offline; PRESENT/MISSING only; no BASE/HEAD state in new commands; line excluded from identity; lazy package-manifest inspection; no new dependency or contract hierarchy; exact diff output/status preserved

**Scale/Scope**: One working tree, all existing instruction discovery rules, existing PathExists and PackageScriptExists candidates/contracts, exact source-line lookup, human-readable output

## Constitution Check

*GATE: Passed before Phase 0 and re-checked after Phase 1.*

- **Simplicity & Necessity — PASS**: One evidence-inspection primitive is concretely reused by existing promotion, check, and explain. Only small result/occurrence values are added; no service layer, storage, registry, cache, plugin, or dependency is introduced.
- **Correctness & Testing — PASS**: Tests cover all four analysis outcomes, both evidence types/states, discovery variants, identity/deduplication, lookup, errors, ordering, performance, and complete 001–003 compatibility.
- **Architectural Boundaries — PASS**: Repository access remains in `GitRepository`; discovery/extraction remain unchanged; evidence and identity behavior remain in `compare.py`; domain values remain infrastructure-neutral; CLI consumes structured results.
- **Security & Failure Handling — PASS**: Source selectors use existing path normalization and positive-line validation. `RepositoryError` and unexpected analysis failures remain errors, never evidence states, and no command reparses another command's output.
- **Spec-Driven Change Discipline — PASS**: The design implements feature 004's current-state requirements and removes the former comparison-diagnostic plan. All exclusions and established features remain authoritative.

**Post-design re-check**: PASS. Phase 0/1 artifacts contain no unresolved clarification or constitution exception.

## Technical Decisions

1. **Shared extraction helper**: Extract current working-tree claim collection from `compare_repository()` into a private helper accepting the already-resolved discovery configuration. It calls existing `head_instruction_sources()` and both existing extractors once per source. Existing diff consumes the helper with unchanged results.
2. **Evidence-inspection primitive**: Add `inspect_claim_occurrences(claims, path_exists, script_exists)` in `compare.py`. It accepts existing claim unions and existing Boolean evidence callbacks, derives identity/location with existing helpers, and produces only supported extracted occurrences.
3. **Evidence once per identity**: Group claims by existing `ContractIdentity`, evaluate the normalized target once per identity, and reuse that PRESENT/MISSING state across its occurrences. Preserve every distinct diagnostic occurrence for explain lookup.
4. **Unsupported text boundary**: Unsupported or ambiguous text never reaches the primitive because only existing extractors create input claims. No rejection model or diagnostic is added.
5. **Failure boundary**: A successful Boolean callback maps to existing `EvidenceState.PRESENT` or `MISSING`. Callback/configuration/repository exceptions propagate. Do not catch them as missing and do not extend `EvidenceState`.
6. **Promotion reuse**: Refactor existing `promote_contracts()` to delegate evidence inspection to the new primitive, filter PRESENT identities, choose the same representative occurrence using the existing line/written-claim ordering, and construct the same existing PathExistsContract or PackageScriptExistsContract. Its signature, return type, equality, deduplication, and observed behavior remain unchanged.
7. **Current analysis operation**: Add `analyze_current_repository(repository)` that loads current discovery configuration once, collects current claims, lazily loads root scripts only if package evidence is requested, calls the shared inspection primitive, and derives verified contracts through the same promotion-from-inspected-occurrences helper used by `promote_contracts()`.
8. **Current analysis result**: Return a minimal immutable `CurrentAnalysisResult` containing all supported `CurrentOccurrence` values and the existing verified contract values. Missing occurrences remain in `occurrences` but never in `verified_contracts`.
9. **Occurrence projection**: `CurrentOccurrence` contains existing `ContractIdentity`, existing `SourceLocation`, exact evidence reference, and existing `EvidenceState`. It is not a contract subclass and defines no new identity.
10. **Neutral contract location**: Add a read-only `source_location` property to existing PathExistsContract and PackageScriptExistsContract as an alias for stored `base_location`. Preserve constructors, stored fields, equality, and diff code; new current presentation uses the neutral accessor.
11. **Evidence references**: PathExists uses the normalized target string. PackageScriptExists uses `package.json:scripts.<target>`. These describe the existing check and are not identity or validation inputs.
12. **Check projection**: `check` consumes `CurrentAnalysisResult.verified_contracts`, pairs each identity with its inspected PRESENT occurrence, and renders one row per identity sorted by existing ContractIdentity. Count is the verified-contract tuple length; zero is successful.
13. **Selector parsing**: Parse `<source>:<line>` at the final colon, normalize the complete repository-relative source with `RepoPath`, and require a positive decimal line. Invalid syntax/path/line is a user-input error following CLI error conventions.
14. **Explain lookup**: Filter `CurrentAnalysisResult.occurrences` by exact normalized source and line, deduplicate by ContractIdentity at that location, and sort by ContractIdentity. Return all distinct matches; do not search neighboring lines or require PRESENT evidence.
15. **No-match outcome**: Represent a valid selector with zero matches explicitly and map it to a clear normal user-facing nonzero outcome. Keep it distinct from invalid input and analysis failure.
16. **CLI integration**: Add check/explain argparse subcommands, explicit dispatch, and separate formatters for comparison, verified inspection, and occurrence explanation. CLI code never performs discovery, extraction, or evidence checks and never parses command text output.
17. **Status conventions**: Check returns 0 on successful analysis including zero. Explain returns 0 for matches and 1 for valid no-match. Invalid selector, repository/required-data failure, or converted unexpected analysis failure returns 2 with `error:` on stderr. Diff retains exact current 0/1/2 behavior and formatter.
18. **Unexpected failures**: Keep normal repository failures under `RepositoryError`. In only the new check/explain dispatch branches, catch an unexpected analysis exception at the outer CLI boundary, emit a generic `error: internal analysis failure` without repository-sensitive details, and return 2; never convert it to MISSING or success. Leave the existing diff exception path unchanged. Tests inject such a failure to verify it remains explicit.
19. **No comparison diagnostics**: New domain/results contain no BASE/HEAD fields, Regression conversion, stored history, or base ref. Existing comparison remains isolated to `compare_repository()` and `compare_contracts()`.
20. **Concrete reuse verification**: Tests and final review verify `compare_repository`, `analyze_current_repository`, check, and explain all consume the shared extraction/evidence primitives; no command-specific discovery, extraction, or validation loop is permitted.

## Project Structure

### Documentation (this feature)

```text
specs/004-inspection-diagnostics/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli.md
└── tasks.md             # Regenerate with /speckit-tasks after this plan revision
```

### Source Code (repository root)

```text
README.md
pyproject.toml
src/instrproof/
├── __init__.py
├── __main__.py
├── cli.py                        # Parsers, dispatch, presentation, status mapping
├── compare.py                    # Shared extraction, evidence inspection, promotion, operations
├── discovery.py                  # Existing behavior unchanged
├── extract.py                    # Existing behavior unchanged
├── models.py                     # Occurrence/result/selector values and neutral alias
└── repository.py                 # Existing evidence/configuration boundary unchanged
tests/
├── conftest.py
├── unit/
│   ├── test_compare.py           # Inspection/promotion/identity/lookup behavior
│   ├── test_discovery.py         # Existing behavior unchanged
│   ├── test_extract.py           # Existing behavior unchanged
│   └── test_models.py            # New value invariants and location alias
└── integration/
    ├── test_cli_diff.py          # Existing compatibility
    ├── test_cli_inspection.py    # New commands
    ├── test_performance.py       # Documented fixture performance
    └── test_repository.py        # Existing boundary behavior unchanged
```

**Structure Decision**: Keep the established single-package layout. The single new evidence-inspection primitive belongs in existing application/domain orchestration because it is reused by promotion and both current-state views.

## Complexity Tracking

No constitution violations require justification.
