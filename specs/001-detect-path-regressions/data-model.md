# Data Model: Detect Path Regressions

## RepoPath

A normalized repository-relative path used at domain boundaries.

**Fields**:

- `value`: non-empty string using `/` separators

**Validation rules**:

- Must be relative to the repository root.
- Must not contain NUL, a drive/UNC prefix, or a leading `/`.
- After lexical normalization, must not equal `..` or begin with `../`.
- `.` segments and redundant separators are removed.
- Equality is case-sensitive, matching Git path identity.

## InstructionSource

A supported AI coding instruction document in one repository snapshot.

**Fields**:

- `path`: `RepoPath`; basename is exactly `AGENTS.md` or `CLAUDE.md`
- `content`: decoded text used for extraction

**Relationships**:

- Contains zero or more `PathClaim` values.

## PathClaim

An explicit supported path reference extracted from an instruction source before BASE evidence validation.

**Fields**:

- `source`: source document `RepoPath`
- `form`: `INLINE_PATH` or `MARKDOWN_LINK`
- `written_target`: destination as written, retained for diagnostics only
- `normalized_target`: resolved `RepoPath`
- `line`: optional positive source line, retained for diagnostics only

**Validation rules**:

- Inline targets are resolved from repository root.
- Markdown targets are resolved from `source.parent`.
- Unsupported or escaping destinations do not produce a `PathClaim`.
- `written_target`, `form`, and `line` do not participate in contract identity.

## ContractIdentity

The stable value identity of a monitored instruction contract.

**Fields**:

- `source`: normalized instruction-source `RepoPath`
- `contract_type`: fixed value `PathExists` for this feature
- `target`: normalized target `RepoPath`

**Validation rules**:

- Equality and hashing use all three fields and no positional/prose metadata.
- Multiple claims with the same identity collapse into one contract.

## PathExistsContract

A BASE claim promoted after repository evidence confirms its target exists.

**Fields**:

- `identity`: `ContractIdentity`

**Relationships**:

- Created from one or more equivalent BASE `PathClaim` values.
- Compared with HEAD claim identities and HEAD target evidence.

## Regression

A baseline contract whose claim survives in HEAD while its target does not.

**Fields**:

- `identity`: the regressed `ContractIdentity`

**Validation rules**:

- The identity must exist in the promoted BASE contract set.
- The same identity must exist in extracted HEAD claims.
- The target must be absent in HEAD.

## ComparisonResult

The successful domain result of one BASE-to-HEAD comparison.

**Fields**:

- `baseline_contract_count`: non-negative integer
- `regressions`: ordered tuple of `Regression`, sorted by source, contract type, and target

**Derived states**:

- `PASS`: comparison completed and `regressions` is empty.
- `REGRESSION`: comparison completed and `regressions` is non-empty.
- Operational failures are exceptions handled at the CLI boundary, not a `ComparisonResult`, so they cannot be confused with `PASS`.

## State Transitions

```text
instruction text
  -> supported candidate
  -> resolved PathClaim
  -> BASE target exists? -- no --> discarded
                         -- yes -> PathExistsContract
  -> same identity in HEAD? -- no --> retired (pass)
                            -- yes -> HEAD target exists? -- yes --> satisfied (pass)
                                                         -- no  --> Regression
```

