from __future__ import annotations

from pathlib import Path
import subprocess

import pytest


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "instrproof@example.test")
    git(tmp_path, "config", "user.name", "InstrProof Test")
    return tmp_path


@pytest.fixture
def committed_repo(git_repo: Path) -> Path:
    (git_repo / "AGENTS.md").write_text("Use `src/auth/service.py`.\n", encoding="utf-8")
    target = git_repo / "src" / "auth" / "service.py"
    target.parent.mkdir(parents=True)
    target.write_text("# service\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base")
    return git_repo
