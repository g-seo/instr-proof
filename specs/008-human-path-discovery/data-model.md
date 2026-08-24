# Data Model: Harden Path and Instruction Discovery

No new contract, persistent entity, identity field, or `models.py` change is planned.

## Root-Level Inline Candidate

A transient lexical string inside inline code.

| Attribute | Rule |
|-----------|------|
| Segments | Exactly one; no `/` or `\` |
| Content | No whitespace or NUL |
| Context | Inline code outside fenced blocks |
| Address | Repository-relative; not absolute, URL, query, fragment, glob, placeholder, or shell expression |
| File form | Final extension starts with ASCII letter, or exact extensionless allowlist member |
| Case | Significant |

Allowlist: `Makefile`, `Dockerfile`, `Containerfile`, `Justfile`, `Procfile`, `LICENSE`, `NOTICE`.

```text
inline text
 -> nested grammar OR root filename grammar
 -> existing _resolve + RepoPath
 -> PathClaim(INLINE_PATH)
 -> exact BASE evidence
 -> existing PathExistsContract only when present
```

## PathClaim (existing)

| Field | Feature behavior |
|-------|------------------|
| `source` | Existing instruction `RepoPath` |
| `form` | `INLINE_PATH` for nested and root inline forms |
| `written_target` | Exact diagnostic spelling |
| `normalized_target` | Repository-root-relative `RepoPath` |
| `line` | Diagnostic only; excluded from identity |

Markdown-link construction and source-relative resolution remain unchanged.

## Configuration Snapshots

Invocation-local uses of existing `InstructionDiscoveryConfig`, not new models.

| Context | Owner | Absence | Error label | Consumer |
|---------|-------|---------|-------------|----------|
| BASE | Exact resolved Git tree | Empty rules | `BASE instrproof.json` | BASE discovery |
| HEAD | Working tree | Empty rules | `HEAD instrproof.json` | Normal HEAD discovery |

One parser validates both; values may differ and are never substituted.

## InstructionSource (existing)

`path` remains the complete normalized `RepoPath`; `content` is state-policy UTF-8. Selecting rules are not stored or added to identity.

## BASE Discovery Set

A lexically sorted, path-deduplicated tuple of sources selected by defaults plus BASE config. Its exact paths are retained. Only its claims can become baseline contracts.

## Normal HEAD Discovery Set

Sources selected from tracked and supported non-ignored untracked files using defaults plus HEAD config. This remains the complete source set for `check` and `explain`.

## Comparison HEAD Source Union

```text
normal HEAD paths
 UNION surviving readable BASE-discovered paths
 -> normalize RepoPath
 -> deduplicate
 -> lexical sort
 -> load each InstructionSource once
```

Invariants:

- Defaults, overlapping rules, and carry-forward cannot duplicate a physical source.
- Comparison orchestration loads and extracts each normalized physical HEAD source exactly once, verified by an explicit source-read call count.
- BASE content is never reused as HEAD content.
- A deleted BASE source contributes no HEAD claim.
- Carried sources use normal HEAD readability/UTF-8 errors.
- The union is comparison-only.

## ContractIdentity (unchanged)

```text
(instruction source RepoPath, contract type, normalized target)
```

Line, spelling, claim form, state, config, and discovery rule remain excluded.

## State transitions

```text
resolve BASE -> parse BASE config -> discover/load BASE -> extract -> promote with BASE evidence
parse HEAD -> normal discovery -> union surviving BASE paths -> load/extract once
-> existing compare_contracts
```

| HEAD state | Existing outcome |
|------------|------------------|
| Same claim, evidence present | Pass |
| Same claim, evidence missing | Regression |
| Claim repaired/removed | Old contract retired; pass |
| Source removed | Old contract retired; pass |
| Source selected only by HEAD | No retroactive baseline contract |

Ordering stays by normalized source then existing identity/diagnostic keys. Any BASE cache is keyed by exact resolved snapshot. Three repeated analyses of deterministic fixtures must produce identical selection, ordering, diagnostics, output, and status.
