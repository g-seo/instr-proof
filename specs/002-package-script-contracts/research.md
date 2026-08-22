# Research: Package Script Contracts

## Existing architecture extension point

**Decision**: Extend the current `models.py` → `extract.py` → `repository.py` → `compare.py` → `cli.py` flow with a second typed claim and contract.

**Rationale**: Feature 001 already separates discovery/evidence from pure contract comparison. Every required package-script stage maps to an existing boundary, so a parallel pipeline would duplicate orchestration and violate project simplicity and architectural-boundary principles.

**Alternatives considered**: A package-script analyzer called separately by the CLI was rejected because it would duplicate source discovery, BASE resolution, HEAD survival, result aggregation, and errors. A generic plugin/registry system was rejected because only two closed contract types are required.

## Package command recognition

**Decision**: Recognize exactly the following lowercase-manager forms in ordinary instruction prose and single-backtick inline code, while continuing to mask fenced blocks:

```text
npm run SCRIPT
pnpm run SCRIPT
pnpm SCRIPT
yarn run SCRIPT
yarn SCRIPT
```

Require one or more ASCII spaces or tabs between command tokens. Newlines cannot occur inside a command form.

**Rationale**: The required instruction form includes prose such as “Run pnpm typecheck,” so backticks cannot be required. Fixed lexical forms and boundaries provide deterministic extraction without a shell parser.

**Alternatives considered**: Requiring inline code was rejected because it would miss required prose commands. Parsing quoting, environment assignments, substitutions, or command semantics was rejected as out of scope. Fenced blocks remain excluded consistently with feature 001.

## Script token and boundaries

**Decision**: Define `SCRIPT` with the case-sensitive regular-language pattern:

```text
[A-Za-z0-9][A-Za-z0-9._:/-]*
```

The first character must be an ASCII letter or digit. Later characters may additionally be `.`, `_`, `:`, `/`, or `-`. The extracted token is retained exactly; no case folding, path cleanup, or separator rewriting occurs.

A manager may begin only at start-of-text or immediately after one of:

```text
ASCII whitespace  `  (  [  {  :
```

`SCRIPT` must be followed immediately by one of:

```text
end-of-text
ASCII whitespace
`
,  )  ]  }  !  ?  .
&&  ||  ;  |
```

ASCII whitespace includes space, tab, carriage return, and newline. A newline may terminate a script token but cannot separate the manager, optional `run`, and script. For `&&`, require both characters; a lone `&` is not an accepted terminator. `||` and `|` are both accepted terminators. Any other adjacent character—including quotes, `$`, `@`, `#`, `=`, `>`, `<`, or `\`—rejects that occurrence rather than extracting a valid-looking prefix.

Whitespace and accepted shell operators terminate the candidate but do not invalidate it. Thus `pnpm typecheck --watch` and `pnpm typecheck && npm run test` both yield `typecheck`; the extractor does not interpret the trailing arguments or operator. The latter text may independently yield `test` because it contains another complete supported form.

**Rationale**: This grammar supports requested names such as `test:unit`, `lint-fix`, `build_docs`, `docs.build`, and `build/client` while making every start, character, and termination decision directly testable. Treating whitespace/operators as lexical terminators satisfies the required boundary behavior without claiming shell semantics.

**Alternatives considered**: Accepting every non-whitespace character would admit shell syntax and quoting. Rejecting a command merely because arguments follow would conflict with whitespace termination and miss otherwise explicit script references. Treating arbitrary punctuation as a terminator could extract prefixes from unsupported script names.

## Bare pnpm and yarn command ambiguity

**Decision**: `npm SCRIPT` is never a candidate. Explicit `pnpm run SCRIPT` and `yarn run SCRIPT` are candidates regardless of shorthand exclusions. For shorthand, exclude these exact lowercase tokens:

```text
PNPM_SHORTHAND_EXCLUSIONS = {
  "add", "approve-builds", "audit", "bin", "completion", "config",
  "create", "deploy", "dlx", "env", "exec", "fetch", "help", "import",
  "init", "install", "link", "list", "outdated", "pack", "patch",
  "patch-commit", "patch-remove", "prune", "publish", "rebuild", "remove",
  "root", "self-update", "server", "setup", "store", "unlink", "update",
  "view", "why"
}

YARN_SHORTHAND_EXCLUSIONS = {
  "add", "bin", "cache", "completion", "config", "constraints", "create",
  "dedupe", "dlx", "exec", "explain", "help", "info", "init", "install",
  "link", "npm", "pack", "patch", "patch-commit", "plugin", "rebuild",
  "remove", "search", "set", "stage", "unlink", "unplug", "up", "upgrade",
  "version", "why", "workspace", "workspaces"
}
```

Exclusion comparison is exact and case-sensitive. Tokens beginning with `-` cannot match the script grammar. A colliding script can still be referenced unambiguously as `pnpm run install` or `yarn run add`.

**Rationale**: Bare pnpm/yarn syntax can invoke scripts but also names package-manager operations. Frozen enumerated sets make extraction deterministic, while explicit `run` avoids false negatives for colliding manifest script names. BASE root-manifest validation remains the final precision gate after syntax extraction.

**Alternatives considered**: Treating every bare word as a script would promote obvious built-ins. Requiring `run` for pnpm/yarn would contradict the specification. Dynamically querying installed package-manager versions would make results environment-dependent. Consulting the manifest during extraction is not a replacement for the exclusion rule; manifest lookup remains the later BASE evidence stage.

## Script-name normalization

**Decision**: Normalize all supported forms by retaining the grammar-validated script token exactly, including case and `.`, `_`, `:`, `/`, and `-`. Do not represent it as `RepoPath`.

**Rationale**: Package manifest keys are case-sensitive strings and `test:unit` is a normal script name. Package-manager spelling and optional `run` do not belong in identity. Filesystem normalization would incorrectly apply path or drive-letter rules to script keys.

**Alternatives considered**: Lowercasing was rejected because it changes manifest-key identity. Reusing `RepoPath` was rejected because script targets are not paths. Retaining the complete command was rejected because syntax changes such as `pnpm run typecheck` to `pnpm typecheck` must preserve identity.

## Contract model evolution

**Decision**: Use a closed `ContractType` enum and a normalized string target in `ContractIdentity`, while retaining typed claim and contract dataclasses for PathExists and PackageScriptExists.

**Rationale**: The identity tuple is already generic in concept but currently validates only PathExists and stores a `RepoPath`. A string target accommodates both domains while constructors/extractors enforce type-specific normalization. Closed enum dispatch makes unsupported types explicit without speculative extensibility.

**Alternatives considered**: Separate identity classes would complicate mixed sorting and comparison. A fully generic protocol/registry would add abstraction without a third contract type. Encoding scripts as synthetic paths would blur evidence domains and create invalid normalization behavior.

## Root package manifest access

**Decision**: Add root-manifest readers to `GitRepository`: BASE reads `package.json` from the resolved tree through Git; HEAD reads `<repository-root>/package.json`. Parse with the Python standard library and cache each state's script-name set.

**Rationale**: This reuses the snapshot/filesystem abstraction, keeps Git and JSON failures outside domain comparison, avoids repeated parsing for multiple claims, and requires no dependency. Using the exact root path enforces the nested/workspace exclusion structurally.

**Alternatives considered**: Direct reads from `compare.py` were rejected because they couple business logic to infrastructure. Recursively locating manifests was rejected as out of scope. A package-manifest library was rejected because simple safe JSON decoding needs no dependency.

## Missing versus invalid manifest evidence

**Decision**: Treat an absent root manifest or absent `scripts` member as missing evidence. Treat invalid UTF-8, malformed JSON, a non-object root, a present non-object `scripts` value, or an I/O/Git failure as `RepositoryError` when package evidence is required.

**Rationale**: Absence answers the existence question normally. Invalid or unreadable content prevents reliable analysis and must never be converted into an empty script set. Requiring an object for a present `scripts` member gives deterministic validation at the trust boundary.

**Alternatives considered**: Treating malformed data as no scripts was rejected because it could produce false regressions or false non-monitoring. Failing every diff merely because an unrelated malformed manifest exists was rejected; lazy reads allow path-only analysis to remain unaffected.

## Evidence-read timing

**Decision**: Load BASE scripts only when package candidates exist, and load HEAD scripts only when promoted package contracts survive claim matching.

**Rationale**: The manifest is relevant only to candidate promotion or surviving-contract validation. Lazy access satisfies “when analysis requires it,” avoids unrelated errors, and prevents needless Git/filesystem work.

**Alternatives considered**: Unconditional reads were rejected because they would change PathExists-only behavior. Per-claim reads were rejected because they repeat parsing and complicate error consistency.

## Diagnostics and compatibility

**Decision**: Store representative source-location metadata separately from identity. Preserve current PathExists output exactly; PackageScriptExists rows add the current claim line and explicit `base=present head=missing` evidence states.

**Rationale**: The new output requirements ask for source/location and BASE/HEAD evidence, while feature 001 compatibility constrains existing rows. Separate metadata allows useful diagnostics without making line or written syntax part of equality, hashing, survival, or deduplication.

**Alternatives considered**: Adding line numbers to identity was rejected by the specification. Changing all row formats was rejected as unnecessary compatibility risk. Omitting evidence state from package rows would not meet the planning direction.

## Testing strategy

**Decision**: Extend the existing pytest files with parameterized extraction/model/comparison tests and temporary-repository integration cases; retain the full pre-existing test suite as a compatibility gate.

**Rationale**: Tests remain aligned to established boundaries and user-observable behavior. Temporary Git repositories exercise BASE-object versus HEAD-working-tree semantics and malformed evidence reliably without altering the project repository.

**Alternatives considered**: A separate package-script test framework was rejected as duplicate infrastructure. Mock-only repository tests were rejected because Git object and working-tree differences are core behavior.
