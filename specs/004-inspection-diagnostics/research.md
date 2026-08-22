# Research: Inspection and Diagnostics

## Decision 1: Inspect supported claims before promotion

**Decision**: Add one evidence-inspection primitive over existing PathClaim and PackageScriptClaim values, and make existing promotion delegate to it.

**Rationale**: Check needs the promoted PRESENT subset while explain also needs supported MISSING occurrences. Inspecting before promotion represents both without weakening verified contracts or duplicating validation.

**Alternatives considered**: Looking only at promoted contracts loses MISSING occurrences. A separate explain validator duplicates evidence logic. Promoting missing candidates changes contract semantics.

## Decision 2: Share discovery and extraction

**Decision**: Move the existing current-source extraction comprehension into one private helper used by diff and current analysis.

**Rationale**: Existing discovery and extractors are authoritative. A shared helper makes command-specific discovery/extraction impossible by construction.

**Alternatives considered**: Copying the flow into each command risks drift. A new service layer is unnecessary indirection.

## Decision 3: Evaluate evidence once per identity

**Decision**: Group supported claims by existing ContractIdentity, inspect evidence once, and attach that state to every retained diagnostic occurrence.

**Rationale**: Repeated occurrences have one evidence target and identity but each line must remain explainable. This avoids redundant repository calls while retaining location metadata.

**Alternatives considered**: Evaluating every occurrence repeats work. Keeping only one representative prevents lookup at repeated lines.

## Decision 4: Reuse existing promotion and contract models

**Decision**: Split promotion internally into inspection plus PRESENT filtering/representative selection while preserving the public `promote_contracts()` API and existing contract classes.

**Rationale**: Diff and tests already depend on promotion behavior. Internal delegation provides concrete reuse without a second identity or hierarchy.

**Alternatives considered**: A second verified-contract model violates scope. Leaving promotion independent would create two validation paths.

## Decision 5: Use one minimal occurrence value

**Decision**: Represent current diagnostics as identity, SourceLocation, evidence reference, and EvidenceState.

**Rationale**: These are exactly the structured fields shared by check/explain presentation. Existing identity/location/state types are composed rather than copied.

**Alternatives considered**: Per-contract occurrence subclasses duplicate the hierarchy. Formatting claims directly couples CLI to extraction details.

## Decision 6: Preserve stored location compatibility

**Decision**: Add a neutral `source_location` property to existing contracts while retaining `base_location` storage and constructors.

**Rationale**: New current views need neutral terminology, but a field rename would destabilize existing comparison code and tests for no behavioral benefit.

**Alternatives considered**: Reusing the BASE-specific name causes semantic drift. Full migration is broader than required.

## Decision 7: Exact lookup with all matches

**Decision**: Parse at the final colon, normalize the full source path, require a positive line, and return all distinct identities exactly on that line in identity order.

**Rationale**: This is deterministic, respects nested sources, and never guesses or silently chooses.

**Alternatives considered**: Nearest-line matching is unstable. Basename matching conflates sources. First-match output hides ambiguity.

## Decision 8: Two evidence states and explicit failures

**Decision**: Successful Boolean inspection yields PRESENT or MISSING. Repository/configuration/manifest failures propagate through the existing analysis-error mechanism.

**Rationale**: Missing evidence and inability to inspect are semantically different. Existing RepositoryError behavior already enforces this boundary.

**Alternatives considered**: UNKNOWN/UNINSPECTABLE violates scope. Treating errors as MISSING hides failures.

## Decision 9: Preserve lazy package evidence

**Decision**: Load root package scripts only when at least one package-script identity requires inspection.

**Rationale**: This retains established behavior where unrelated malformed package data does not break path-only analysis.

**Alternatives considered**: Eager parsing changes errors and wastes work.

## Decision 10: Keep comparison isolated

**Decision**: Add no BASE/HEAD fields, ref, history, or Regression conversion to current results.

**Rationale**: Diff owns comparison; the feature explicitly requests current state only.

**Alternatives considered**: Comparison diagnostics and persisted history are out of scope.
