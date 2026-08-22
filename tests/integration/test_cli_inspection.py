from pathlib import Path

from instrproof.cli import main


def test_check_lists_present_contracts_across_discovered_sources(
    git_repo: Path, capsys
) -> None:
    (git_repo / "AGENTS.md").write_text(
        "Run pnpm typecheck.\nUse `src/missing.py`.\nMaybe update things.\n",
        encoding="utf-8",
    )
    nested = git_repo / "packages" / "auth" / "AGENTS.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("Use `src/service.py`.\n", encoding="utf-8")
    configured = git_repo / ".claude" / "rules" / "policy.md"
    configured.parent.mkdir(parents=True)
    configured.write_text("Use `docs/policy.md`.\n", encoding="utf-8")
    (git_repo / "instrproof.json").write_text(
        '{"instructions":[".claude/rules/*.md"]}\n', encoding="utf-8"
    )
    for target in ("src/service.py", "docs/policy.md"):
        path = git_repo / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("present\n", encoding="utf-8")
    (git_repo / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc"}}\n', encoding="utf-8"
    )

    assert main(["check"], cwd=git_repo) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == (
        "Found 3 verified instruction contracts:\n"
        "PathExists  source=.claude/rules/policy.md:1  target=docs/policy.md  current=present\n"
        "PackageScriptExists  source=AGENTS.md:1  target=typecheck  current=present\n"
        "PathExists  source=packages/auth/AGENTS.md:1  target=src/service.py  current=present\n"
    )
    assert "missing.py" not in captured.out


def test_check_deduplicates_identity_and_counts_other_sources_separately(
    git_repo: Path, capsys
) -> None:
    (git_repo / "AGENTS.md").write_text(
        "Use `docs/shared.md`.\nUse `docs/shared.md`.\n", encoding="utf-8"
    )
    nested = git_repo / "docs" / "AGENTS.md"
    nested.parent.mkdir()
    nested.write_text("Use `docs/shared.md`.\n", encoding="utf-8")
    (git_repo / "docs" / "shared.md").write_text("present\n", encoding="utf-8")

    assert main(["check"], cwd=git_repo) == 0
    output = capsys.readouterr().out
    assert output.startswith("Found 2 verified instruction contracts:\n")
    assert output.count("target=docs/shared.md") == 2


def test_check_zero_contracts_is_success(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("General guidance.\n", encoding="utf-8")

    assert main(["check"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "Found 0 verified instruction contracts.\n"


def test_check_reports_required_manifest_analysis_error(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("Run pnpm typecheck.\n", encoding="utf-8")
    (git_repo / "package.json").write_text("{", encoding="utf-8")

    assert main(["check"], cwd=git_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: HEAD package.json is malformed JSON\n"


def test_check_reports_unexpected_analysis_failure(
    git_repo: Path, capsys, monkeypatch
) -> None:
    def fail(_repository):
        raise RuntimeError("sensitive detail")

    monkeypatch.setattr("instrproof.cli.analyze_current_repository", fail)

    assert main(["check"], cwd=git_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: internal analysis failure\n"


def test_explain_present_and_missing_path_occurrences(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text(
        "Use `src/present.py`.\nUse `src/missing.py`.\n", encoding="utf-8"
    )
    present = git_repo / "src" / "present.py"
    present.parent.mkdir()
    present.write_text("present\n", encoding="utf-8")

    assert main(["explain", "AGENTS.md:1"], cwd=git_repo) == 0
    present_output = capsys.readouterr().out
    assert "Source\n  AGENTS.md:1" in present_output
    assert "Type\n  PathExists" in present_output
    assert "Target\n  src/present.py" in present_output
    assert "Evidence\n  src/present.py" in present_output
    assert "CURRENT\n  PRESENT" in present_output
    assert "BASE" not in present_output and "HEAD" not in present_output

    assert main(["explain", "AGENTS.md:2"], cwd=git_repo) == 0
    missing_output = capsys.readouterr().out
    assert "Target\n  src/missing.py" in missing_output
    assert "CURRENT\n  MISSING" in missing_output


def test_explain_present_and_missing_package_scripts(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text(
        "Run pnpm typecheck.\nRun npm run lint.\n", encoding="utf-8"
    )
    (git_repo / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc"}}\n', encoding="utf-8"
    )

    assert main(["explain", "AGENTS.md:1"], cwd=git_repo) == 0
    assert "Evidence\n  package.json:scripts.typecheck" in capsys.readouterr().out
    assert main(["explain", "AGENTS.md:2"], cwd=git_repo) == 0
    output = capsys.readouterr().out
    assert "Type\n  PackageScriptExists" in output
    assert "Evidence\n  package.json:scripts.lint" in output
    assert "CURRENT\n  MISSING" in output


def test_explain_configured_nested_source_and_multiple_matches(
    git_repo: Path, capsys
) -> None:
    source = git_repo / "rules" / "instructions.md"
    source.parent.mkdir()
    source.write_text(
        "Use `src/service.py` and run pnpm typecheck.\n", encoding="utf-8"
    )
    (git_repo / "instrproof.json").write_text(
        '{"instructions":["rules/instructions.md"]}\n', encoding="utf-8"
    )
    (git_repo / "src").mkdir()
    (git_repo / "src" / "service.py").write_text("present\n", encoding="utf-8")
    (git_repo / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc"}}\n', encoding="utf-8"
    )

    assert main(["explain", "rules/instructions.md:1"], cwd=git_repo) == 0
    output = capsys.readouterr().out
    assert output.count("Contract\n") == 2
    assert output.index("PackageScriptExists") < output.index("PathExists")
    assert output.count("rules/instructions.md:1") == 2


def test_explain_no_match_is_clear_status_one(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("General guidance.\n", encoding="utf-8")

    assert main(["explain", "AGENTS.md:1"], cwd=git_repo) == 1
    captured = capsys.readouterr()
    assert captured.out == "No supported instruction contract at AGENTS.md:1.\n"
    assert captured.err == ""


def test_explain_invalid_selector_is_status_two(git_repo: Path, capsys) -> None:
    assert main(["explain", "AGENTS.md:0"], cwd=git_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error: invalid source location")


def test_explain_propagates_required_data_and_hides_internal_failures(
    git_repo: Path, capsys, monkeypatch
) -> None:
    (git_repo / "AGENTS.md").write_text("Run pnpm typecheck.\n", encoding="utf-8")
    (git_repo / "package.json").write_text("{", encoding="utf-8")
    assert main(["explain", "AGENTS.md:1"], cwd=git_repo) == 2
    assert capsys.readouterr().err == "error: HEAD package.json is malformed JSON\n"

    def fail(_repository):
        raise RuntimeError("sensitive detail")

    monkeypatch.setattr("instrproof.cli.analyze_current_repository", fail)
    assert main(["explain", "AGENTS.md:1"], cwd=git_repo) == 2
    assert capsys.readouterr().err == "error: internal analysis failure\n"
