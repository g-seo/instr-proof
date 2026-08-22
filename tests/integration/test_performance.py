from __future__ import annotations

import json
import platform
from pathlib import Path
import subprocess
import sys
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
        for claim_index in range(5):
            relative = f"targets/group-{document_index:03}/file-{claim_index:02}.txt"
            claims.append(f"Use `{relative}`.")
            target = git_repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("evidence\n", encoding="utf-8")
        for script_index in range(5):
            claims.append(f"Run pnpm verify:{script_index}.")
        instruction_name = "AGENTS.md" if document_index % 2 == 0 else "rules.md"
        (directory / instruction_name).write_text(
            "\n".join(claims) + "\n", encoding="utf-8"
        )

    (git_repo / "instrproof.json").write_text(
        json.dumps({"instructions": ["instructions/**/rules.md"]}) + "\n",
        encoding="utf-8",
    )

    (git_repo / "package.json").write_text(
        json.dumps(
            {"scripts": {f"verify:{index}": f"verify command {index}" for index in range(5)}}
        )
        + "\n",
        encoding="utf-8",
    )

    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "performance fixture")

    git_version = subprocess.run(
        ["git", "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    environment = (
        f"python={sys.version.split()[0]}, platform={platform.platform()}, "
        f"git={git_version}"
    )

    check_started = monotonic()
    check_status = main(["check"], cwd=git_repo)
    check_elapsed = monotonic() - check_started

    assert check_status == 0
    assert capsys.readouterr().out.startswith(
        "Found 1000 verified instruction contracts:\n"
    )
    assert check_elapsed < 5.0, (
        f"current inspection took {check_elapsed:.3f}s; {environment}"
    )

    diff_started = monotonic()
    status = main(["diff", "--base", "HEAD"], cwd=git_repo)
    diff_elapsed = monotonic() - diff_started

    assert status == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"
    assert diff_elapsed < 5.0, f"comparison took {diff_elapsed:.3f}s; {environment}"
