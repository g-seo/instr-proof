import pytest

from instrproof.discovery import InstructionDiscoveryConfig, discover_instruction_paths
from instrproof.models import RepoPath


def values(paths: tuple[RepoPath, ...]) -> list[str]:
    return [path.value for path in paths]


def test_default_discovery_selects_root_and_nested_names_in_sorted_order() -> None:
    paths = [
        RepoPath("z/CLAUDE.md"),
        RepoPath("README.md"),
        RepoPath("AGENTS.md"),
        RepoPath("a/deep/AGENTS.md"),
        RepoPath("CLAUDE.md"),
    ]

    assert values(discover_instruction_paths(paths)) == [
        "AGENTS.md",
        "CLAUDE.md",
        "a/deep/AGENTS.md",
        "z/CLAUDE.md",
    ]


def test_default_discovery_deduplicates_normalized_paths() -> None:
    paths = [RepoPath("docs//AGENTS.md"), RepoPath("docs/./AGENTS.md")]
    assert values(discover_instruction_paths(paths)) == ["docs/AGENTS.md"]


def test_exact_and_glob_rules_select_additional_sources_once() -> None:
    config = InstructionDiscoveryConfig.from_strings(
        [
            "docs//agent-instructions.md",
            ".claude/rules/**/*.md",
            ".claude/rules/**/*.md",
            "packages/auth/AGENTS.md",
        ]
    )
    paths = [
        RepoPath("docs/agent-instructions.md"),
        RepoPath(".claude/rules/local.md"),
        RepoPath(".claude/rules/packages/auth.md"),
        RepoPath("packages/auth/AGENTS.md"),
        RepoPath(".claude/RULES/not-matched.md"),
    ]

    assert values(discover_instruction_paths(paths, config)) == [
        ".claude/rules/local.md",
        ".claude/rules/packages/auth.md",
        "docs/agent-instructions.md",
        "packages/auth/AGENTS.md",
    ]


def test_zero_match_glob_contributes_no_source() -> None:
    config = InstructionDiscoveryConfig.from_strings(["missing/**/*.md"])
    assert discover_instruction_paths([RepoPath("README.md")], config) == ()


def test_zero_match_exact_rule_contributes_no_source() -> None:
    config = InstructionDiscoveryConfig.from_strings(["missing/instructions.md"])
    assert discover_instruction_paths([RepoPath("README.md")], config) == ()


def test_single_segment_question_and_bracket_globs_are_supported() -> None:
    config = InstructionDiscoveryConfig.from_strings(
        ["rules/team-?.md", "docs/[ab]-instructions.md"]
    )
    paths = [
        RepoPath("rules/team-a.md"),
        RepoPath("rules/team-long.md"),
        RepoPath("docs/a-instructions.md"),
        RepoPath("docs/c-instructions.md"),
    ]

    assert values(discover_instruction_paths(paths, config)) == [
        "docs/a-instructions.md",
        "rules/team-a.md",
    ]


@pytest.mark.parametrize(
    "value",
    ["", "/absolute.md", "C:/absolute.md", "../outside.md", "a\\b.md", "bad[.md", "a/**b/x.md", "a\x00b.md"],
)
def test_invalid_instruction_rule_is_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        InstructionDiscoveryConfig.from_strings([value])
