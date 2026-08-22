import pytest

from instrproof.models import (
    ContractIdentity,
    ContractType,
    EvidenceState,
    PackageManager,
    PackageScriptClaim,
    Regression,
    RepoPath,
    SourceLocation,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("src/./auth/../auth/service.py", "src/auth/service.py"), ("docs//api.md", "docs/api.md")],
)
def test_repo_path_normalizes_git_style_paths(raw: str, expected: str) -> None:
    assert RepoPath(raw).value == expected


@pytest.mark.parametrize("raw", ["", ".", "..", "../secret", "/tmp/x", "C:/tmp/x", "a\\b", "a\x00b"])
def test_repo_path_rejects_invalid_or_escaping_paths(raw: str) -> None:
    with pytest.raises(ValueError):
        RepoPath(raw)


def test_contract_identity_uses_source_type_and_normalized_target() -> None:
    first = ContractIdentity(RepoPath("AGENTS.md"), ContractType.PATH_EXISTS, "src/service.py")
    second = ContractIdentity(RepoPath("AGENTS.md"), ContractType.PATH_EXISTS, "src/service.py")
    assert first == second
    assert hash(first) == hash(second)


def test_contract_identity_distinguishes_type_and_supports_script_targets() -> None:
    package = ContractIdentity(
        RepoPath("AGENTS.md"), ContractType.PACKAGE_SCRIPT_EXISTS, "test:unit"
    )
    path = ContractIdentity(RepoPath("AGENTS.md"), ContractType.PATH_EXISTS, "test:unit")

    assert package.target == "test:unit"
    assert package != path


def test_package_claim_diagnostics_do_not_change_identity() -> None:
    first = PackageScriptClaim(
        RepoPath("AGENTS.md"), PackageManager.PNPM, "pnpm run typecheck", "typecheck", 2
    )
    moved = PackageScriptClaim(
        RepoPath("AGENTS.md"), PackageManager.YARN, "yarn typecheck", "typecheck", 99
    )

    first_identity = ContractIdentity(
        first.source, ContractType.PACKAGE_SCRIPT_EXISTS, first.normalized_target
    )
    moved_identity = ContractIdentity(
        moved.source, ContractType.PACKAGE_SCRIPT_EXISTS, moved.normalized_target
    )
    assert first_identity == moved_identity
    assert hash(first_identity) == hash(moved_identity)


def test_source_location_and_evidence_are_diagnostic_values() -> None:
    location = SourceLocation(RepoPath("AGENTS.md"), 4, "pnpm typecheck")
    assert location.line == 4
    assert EvidenceState.PRESENT.value == "present"
    assert EvidenceState.MISSING.value == "missing"


def test_regression_diagnostics_do_not_affect_equality_or_hashing() -> None:
    identity = ContractIdentity(
        RepoPath("AGENTS.md"), ContractType.PACKAGE_SCRIPT_EXISTS, "typecheck"
    )
    original = Regression(
        identity,
        SourceLocation(RepoPath("AGENTS.md"), 2, "pnpm run typecheck"),
        SourceLocation(RepoPath("AGENTS.md"), 3, "pnpm typecheck"),
        EvidenceState.PRESENT,
        EvidenceState.MISSING,
    )
    moved = Regression(
        identity,
        SourceLocation(RepoPath("AGENTS.md"), 20, "yarn run typecheck"),
        SourceLocation(RepoPath("AGENTS.md"), 30, "yarn typecheck"),
        None,
        None,
    )

    assert original == moved
    assert hash(original) == hash(moved)
