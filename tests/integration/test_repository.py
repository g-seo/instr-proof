from pathlib import Path

import pytest

from instrproof.models import RepoPath
from instrproof.repository import GitRepository, RepositoryError

from conftest import git


def test_discovers_repository_and_reads_base_and_head(committed_repo: Path) -> None:
    repository = GitRepository.discover(committed_repo / "src")
    commit = repository.resolve_base("HEAD")
    base = repository.base_instruction_sources(commit)
    head = repository.head_instruction_sources()

    assert repository.root == committed_repo
    assert [source.path.value for source in base] == ["AGENTS.md"]
    assert [source.content for source in head] == ["Use `src/auth/service.py`.\n"]
    assert repository.base_target_exists(commit, RepoPath("src/auth/service.py"))
    assert repository.head_target_exists(RepoPath("src/auth/service.py"))


def test_head_omits_deleted_instruction(committed_repo: Path) -> None:
    (committed_repo / "AGENTS.md").unlink()
    assert GitRepository.discover(committed_repo).head_instruction_sources() == ()


def test_invalid_base_is_explicit(committed_repo: Path) -> None:
    with pytest.raises(RepositoryError):
        GitRepository.discover(committed_repo).resolve_base("does-not-exist")


def test_non_repository_is_explicit(tmp_path: Path) -> None:
    with pytest.raises(RepositoryError, match="not inside"):
        GitRepository.discover(tmp_path)


def test_invalid_utf8_base_instruction_is_explicit(git_repo: Path) -> None:
    (git_repo / "AGENTS.md").write_bytes(b"\xff")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "invalid base instruction")
    repository = GitRepository.discover(git_repo)

    with pytest.raises(RepositoryError, match="not valid UTF-8"):
        repository.base_instruction_sources(repository.resolve_base("HEAD"))


def test_invalid_utf8_head_instruction_is_explicit(committed_repo: Path) -> None:
    (committed_repo / "AGENTS.md").write_bytes(b"\xff")

    with pytest.raises(RepositoryError, match="cannot read instruction"):
        GitRepository.discover(committed_repo).head_instruction_sources()


def test_head_target_existence_counts_a_dangling_symlink(committed_repo: Path) -> None:
    link = committed_repo / "dangling-link"
    try:
        link.symlink_to("missing-target")
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are unavailable on this platform")

    assert GitRepository.discover(committed_repo).head_target_exists(RepoPath("dangling-link"))


def test_base_target_missing_is_false(committed_repo: Path) -> None:
    repository = GitRepository.discover(committed_repo)
    snapshot = repository.resolve_base("HEAD")
    assert not repository.base_target_exists(snapshot, RepoPath("missing/file.py"))


def test_base_target_inspection_failure_is_explicit(
    committed_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = GitRepository.discover(committed_repo)
    snapshot = repository.resolve_base("HEAD")

    def fail(*_args: str, **_kwargs):
        raise RepositoryError("BASE inspection failed")

    monkeypatch.setattr(repository, "_git", fail)
    with pytest.raises(RepositoryError, match="BASE inspection failed"):
        repository.base_target_exists(snapshot, RepoPath("src/auth/service.py"))


def test_missing_base_object_is_not_treated_as_an_absent_path(committed_repo: Path) -> None:
    blob = git(committed_repo, "rev-parse", "HEAD:src/auth/service.py")
    object_file = committed_repo / ".git" / "objects" / blob[:2] / blob[2:]
    object_file.unlink()
    repository = GitRepository.discover(committed_repo)

    with pytest.raises(RepositoryError):
        repository.base_target_exists(
            repository.resolve_base("HEAD"), RepoPath("src/auth/service.py")
        )


def test_tree_object_is_a_valid_base(committed_repo: Path) -> None:
    tree = git(committed_repo, "rev-parse", "HEAD^{tree}")
    repository = GitRepository.discover(committed_repo)
    snapshot = repository.resolve_base(tree)

    assert snapshot == tree
    assert [source.path.value for source in repository.base_instruction_sources(snapshot)] == [
        "AGENTS.md"
    ]
    assert repository.base_target_exists(snapshot, RepoPath("src/auth/service.py"))
