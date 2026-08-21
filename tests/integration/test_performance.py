from __future__ import annotations

from pathlib import Path
from time import monotonic

from instrproof.cli import main

from conftest import git


def test_100_documents_and_1000_candidates_complete_within_five_seconds(
    git_repo: Path, capsys
) -> None:
    for document_index in range(100):
        directory = git_repo / "instructions" / f"group-{document_index:03}"
        directory.mkdir(parents=True)
        claims = []
        for claim_index in range(10):
            relative = f"targets/group-{document_index:03}/file-{claim_index:02}.txt"
            claims.append(f"Use `{relative}`.")
            target = git_repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("evidence\n", encoding="utf-8")
        (directory / "AGENTS.md").write_text("\n".join(claims) + "\n", encoding="utf-8")

    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "performance fixture")

    started = monotonic()
    status = main(["diff", "--base", "HEAD"], cwd=git_repo)
    elapsed = monotonic() - started

    assert status == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"
    assert elapsed < 5.0, f"comparison took {elapsed:.3f}s"
