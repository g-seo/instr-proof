from pathlib import Path

import pytest

from instrproof.cli import main
from instrproof.models import (
    ComparisonResult,
    ContractIdentity,
    ContractType,
    Regression,
    RepoPath,
)
from instrproof.repository import RepositoryError

from conftest import git


def commit_package_contract(repo: Path) -> None:
    (repo / "AGENTS.md").write_text("Run pnpm typecheck.\n", encoding="utf-8")
    (repo / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc --noEmit"}}\n', encoding="utf-8"
    )
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "package contract base")


def test_ci_pass_reports_zero_baseline_contracts(git_repo: Path, capsys) -> None:
    (git_repo / "README.md").write_text("base\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "empty contract base")

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=git_repo) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        "InstrProof ✓\n\n"
        "0 baseline contracts checked.\n"
        "No instruction contract regressions.\n"
    )
    assert captured.err == ""


def test_ci_pass_reports_nonzero_baseline_contracts(
    committed_repo: Path, capsys
) -> None:
    assert main(["diff", "--base", "HEAD", "--ci"], cwd=committed_repo) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        "InstrProof ✓\n\n"
        "1 baseline contracts checked.\n"
        "No instruction contract regressions.\n"
    )
    assert captured.err == ""


def test_ci_reports_one_path_regression(committed_repo: Path, capsys) -> None:
    (committed_repo / "src" / "auth" / "service.py").unlink()

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=committed_repo) == 1
    captured = capsys.readouterr()
    assert captured.out == (
        "InstrProof ✗\n\n"
        "1 instruction contract regression\n\n"
        "AGENTS.md:1\n"
        "PathExists(src/auth/service.py)\n"
    )
    assert captured.err == ""


def test_ci_reports_one_package_script_regression(git_repo: Path, capsys) -> None:
    commit_package_contract(git_repo)
    (git_repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=git_repo) == 1
    captured = capsys.readouterr()
    assert captured.out == (
        "InstrProof ✗\n\n"
        "1 instruction contract regression\n\n"
        "AGENTS.md:1\n"
        "PackageScriptExists(typecheck)\n"
    )
    assert captured.err == ""


def test_ci_reports_every_mixed_regression_with_status_one(
    git_repo: Path, capsys
) -> None:
    (git_repo / "AGENTS.md").write_text(
        "Run pnpm typecheck.\nUse `src/service.py`.\n", encoding="utf-8"
    )
    target = git_repo / "src" / "service.py"
    target.parent.mkdir()
    target.write_text("service\n", encoding="utf-8")
    (git_repo / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc --noEmit"}}\n', encoding="utf-8"
    )
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "mixed contract base")
    target.unlink()
    (git_repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=git_repo) == 1
    captured = capsys.readouterr()
    assert captured.out == (
        "InstrProof ✗\n\n"
        "2 instruction contract regressions\n\n"
        "AGENTS.md:1\n"
        "PackageScriptExists(typecheck)\n\n"
        "AGENTS.md:2\n"
        "PathExists(src/service.py)\n"
    )
    assert captured.out.count("PackageScriptExists(typecheck)") == 1
    assert captured.out.count("PathExists(src/service.py)") == 1
    assert captured.err == ""


@pytest.mark.parametrize("change", ["updated", "removed"])
def test_ci_preserves_coordinated_instruction_change_pass_decisions(
    committed_repo: Path, capsys, change: str
) -> None:
    old = committed_repo / "src" / "auth" / "service.py"
    old.unlink()
    if change == "updated":
        replacement = committed_repo / "src" / "auth" / "renamed.py"
        replacement.write_text("replacement\n", encoding="utf-8")
        (committed_repo / "AGENTS.md").write_text(
            "Use `src/auth/renamed.py`.\n", encoding="utf-8"
        )
    else:
        (committed_repo / "AGENTS.md").unlink()

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=committed_repo) == 0
    assert "No instruction contract regressions." in capsys.readouterr().out


def test_ci_invokes_shared_comparison_once(
    git_repo: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def compare_once(_repository, base_ref: str) -> ComparisonResult:
        nonlocal calls
        calls += 1
        assert base_ref == "HEAD"
        return ComparisonResult(0, ())

    monkeypatch.setattr("instrproof.cli.compare_repository", compare_once)

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=git_repo) == 0
    assert calls == 1
    assert "0 baseline contracts checked." in capsys.readouterr().out


def test_ci_regression_without_location_uses_source_only(
    git_repo: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    regression = Regression(
        ContractIdentity(
            RepoPath("docs/AGENTS.md"),
            ContractType.PATH_EXISTS,
            "src/service.py",
        )
    )
    monkeypatch.setattr(
        "instrproof.cli.compare_repository",
        lambda _repository, _base_ref: ComparisonResult(1, (regression,)),
    )

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=git_repo) == 1
    captured = capsys.readouterr()
    assert captured.out == (
        "InstrProof ✗\n\n"
        "1 instruction contract regression\n\n"
        "docs/AGENTS.md\n"
        "PathExists(src/service.py)\n"
    )
    assert captured.out.count("PathExists(src/service.py)") == 1
    assert captured.err == ""


def test_ci_output_order_is_stable_across_sources_types_and_targets(
    git_repo: Path, capsys
) -> None:
    sources = {
        "AGENTS.md": "Run pnpm typecheck.\nUse `targets/shared.py`.\n",
        "docs/AGENTS.md": "Use `targets/shared.py`.\n",
        "packages/app/AGENTS.md": "Use `targets/shared.py`.\n",
    }
    for relative, content in sources.items():
        source = git_repo / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(content, encoding="utf-8")
    target = git_repo / "targets" / "shared.py"
    target.parent.mkdir()
    target.write_text("shared\n", encoding="utf-8")
    (git_repo / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc"}}\n', encoding="utf-8"
    )
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "ordered contracts")
    target.unlink()
    (git_repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

    outputs = []
    for _ in range(3):
        assert main(["diff", "--base", "HEAD", "--ci"], cwd=git_repo) == 1
        captured = capsys.readouterr()
        assert captured.err == ""
        outputs.append(captured.out)

    assert outputs[0] == outputs[1] == outputs[2]
    assert outputs[0] == (
        "InstrProof ✗\n\n"
        "4 instruction contract regressions\n\n"
        "AGENTS.md:1\n"
        "PackageScriptExists(typecheck)\n\n"
        "AGENTS.md:2\n"
        "PathExists(targets/shared.py)\n\n"
        "docs/AGENTS.md:1\n"
        "PathExists(targets/shared.py)\n\n"
        "packages/app/AGENTS.md:1\n"
        "PathExists(targets/shared.py)\n"
    )


def test_ci_reports_one_hundred_regressions_once(git_repo: Path, capsys) -> None:
    targets = [f"targets/item-{index:03}.py" for index in range(100)]
    (git_repo / "AGENTS.md").write_text(
        "\n".join(f"Use `{target}`." for target in reversed(targets)) + "\n",
        encoding="utf-8",
    )
    for relative in targets:
        target = git_repo / relative
        target.parent.mkdir(exist_ok=True)
        target.write_text("present\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "one hundred contracts")
    for relative in targets:
        (git_repo / relative).unlink()

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=git_repo) == 1
    captured = capsys.readouterr()
    assert "100 instruction contract regressions\n" in captured.out
    for relative in targets:
        assert captured.out.count(f"PathExists({relative})") == 1
    assert captured.err == ""


@pytest.mark.parametrize("base_ref", ["missing-ref", "origin/main", "HEAD~1"])
def test_ci_unavailable_base_is_an_actionable_analysis_error(
    git_repo: Path, capsys, base_ref: str
) -> None:
    (git_repo / "README.md").write_text("only revision\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "single revision checkout")

    assert main(["diff", "--base", base_ref, "--ci"], cwd=git_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "InstrProof ✗\n\n"
        f"Analysis error: BASE reference '{base_ref}' is unavailable. "
        "Ensure the exact reference exists in the local checkout.\n"
    )
    assert "instruction contract regression" not in captured.err


def test_ci_malformed_required_data_is_an_analysis_error(
    git_repo: Path, capsys
) -> None:
    commit_package_contract(git_repo)
    (git_repo / "package.json").write_text("{", encoding="utf-8")

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=git_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "InstrProof ✗\n\n"
        "Analysis error: HEAD package.json is malformed JSON\n"
    )
    assert "instruction contract regression" not in captured.err


def test_ci_repository_failure_is_not_a_partial_regression_result(
    git_repo: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_repository, _base_ref: str) -> ComparisonResult:
        raise RepositoryError("repository comparison failed")

    monkeypatch.setattr("instrproof.cli.compare_repository", fail)

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=git_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "InstrProof ✗\n\n"
        "Analysis error: repository comparison failed\n"
    )
    assert "regression" not in captured.err.lower()


def test_ci_unexpected_failure_is_sanitized_analysis_error(
    git_repo: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_repository, _base_ref: str) -> ComparisonResult:
        raise RuntimeError("sensitive internal detail")

    monkeypatch.setattr("instrproof.cli.compare_repository", fail)

    assert main(["diff", "--base", "HEAD", "--ci"], cwd=git_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "InstrProof ✗\n\n"
        "Analysis error: internal analysis failure.\n"
    )
    assert "sensitive internal detail" not in captured.err
    assert "regression" not in captured.err.lower()


def test_non_ci_commands_remain_unchanged_after_ci_execution(
    committed_repo: Path, capsys
) -> None:
    assert main(["diff", "--base", "HEAD", "--ci"], cwd=committed_repo) == 0
    capsys.readouterr()

    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 0
    captured = capsys.readouterr()
    assert captured.out == "No instruction contract regressions found.\n"
    assert captured.err == ""

    assert main(["check"], cwd=committed_repo) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        "Found 1 verified instruction contract:\n"
        "PathExists  source=AGENTS.md:1  target=src/auth/service.py  "
        "current=present\n"
    )
    assert captured.err == ""

    assert main(["explain", "AGENTS.md:1"], cwd=committed_repo) == 0
    captured = capsys.readouterr()
    assert "Source\n  AGENTS.md:1" in captured.out
    assert "Type\n  PathExists" in captured.out
    assert "Target\n  src/auth/service.py" in captured.out
    assert "CURRENT\n  PRESENT" in captured.out
    assert captured.err == ""


def test_non_ci_diff_error_format_remains_unchanged_after_ci_error(
    committed_repo: Path, capsys
) -> None:
    assert main(["diff", "--base", "missing-ref", "--ci"], cwd=committed_repo) == 2
    capsys.readouterr()

    assert main(["diff", "--base", "missing-ref"], cwd=committed_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error:")
    assert "InstrProof" not in captured.err
