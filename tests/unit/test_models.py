import pytest

from instrproof.models import ContractIdentity, RepoPath


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
    first = ContractIdentity(RepoPath("AGENTS.md"), "PathExists", RepoPath("src/./service.py"))
    second = ContractIdentity(RepoPath("AGENTS.md"), "PathExists", RepoPath("src/service.py"))
    assert first == second
    assert hash(first) == hash(second)
