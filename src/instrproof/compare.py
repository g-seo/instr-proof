"""Promotion and regression comparison for PathExists contracts."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from instrproof.extract import extract_path_claims
from instrproof.models import (
    ComparisonResult,
    ContractIdentity,
    PathClaim,
    PathExistsContract,
    Regression,
    RepoPath,
)
from instrproof.repository import GitRepository


Exists = Callable[[RepoPath], bool]


def claim_identity(claim: PathClaim) -> ContractIdentity:
    return ContractIdentity(claim.source, "PathExists", claim.normalized_target)


def promote_contracts(claims: Iterable[PathClaim], target_exists: Exists) -> frozenset[PathExistsContract]:
    return frozenset(
        PathExistsContract(claim_identity(claim))
        for claim in claims
        if target_exists(claim.normalized_target)
    )


def compare_contracts(
    baseline: Iterable[PathExistsContract],
    head_claims: Iterable[PathClaim],
    head_target_exists: Exists,
) -> ComparisonResult:
    contracts = frozenset(baseline)
    head_identities = {claim_identity(claim) for claim in head_claims}
    regressions = tuple(
        Regression(contract.identity)
        for contract in sorted(contracts, key=lambda item: item.identity)
        if contract.identity in head_identities and not head_target_exists(contract.identity.target)
    )
    return ComparisonResult(len(contracts), regressions)


def compare_repository(repository: GitRepository, base_ref: str) -> ComparisonResult:
    snapshot = repository.resolve_base(base_ref)
    base_claims = (
        claim
        for source in repository.base_instruction_sources(snapshot)
        for claim in extract_path_claims(source)
    )
    baseline = promote_contracts(
        base_claims, lambda path: repository.base_target_exists(snapshot, path)
    )
    head_claims = (
        claim
        for source in repository.head_instruction_sources()
        for claim in extract_path_claims(source)
    )
    return compare_contracts(baseline, head_claims, repository.head_target_exists)
