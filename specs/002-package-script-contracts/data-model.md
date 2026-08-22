# Data Model: Package Script Contracts

## ContractType

A closed discriminator for evidence semantics and display.

**Values**:

- `PathExists`
- `PackageScriptExists`

**Validation rules**:

- Unsupported values are rejected.
- Ordering uses the stable displayed value for deterministic mixed output.

## ContractIdentity

The stable identity shared by all monitored instruction contracts.

**Fields**:

- `source`: normalized instruction-source `RepoPath`
- `contract_type`: `ContractType`
- `target`: non-empty normalized string whose type-specific validation happened before identity construction

**Validation rules**:

- Equality, hashing, and ordering use exactly source, contract type, and normalized target.
- For `PathExists`, target is the normalized repository-relative path value.
- For `PackageScriptExists`, target is the exact normalized script-name token.
- Line, prose, written command, package manager, and optional `run` syntax do not participate.

## PackageScriptClaim

A high-confidence supported package-manager command extracted before repository evidence validation.

**Fields**:

- `source`: instruction-source `RepoPath`
- `package_manager`: `NPM`, `PNPM`, or `YARN`, diagnostic only
- `written_command`: full matched command, diagnostic only
- `normalized_target`: script-name string
- `line`: positive source line, diagnostic only

**Validation rules**:

- The recognized prose or inline-code command matches one of the five forms in `research.md`; fenced blocks are excluded.
- The target matches `[A-Za-z0-9][A-Za-z0-9._:/-]*` and is retained case-sensitively.
- Start and termination boundaries are exactly the enumerated sets in `research.md`; whitespace and supported shell operators terminate rather than invalidate the token.
- Bare pnpm/yarn tokens in the exact manager-specific exclusion sets do not create claims; explicit `run` forms bypass those sets.
- Package manager, written command, and line do not affect contract identity.

## PathClaim

The existing supported repository-path claim.

**Change for this feature**:

- Its identity target is supplied as `normalized_target.value` to the shared string target.
- Existing resolution, validation, forms, and diagnostic fields remain unchanged.

## SourceLocation

Diagnostic metadata retained separately from contract identity.

**Fields**:

- `source`: instruction-source `RepoPath`
- `line`: optional positive integer
- `written_claim`: optional original spelling

**Validation rules**:

- Never contributes to identity, equality of identities, or survival.
- When duplicate claims share an identity, choose the lowest line deterministically as representative metadata.

## PackageScriptExistsContract

A BASE package-script claim promoted after root-manifest evidence confirms its target key.

**Fields**:

- `identity`: `ContractIdentity` with type `PackageScriptExists`
- `base_location`: representative `SourceLocation`, diagnostic only

**Relationships**:

- Created from one or more equivalent BASE `PackageScriptClaim` values.
- Deduplicated by `identity`.
- Compared with HEAD claim identities and root-manifest script evidence.

## PathExistsContract

The existing BASE-validated path contract.

**Change for this feature**:

- Uses the generalized `ContractIdentity` target string.
- May retain representative BASE location through the same metadata mechanism.
- Promotion and target evidence semantics remain unchanged.

## PackageManifestScripts

Parsed evidence from the root `package.json` in one repository state.

**Fields**:

- `script_names`: immutable set of exact keys under `scripts`
- `manifest_present`: boolean distinguishing absent manifest from parsed manifest for diagnostics

**Validation rules**:

- Only repository-root `package.json` is eligible.
- Missing file or missing `scripts` member yields an empty name set without an analysis error.
- A present manifest must decode as UTF-8 and parse as a JSON object.
- A present `scripts` member must be an object; values are not interpreted.
- Malformed or unreadable required evidence raises an operational error rather than creating this value.

## EvidenceState

The result of validating a contract target in one repository state.

**Values**:

- `PRESENT`: target evidence exists.
- `MISSING`: repository state was inspected reliably and target evidence does not exist.

Operational inspection failure is an exception, not an evidence state.

## Regression

A promoted BASE contract whose identity survives in HEAD while HEAD evidence is missing.

**Fields**:

- `identity`: regressed `ContractIdentity`
- `base_location`: representative BASE diagnostic location
- `head_location`: representative surviving HEAD diagnostic location
- `base_evidence`: always `PRESENT` for a promoted contract
- `head_evidence`: always `MISSING` for a regression

**Validation rules**:

- Identity belongs to the promoted BASE set.
- The same identity exists among HEAD claims.
- Type-appropriate HEAD evidence is missing.
- Both PathExists and PackageScriptExists regressions carry these diagnostics.
- Diagnostic fields do not change identity, equality, hashing, survival, or sort order.

## ComparisonResult

The existing successful comparison result containing both contract types.

**Fields**:

- `baseline_contract_count`: total promoted PathExists and PackageScriptExists identities
- `regressions`: ordered tuple of mixed `Regression` values

**Derived states**:

- `PASS`: comparison completed and no regressions exist.
- `REGRESSION`: comparison completed and at least one regression exists.
- Analysis failure remains outside this value and maps to CLI exit 2.

## State Transitions

```text
discovered instruction source
  -> extract PathClaim and PackageScriptClaim candidates
  -> BASE type-specific evidence exists?
       no  -> candidate discarded (not monitored)
       yes -> typed baseline contract (deduplicated by identity)
  -> same source + type + normalized target in HEAD claims?
       no  -> contract retired (pass)
       yes -> retain representative HEAD location
             -> HEAD type-specific evidence exists?
                  yes -> satisfied (pass)
                  no  -> Regression(base=PRESENT, head=MISSING)
```

Package-manager syntax changes preserve the same package identity when the script target is unchanged. Script-target changes produce a new HEAD identity, so the old BASE contract retires rather than regresses.
