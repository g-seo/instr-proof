# Data Model: Discover Instruction Documents

## InstructionDiscoveryConfig

Represents validated discovery rules for one comparison invocation.

| Field | Type | Rules |
|-------|------|-------|
| `additional_rules` | ordered tuple of instruction rules | Defaults to empty; duplicate inputs have no duplicate-analysis effect |

Validation occurs when `instrproof.json` is read. The immutable resolved configuration is shared by BASE and HEAD discovery.

## InstructionRule

A repository-relative exact source path or glob supplied by one `instructions` entry.

| Field | Type | Rules |
|-------|------|-------|
| `written` | string | Non-empty JSON string retained for error context |
| `kind` | exact path or glob | Glob when the value contains `*`, `?`, or `[`; exact otherwise |
| `normalized` | `RepoPath` or normalized POSIX pattern | Relative, `/`-separated, non-escaping, non-absolute, no NUL/backslash; valid glob syntax |

Exact rules match an equal normalized file when it exists. Globs match complete normalized paths using [research.md](research.md). Matching zero files is valid.

## InstructionSourcePath

The selected identity of one instruction document before content loading, represented by existing `RepoPath`.

| Attribute | Rule |
|-----------|------|
| Value | Complete repository-relative path, never only the basename |
| Normalization | Existing canonical Git-style `RepoPath` normalization |
| Eligibility | Default basename match or at least one configured rule match |
| Uniqueness | One value per normalized path in one repository state |
| Order | Lexicographic normalized-path order |

Examples include `AGENTS.md`, `packages/auth/AGENTS.md`, `.claude/rules/testing.md`, and `docs/agent-instructions.md`.

## DiscoverySet

The deterministic collection returned for one repository state.

| Field | Type | Rules |
|-------|------|-------|
| `state` | BASE or HEAD context | Supplied by repository access; not part of source identity |
| `sources` | sorted unique tuple of `RepoPath` | Union of default/configured matches; every physical path appears once |

### Derivation

1. Receive all normalized file paths for one state.
2. Select files named exactly `AGENTS.md` or `CLAUDE.md`.
3. Add files matching each configured exact rule or glob.
4. Deduplicate by normalized `RepoPath`.
5. Return paths in lexical order.

BASE and HEAD derive separate sets from separate enumerations using the same `InstructionDiscoveryConfig`.

## InstructionSource (existing, validation adjusted)

Pairs a discovered source path with decoded Markdown content for existing extractors.

| Field | Type | Rules |
|-------|------|-------|
| `path` | `RepoPath` | Any path admitted by discovery; complete path retained |
| `content` | string | UTF-8 decoded instruction text |

The former basename restriction is removed because eligibility belongs to discovery. Rule provenance is not retained downstream.

## Existing claims and contracts (unchanged)

`PathClaim`, `PackageScriptClaim`, `PathExistsContract`, and `PackageScriptExistsContract` retain `InstructionSource.path` as source. Identity remains:

```text
(instruction source RepoPath, contract type, normalized target)
```

- Equal claims within one source collapse under existing representative-claim logic.
- `AGENTS.md + PathExists(foo.md)` differs from `packages/auth/AGENTS.md + PathExists(foo.md)`.
- Line, written form, discovery rule, and repository state stay outside identity.

## State transitions

```text
absent instrproof.json -> empty additional rules
valid instrproof.json  -> one immutable shared rule set
invalid/unreadable     -> explicit analysis error

state file enumeration
  -> normalized available files
  -> default + configured selection
  -> deduplicated sorted DiscoverySet
  -> UTF-8 InstructionSource values
  -> existing extraction pipeline
```

A source can exist in BASE only, HEAD only, both, or neither. The existing claim-survival comparison handles these differences without new contract transitions.
