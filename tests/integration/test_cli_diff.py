from pathlib import Path

import pytest

from instrproof.cli import main
from instrproof.repository import GitRepository, RepositoryError

from conftest import git


def test_passes_when_target_remains(committed_repo: Path, capsys) -> None:
    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 0
    captured = capsys.readouterr()
    assert captured.out == "No instruction contract regressions found.\n"
    assert captured.err == ""


def test_reports_removed_inline_target(committed_repo: Path, capsys) -> None:
    (committed_repo / "src" / "auth" / "service.py").unlink()
    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 1
    captured = capsys.readouterr()
    assert captured.out == (
        "Found 1 instruction contract regression:\n"
        "PathExists  source=AGENTS.md  target=src/auth/service.py\n"
    )
    assert captured.err == ""


def test_reports_removed_nested_markdown_target(git_repo: Path, capsys) -> None:
    docs = git_repo / "docs"
    docs.mkdir()
    (docs / "CLAUDE.md").write_text("Read [API](api.md).\n", encoding="utf-8")
    (docs / "api.md").write_text("# API\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base")
    (docs / "api.md").unlink()

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    assert "source=docs/CLAUDE.md  target=docs/api.md" in capsys.readouterr().out


def test_regressions_are_sorted(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("`z/file.py` and `a/file.py`\n", encoding="utf-8")
    for name in ("z/file.py", "a/file.py"):
        target = git_repo / name
        target.parent.mkdir(exist_ok=True)
        target.write_text("x\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base")
    (git_repo / "z" / "file.py").unlink()
    (git_repo / "a" / "file.py").unlink()

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    lines = capsys.readouterr().out.splitlines()
    assert "target=a/file.py" in lines[1]
    assert "target=z/file.py" in lines[2]


def test_renamed_target_with_updated_instruction_passes(committed_repo: Path, capsys) -> None:
    old = committed_repo / "src" / "auth" / "service.py"
    new = committed_repo / "src" / "auth" / "renamed.py"
    old.rename(new)
    (committed_repo / "AGENTS.md").write_text("Use `src/auth/renamed.py`.\n", encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_removed_instruction_passes(committed_repo: Path, capsys) -> None:
    (committed_repo / "AGENTS.md").unlink()
    (committed_repo / "src" / "auth" / "service.py").unlink()

    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_moved_claim_keeps_identity(committed_repo: Path, capsys) -> None:
    (committed_repo / "AGENTS.md").write_text(
        "New surrounding prose.\n\nMore context.\nUse `src/auth/service.py` carefully.\n",
        encoding="utf-8",
    )
    (committed_repo / "src" / "auth" / "service.py").unlink()

    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 1
    assert "target=src/auth/service.py" in capsys.readouterr().out


def test_nonexistent_base_target_is_not_monitored(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("Use `missing/file.py`.\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_nested_link_resolves_dot_segments(git_repo: Path, capsys) -> None:
    nested = git_repo / "docs" / "agents"
    nested.mkdir(parents=True)
    (nested / "CLAUDE.md").write_text("Read [API](../api.md#usage).\n", encoding="utf-8")
    target = git_repo / "docs" / "api.md"
    target.write_text("# API\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base")
    target.unlink()

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    assert "source=docs/agents/CLAUDE.md  target=docs/api.md" in capsys.readouterr().out


def test_missing_base_argument_is_usage_error(capsys) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["diff"])
    assert raised.value.code == 2
    assert "--base" in capsys.readouterr().err


def test_non_repository_returns_operational_error(tmp_path: Path, capsys) -> None:
    assert main(["diff", "--base", "HEAD"], cwd=tmp_path) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error: not inside a Git working tree")


def test_invalid_base_ref_returns_operational_error(committed_repo: Path, capsys) -> None:
    assert main(["diff", "--base", "missing-ref"], cwd=committed_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error:")


def test_invalid_base_instruction_returns_operational_error(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_bytes(b"\xff")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "invalid instruction")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 2
    assert capsys.readouterr().err == "error: instruction is not valid UTF-8: AGENTS.md\n"


def test_invalid_head_instruction_returns_operational_error(committed_repo: Path, capsys) -> None:
    (committed_repo / "AGENTS.md").write_bytes(b"\xff")

    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 2
    assert capsys.readouterr().err == "error: cannot read instruction: AGENTS.md\n"


def test_unreadable_head_instruction_returns_operational_error(
    committed_repo: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path.read_text

    def fail_instruction(path: Path, *args, **kwargs):
        if path.name == "AGENTS.md":
            raise PermissionError("denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_instruction)
    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 2
    assert capsys.readouterr().err == "error: cannot read instruction: AGENTS.md\n"


def test_base_evidence_failure_returns_operational_error(
    committed_repo: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_repository: GitRepository, _snapshot: str, _path) -> bool:
        raise RepositoryError("BASE evidence inspection failed")

    monkeypatch.setattr(GitRepository, "base_target_exists", fail)
    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 2
    assert capsys.readouterr().err == "error: BASE evidence inspection failed\n"


def test_missing_base_object_returns_operational_error(committed_repo: Path, capsys) -> None:
    blob = git(committed_repo, "rev-parse", "HEAD:src/auth/service.py")
    object_file = committed_repo / ".git" / "objects" / blob[:2] / blob[2:]
    object_file.unlink()

    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error:")


def test_tree_object_base_is_accepted(committed_repo: Path, capsys) -> None:
    tree = git(committed_repo, "rev-parse", "HEAD^{tree}")
    assert main(["diff", "--base", tree], cwd=committed_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_file_replaced_by_directory_at_same_target_passes(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("Use `artifacts/item`.\n", encoding="utf-8")
    target = git_repo / "artifacts" / "item"
    target.parent.mkdir()
    target.write_text("file\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "file base")

    target.unlink()
    target.mkdir()
    (target / "child.txt").write_text("directory evidence\n", encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_directory_replaced_by_file_at_same_target_passes(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("Use `artifacts/item`.\n", encoding="utf-8")
    target = git_repo / "artifacts" / "item"
    target.mkdir(parents=True)
    (target / "child.txt").write_text("directory evidence\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "directory base")

    (target / "child.txt").unlink()
    target.rmdir()
    target.write_text("file\n", encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_head_only_instruction_cannot_create_regression(git_repo: Path, capsys) -> None:
    (git_repo / "README.md").write_text("base\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base without instructions")
    (git_repo / "AGENTS.md").write_text("Use `missing/file.py`.\n", encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"
