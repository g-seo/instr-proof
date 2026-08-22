from pathlib import Path

import pytest

from instrproof.cli import main
from instrproof.repository import GitRepository, RepositoryError

from conftest import git


def test_new_command_dispatch_does_not_change_diff_output(
    committed_repo: Path, capsys
) -> None:
    assert main(["check"], cwd=committed_repo) == 0
    capsys.readouterr()
    assert main(["explain", "AGENTS.md:1"], cwd=committed_repo) == 0
    capsys.readouterr()

    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 0
    captured = capsys.readouterr()
    assert captured.out == "No instruction contract regressions found.\n"
    assert captured.err == ""


def commit_package_contract(repo: Path) -> None:
    (repo / "AGENTS.md").write_text("Run pnpm typecheck.\n", encoding="utf-8")
    (repo / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc --noEmit"}}\n', encoding="utf-8"
    )
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "package contract base")


def test_default_nested_instruction_source_reports_complete_path(git_repo: Path, capsys) -> None:
    source = git_repo / "packages" / "auth" / "AGENTS.md"
    source.parent.mkdir(parents=True)
    source.write_text("Use `src/service.py`.\n", encoding="utf-8")
    target = git_repo / "src" / "service.py"
    target.parent.mkdir()
    target.write_text("service\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "nested default")
    target.unlink()

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    assert "source=packages/auth/AGENTS.md:1  target=src/service.py" in capsys.readouterr().out


def test_configured_sources_flow_through_both_contract_extractors(git_repo: Path, capsys) -> None:
    rules = git_repo / ".claude" / "rules"
    rules.mkdir(parents=True)
    (rules / "paths.md").write_text("Use `src/service.py`.\n", encoding="utf-8")
    (rules / "scripts.md").write_text("Run pnpm typecheck.\n", encoding="utf-8")
    (git_repo / "instrproof.json").write_text(
        '{"instructions":[".claude/rules/**/*.md",".claude/rules/paths.md"]}\n',
        encoding="utf-8",
    )
    target = git_repo / "src" / "service.py"
    target.parent.mkdir()
    target.write_text("service\n", encoding="utf-8")
    (git_repo / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc"}}\n', encoding="utf-8"
    )
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "configured contracts")
    target.unlink()
    (git_repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    output = capsys.readouterr().out
    assert output.count("source=.claude/rules/paths.md") == 1
    assert "PathExists  source=.claude/rules/paths.md:1  target=src/service.py" in output
    assert "PackageScriptExists  source=.claude/rules/scripts.md:1  target=typecheck" in output


def test_zero_match_configuration_succeeds(git_repo: Path, capsys) -> None:
    (git_repo / "instrproof.json").write_text(
        '{"instructions":["missing/**/*.md"]}\n', encoding="utf-8"
    )
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "zero match")
    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_malformed_configuration_is_cli_error(git_repo: Path, capsys) -> None:
    (git_repo / "instrproof.json").write_text("{", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "bad config")
    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: instrproof.json is malformed JSON\n"


def test_configured_nested_source_preserves_both_path_resolution_bases(
    git_repo: Path, capsys
) -> None:
    source = git_repo / "packages" / "auth" / "instructions.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "See [architecture](docs/architecture.md).\nUse `docs/root-policy.md`.\n",
        encoding="utf-8",
    )
    (git_repo / "instrproof.json").write_text(
        '{"instructions":["packages/auth/instructions.md"]}\n', encoding="utf-8"
    )
    local_target = source.parent / "docs" / "architecture.md"
    local_target.parent.mkdir()
    local_target.write_text("architecture\n", encoding="utf-8")
    root_target = git_repo / "docs" / "root-policy.md"
    root_target.parent.mkdir()
    root_target.write_text("policy\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "nested resolution")
    local_target.unlink()
    root_target.unlink()

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    output = capsys.readouterr().out
    assert "target=packages/auth/docs/architecture.md" in output
    assert "target=docs/root-policy.md" in output


def test_configured_source_set_changes_use_existing_claim_survival(
    git_repo: Path, capsys
) -> None:
    instructions = git_repo / "instructions"
    instructions.mkdir()
    (instructions / "retained.md").write_text("Use `targets/retained.md`.\n", encoding="utf-8")
    (instructions / "deleted.md").write_text("Use `targets/deleted.md`.\n", encoding="utf-8")
    (instructions / "updated.md").write_text("Use `targets/old.md`.\n", encoding="utf-8")
    (git_repo / "instrproof.json").write_text(
        '{"instructions":["instructions/*.md"]}\n', encoding="utf-8"
    )
    targets = git_repo / "targets"
    targets.mkdir()
    for name in ("retained.md", "deleted.md", "old.md"):
        (targets / name).write_text(name + "\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "survival baseline")

    (targets / "retained.md").unlink()
    (targets / "deleted.md").unlink()
    (instructions / "deleted.md").unlink()
    (targets / "old.md").unlink()
    (targets / "new.md").write_text("new\n", encoding="utf-8")
    (instructions / "updated.md").write_text("Use `targets/new.md`.\n", encoding="utf-8")
    (instructions / "head-only.md").write_text("Use `targets/missing.md`.\n", encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    output = capsys.readouterr().out
    assert output.count("PathExists") == 1
    assert "source=instructions/retained.md:1  target=targets/retained.md" in output


def test_identical_targets_from_configured_sources_are_distinct_contracts(
    git_repo: Path, capsys
) -> None:
    instructions = git_repo / "instructions"
    instructions.mkdir()
    for name in ("first.md", "second.md"):
        (instructions / name).write_text("Use `targets/shared.md`.\n", encoding="utf-8")
    (git_repo / "instrproof.json").write_text(
        '{"instructions":["instructions/*.md"]}\n', encoding="utf-8"
    )
    target = git_repo / "targets" / "shared.md"
    target.parent.mkdir()
    target.write_text("shared\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "distinct sources")
    target.unlink()

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    output = capsys.readouterr().out
    assert "Found 2 instruction contract regressions:" in output
    assert "source=instructions/first.md:1" in output
    assert "source=instructions/second.md:1" in output


def test_package_script_exists_in_base_and_head_passes(git_repo: Path, capsys) -> None:
    commit_package_contract(git_repo)

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


@pytest.mark.parametrize("head_script", [None, "check-types"])
def test_reports_removed_or_renamed_package_script(
    git_repo: Path, capsys, head_script: str | None
) -> None:
    commit_package_contract(git_repo)
    scripts = {} if head_script is None else {head_script: "tsc --noEmit"}
    import json

    (git_repo / "package.json").write_text(
        json.dumps({"scripts": scripts}) + "\n", encoding="utf-8"
    )

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    captured = capsys.readouterr()
    assert captured.out == (
        "Found 1 instruction contract regression:\n"
        "PackageScriptExists  source=AGENTS.md:1  target=typecheck  "
        "base=present  head=missing\n"
    )
    assert captured.err == ""


def test_package_syntax_change_survives_and_reports_current_line(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("Run pnpm run typecheck.\n", encoding="utf-8")
    (git_repo / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc --noEmit"}}\n', encoding="utf-8"
    )
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base")
    (git_repo / "AGENTS.md").write_text(
        "Updated prose.\n\nRun yarn typecheck.\n", encoding="utf-8"
    )
    (git_repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    assert "source=AGENTS.md:3  target=typecheck" in capsys.readouterr().out


def test_coordinated_package_script_rename_passes(git_repo: Path, capsys) -> None:
    commit_package_contract(git_repo)
    (git_repo / "AGENTS.md").write_text("Run pnpm check-types.\n", encoding="utf-8")
    (git_repo / "package.json").write_text(
        '{"scripts":{"check-types":"tsc --noEmit"}}\n', encoding="utf-8"
    )

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_removed_package_instruction_retires_contract(git_repo: Path, capsys) -> None:
    commit_package_contract(git_repo)
    (git_repo / "AGENTS.md").write_text("No package command remains.\n", encoding="utf-8")
    (git_repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_path_regression_includes_diagnostic_evidence(committed_repo: Path, capsys) -> None:
    (committed_repo / "src" / "auth" / "service.py").unlink()

    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 1
    assert capsys.readouterr().out == (
        "Found 1 instruction contract regression:\n"
        "PathExists  source=AGENTS.md:1  target=src/auth/service.py  "
        "base=present  head=missing\n"
    )


def test_package_script_missing_in_base_is_not_monitored(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("Run pnpm typecheck.\n", encoding="utf-8")
    (git_repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "missing script")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_nested_package_script_is_not_base_evidence(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("Run pnpm typecheck.\n", encoding="utf-8")
    nested = git_repo / "packages" / "app"
    nested.mkdir(parents=True)
    (nested / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc"}}\n', encoding="utf-8"
    )
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "nested script")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_malformed_required_base_package_manifest_is_error(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text("Run pnpm typecheck.\n", encoding="utf-8")
    (git_repo / "package.json").write_text("{", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "malformed base")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: BASE package.json is malformed JSON\n"


def test_malformed_required_head_package_manifest_is_error(git_repo: Path, capsys) -> None:
    commit_package_contract(git_repo)
    (git_repo / "package.json").write_text("{", encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: HEAD package.json is malformed JSON\n"


def test_path_only_diff_does_not_read_unrelated_malformed_manifest(
    committed_repo: Path, capsys
) -> None:
    (committed_repo / "package.json").write_text("{", encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=committed_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_base_manifest_is_lazy_when_base_has_no_package_candidate(
    git_repo: Path, capsys
) -> None:
    (git_repo / "AGENTS.md").write_text("Use `src/service.py`.\n", encoding="utf-8")
    target = git_repo / "src" / "service.py"
    target.parent.mkdir()
    target.write_text("service\n", encoding="utf-8")
    (git_repo / "package.json").write_text("{", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "path-only malformed manifest")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_head_manifest_is_lazy_when_package_claim_does_not_survive(
    git_repo: Path, capsys
) -> None:
    commit_package_contract(git_repo)
    (git_repo / "AGENTS.md").write_text("Claim removed.\n", encoding="utf-8")
    (git_repo / "package.json").write_text("{", encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 0
    assert capsys.readouterr().out == "No instruction contract regressions found.\n"


def test_mixed_path_and_package_regressions_share_one_sorted_result(
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
    git(git_repo, "commit", "-qm", "mixed base")
    target.unlink()
    (git_repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    assert capsys.readouterr().out == (
        "Found 2 instruction contract regressions:\n"
        "PackageScriptExists  source=AGENTS.md:1  target=typecheck  "
        "base=present  head=missing\n"
        "PathExists  source=AGENTS.md:2  target=src/service.py  "
        "base=present  head=missing\n"
    )


def test_multiple_package_regressions_are_deterministic(git_repo: Path, capsys) -> None:
    (git_repo / "AGENTS.md").write_text(
        "Run pnpm z-check.\nRun yarn a-check.\nRun npm run z-check.\n",
        encoding="utf-8",
    )
    (git_repo / "package.json").write_text(
        '{"scripts":{"z-check":"z","a-check":"a"}}\n', encoding="utf-8"
    )
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "multiple package base")
    (git_repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

    assert main(["diff", "--base", "HEAD"], cwd=git_repo) == 1
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "Found 2 instruction contract regressions:"
    assert "target=a-check" in lines[1]
    assert "source=AGENTS.md:2" in lines[1]
    assert "target=z-check" in lines[2]
    assert "source=AGENTS.md:1" in lines[2]


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
        "PathExists  source=AGENTS.md:1  target=src/auth/service.py  "
        "base=present  head=missing\n"
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
    assert "source=docs/CLAUDE.md:1  target=docs/api.md" in capsys.readouterr().out


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
    assert "source=docs/agents/CLAUDE.md:1  target=docs/api.md" in capsys.readouterr().out


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
