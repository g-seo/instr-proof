# Data Model: Inspection and Diagnostics

## Existing values reused unchanged

### ContractIdentity

```text
(instruction source RepoPath, ContractType, normalized target)
```

Line, occurrence, written form, evidence state, and repository state remain outside equality, hashing, and ordering.

### Claims and contracts

Existing PathClaim and PackageScriptClaim are the only supported candidate representations. Existing PathExistsContract and PackageScriptExistsContract remain the only verified contract representations.

### EvidenceState

- `PRESENT`: inspection succeeded and evidence exists.
- `MISSING`: inspection succeeded and evidence does not exist.

Analysis failure remains an error outside this enum.

## CurrentOccurrence

A presentation-neutral supported occurrence after successful current evidence inspection.

| Field | Type | Rules |
|---|---|---|
| `identity` | existing ContractIdentity | Derived with existing `claim_identity()` |
| `source_location` | existing SourceLocation | Actual extracted occurrence; diagnostic only |
| `evidence_reference` | string | Normalized path or `package.json:scripts.<target>` |
| `evidence_state` | existing EvidenceState | PRESENT or MISSING |

Unsupported/rejected text never creates this value. It is not a contract class.

## CurrentAnalysisResult

One completed analysis of the current working repository.

| Field | Type | Rules |
|---|---|---|
| `occurrences` | tuple of CurrentOccurrence | All supported occurrences, deterministic by identity then occurrence order |
| `verified_contracts` | tuple of existing contract union | PRESENT identities only, one per ContractIdentity, identity-sorted |

Invariants:

- Every verified identity has at least one PRESENT occurrence.
- No MISSING occurrence becomes a verified contract.
- Repeated equal occurrences remain available by line but yield one verified identity.
- Equal type/target in different sources remain distinct.

## SourceLocationSelector

| Field | Type | Rules |
|---|---|---|
| `source` | existing RepoPath | Complete normalized repository-relative instruction source |
| `line` | integer | Positive decimal line |

It is lookup input only and never changes identity.

## Neutral contract location

Existing contract classes expose read-only `source_location` as an alias of stored `base_location`. Storage, constructors, equality, hashes, and diff behavior remain unchanged.

## Derivation

```text
existing discovery + existing extractors
  -> existing supported claims
  -> group by existing identity
  -> existing repository evidence callbacks
  -> CurrentOccurrence(PRESENT|MISSING)
  -> CurrentAnalysisResult
       ├── PRESENT identities -> existing verified contracts -> check
       └── all exact source/line occurrences -> explain

inspection exception -> analysis error, no result
```

Existing `promote_contracts()` uses the same inspection and PRESENT-promotion operations, so diff and current inspection do not diverge.
