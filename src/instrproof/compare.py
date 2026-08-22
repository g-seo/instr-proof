"""Promotion and regression comparison for typed instruction contracts."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from instrproof.discovery import InstructionDiscoveryConfig
from instrproof.extract import extract_package_script_claims, extract_path_claims
from instrproof.models import (
    ComparisonResult,
    ContractIdentity,
    ContractType,
    CurrentAnalysisResult,
    CurrentOccurrence,
    EvidenceState,
    PackageScriptClaim,
    PackageScriptExistsContract,
    PathClaim,
    PathExistsContract,
    Regression,
    RepoPath,
    SourceLocation,
    SourceLocationSelector,
)
from instrproof.repository import GitRepository


PathExists = Callable[[RepoPath], bool]
ScriptExists = Callable[[str], bool]
Claim = PathClaim | PackageScriptClaim
Contract = PathExistsContract | PackageScriptExistsContract


def claim_identity(claim: Claim) -> ContractIdentity:
    if isinstance(claim, PathClaim):
        return ContractIdentity(
            claim.source, ContractType.PATH_EXISTS, claim.normalized_target.value
        )
    return ContractIdentity(
        claim.source, ContractType.PACKAGE_SCRIPT_EXISTS, claim.normalized_target
    )


def claim_location(claim: Claim) -> SourceLocation:
    written = (
        claim.written_target if isinstance(claim, PathClaim) else claim.written_command
    )
    return SourceLocation(claim.source, claim.line, written)


def _claim_order(claim: Claim) -> tuple[int, str]:
    location = claim_location(claim)
    return (
        location.line if location.line is not None else 2**31,
        location.written_claim or "",
    )


def _representative_claims(claims: Iterable[Claim]) -> dict[ContractIdentity, Claim]:
    representatives: dict[ContractIdentity, Claim] = {}
    for claim in claims:
        identity = claim_identity(claim)
        current = representatives.get(identity)
        if current is None or _claim_order(claim) < _claim_order(current):
            representatives[identity] = claim
    return representatives


def inspect_claim_occurrences(
    claims: Iterable[Claim],
    path_exists: PathExists,
    script_exists: ScriptExists | None = None,
) -> tuple[CurrentOccurrence, ...]:
    """Inspect evidence once per identity while retaining diagnostic occurrences."""
    grouped: dict[ContractIdentity, list[Claim]] = {}
    for claim in claims:
        grouped.setdefault(claim_identity(claim), []).append(claim)

    inspected: list[CurrentOccurrence] = []
    for identity in sorted(grouped):
        identity_claims = grouped[identity]
        representative = min(identity_claims, key=_claim_order)
        if isinstance(representative, PathClaim):
            exists = path_exists(representative.normalized_target)
            evidence_reference = representative.normalized_target.value
        else:
            exists = script_exists is not None and script_exists(
                representative.normalized_target
            )
            evidence_reference = f"package.json:scripts.{representative.normalized_target}"
        state = EvidenceState.PRESENT if exists else EvidenceState.MISSING
        for claim in sorted(identity_claims, key=_claim_order):
            inspected.append(
                CurrentOccurrence(
                    identity,
                    claim_location(claim),
                    evidence_reference,
                    state,
                )
            )
    return tuple(inspected)


def _promote_inspected(
    occurrences: Iterable[CurrentOccurrence],
) -> frozenset[Contract]:
    representatives: dict[ContractIdentity, CurrentOccurrence] = {}
    for occurrence in occurrences:
        if occurrence.evidence_state is not EvidenceState.PRESENT:
            continue
        representatives.setdefault(occurrence.identity, occurrence)

    promoted: set[Contract] = set()
    for identity, occurrence in representatives.items():
        if identity.contract_type is ContractType.PATH_EXISTS:
            promoted.add(PathExistsContract(identity, occurrence.source_location))
        else:
            promoted.add(
                PackageScriptExistsContract(identity, occurrence.source_location)
            )
    return frozenset(promoted)


def promote_contracts(
    claims: Iterable[Claim],
    path_exists: PathExists,
    script_exists: ScriptExists | None = None,
) -> frozenset[Contract]:
    """Promote BASE claims whose type-specific evidence exists."""
    return _promote_inspected(
        inspect_claim_occurrences(claims, path_exists, script_exists)
    )


def _current_claims(
    repository: GitRepository, discovery_config: InstructionDiscoveryConfig
) -> tuple[Claim, ...]:
    return tuple(
        claim
        for source in repository.head_instruction_sources(discovery_config)
        for claim in (*extract_path_claims(source), *extract_package_script_claims(source))
    )


def analyze_current_repository(repository: GitRepository) -> CurrentAnalysisResult:
    """Analyze supported claims and evidence in the current working tree."""
    discovery_config = repository.instruction_discovery_config()
    claims = _current_claims(repository, discovery_config)
    scripts: frozenset[str] | None = None

    def script_exists(name: str) -> bool:
        nonlocal scripts
        if scripts is None:
            scripts = repository.head_package_scripts()
        return name in scripts

    occurrences = inspect_claim_occurrences(
        claims, repository.head_target_exists, script_exists
    )
    contracts = tuple(
        sorted(_promote_inspected(occurrences), key=lambda item: item.identity)
    )
    return CurrentAnalysisResult(occurrences, contracts)


def parse_source_location_selector(value: str) -> SourceLocationSelector:
    """Parse and normalize a repository-relative ``source:line`` selector."""
    source_text, separator, line_text = value.rpartition(":")
    if (
        not separator
        or not source_text
        or not line_text.isascii()
        or not line_text.isdecimal()
    ):
        raise ValueError("invalid source location; expected <source>:<positive-line>")
    line = int(line_text)
    if line < 1:
        raise ValueError("invalid source location; line must be positive")
    try:
        source = RepoPath(source_text)
    except ValueError as exc:
        raise ValueError(f"invalid source location: {exc}") from exc
    return SourceLocationSelector(source, line)


def lookup_current_occurrences(
    result: CurrentAnalysisResult, selector: SourceLocationSelector
) -> tuple[CurrentOccurrence, ...]:
    """Return every distinct supported identity at an exact diagnostic location."""
    matches: dict[ContractIdentity, CurrentOccurrence] = {}
    for occurrence in result.occurrences:
        location = occurrence.source_location
        if location.source == selector.source and location.line == selector.line:
            matches.setdefault(occurrence.identity, occurrence)
    return tuple(matches[identity] for identity in sorted(matches))


def compare_contracts(
    baseline: Iterable[Contract],
    head_claims: Iterable[Claim],
    head_path_exists: PathExists,
    head_script_exists: ScriptExists | None = None,
) -> ComparisonResult:
    """Compare surviving typed claims with their HEAD evidence."""
    contracts = frozenset(baseline)
    head_by_identity = _representative_claims(head_claims)
    regressions: list[Regression] = []
    for contract in sorted(contracts, key=lambda item: item.identity):
        head_claim = head_by_identity.get(contract.identity)
        if head_claim is None:
            continue
        if contract.identity.contract_type is ContractType.PATH_EXISTS:
            exists = head_path_exists(RepoPath(contract.identity.target))
        else:
            exists = (
                head_script_exists is not None
                and head_script_exists(contract.identity.target)
            )
        if not exists:
            regressions.append(
                Regression(
                    contract.identity,
                    contract.base_location,
                    claim_location(head_claim),
                    EvidenceState.PRESENT,
                    EvidenceState.MISSING,
                )
            )
    return ComparisonResult(len(contracts), tuple(regressions))


def compare_repository(repository: GitRepository, base_ref: str) -> ComparisonResult:
    """Run the shared typed-contract pipeline for BASE and working-tree HEAD."""
    snapshot = repository.resolve_base(base_ref)
    discovery_config = repository.instruction_discovery_config()
    base_claims: tuple[Claim, ...] = tuple(
        claim
        for source in repository.base_instruction_sources(snapshot, discovery_config)
        for claim in (*extract_path_claims(source), *extract_package_script_claims(source))
    )
    base_scripts: frozenset[str] | None = None

    def base_script_exists(name: str) -> bool:
        nonlocal base_scripts
        if base_scripts is None:
            base_scripts = repository.base_package_scripts(snapshot)
        return name in base_scripts

    baseline = promote_contracts(
        base_claims,
        lambda path: repository.base_target_exists(snapshot, path),
        base_script_exists,
    )
    head_claims = _current_claims(repository, discovery_config)
    head_scripts: frozenset[str] | None = None

    def head_script_exists(name: str) -> bool:
        nonlocal head_scripts
        if head_scripts is None:
            head_scripts = repository.head_package_scripts()
        return name in head_scripts

    return compare_contracts(
        baseline, head_claims, repository.head_target_exists, head_script_exists
    )
