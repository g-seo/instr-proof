"""Promotion and regression comparison for typed instruction contracts."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from instrproof.extract import extract_package_script_claims, extract_path_claims
from instrproof.models import (
    ComparisonResult,
    ContractIdentity,
    ContractType,
    EvidenceState,
    PackageScriptClaim,
    PackageScriptExistsContract,
    PathClaim,
    PathExistsContract,
    Regression,
    RepoPath,
    SourceLocation,
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


def promote_contracts(
    claims: Iterable[Claim],
    path_exists: PathExists,
    script_exists: ScriptExists | None = None,
) -> frozenset[Contract]:
    """Promote BASE claims whose type-specific evidence exists."""
    promoted: set[Contract] = set()
    for identity, claim in _representative_claims(claims).items():
        location = claim_location(claim)
        if isinstance(claim, PathClaim):
            if path_exists(claim.normalized_target):
                promoted.add(PathExistsContract(identity, location))
        elif script_exists is not None and script_exists(claim.normalized_target):
            promoted.add(PackageScriptExistsContract(identity, location))
    return frozenset(promoted)


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
    head_claims: tuple[Claim, ...] = tuple(
        claim
        for source in repository.head_instruction_sources(discovery_config)
        for claim in (*extract_path_claims(source), *extract_package_script_claims(source))
    )
    head_scripts: frozenset[str] | None = None

    def head_script_exists(name: str) -> bool:
        nonlocal head_scripts
        if head_scripts is None:
            head_scripts = repository.head_package_scripts()
        return name in head_scripts

    return compare_contracts(
        baseline, head_claims, repository.head_target_exists, head_script_exists
    )
