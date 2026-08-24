from instrproof.extract import (
    PNPM_SHORTHAND_EXCLUSIONS,
    YARN_SHORTHAND_EXCLUSIONS,
    _is_supported_root_filename,
    extract_package_script_claims,
    extract_path_claims,
)
import pytest

from instrproof.models import ClaimForm, InstructionSource, RepoPath


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("npm run typecheck", "typecheck"),
        ("pnpm typecheck", "typecheck"),
        ("pnpm run test:unit", "test:unit"),
        ("yarn lint-fix", "lint-fix"),
        ("yarn run build_2.docs/client", "build_2.docs/client"),
    ],
)
def test_extracts_supported_package_script_forms(command: str, expected: str) -> None:
    source = InstructionSource(RepoPath("AGENTS.md"), f"Run `{command}`.\n")
    claims = extract_package_script_claims(source)

    assert [(claim.package_manager.value, claim.normalized_target) for claim in claims] == [
        (command.split()[0], expected)
    ]
    assert claims[0].line == 1


@pytest.mark.parametrize("prefix", ["", " ", "\t", "\n", "`", "(", "[", "{", ":"])
def test_package_command_allowed_start_boundaries(prefix: str) -> None:
    suffix = "`" if prefix == "`" else "."
    source = InstructionSource(RepoPath("AGENTS.md"), f"{prefix}pnpm typecheck{suffix}")
    assert [c.normalized_target for c in extract_package_script_claims(source)] == [
        "typecheck"
    ]


@pytest.mark.parametrize(
    "suffix",
    ["", " ", "\t", "\r", "\n", "`", ",", ")", "]", "}", "!", "?", ".", "&&next", "||next", ";next", "|next"],
)
def test_package_script_exact_termination_boundaries(suffix: str) -> None:
    source = InstructionSource(RepoPath("AGENTS.md"), f"pnpm typecheck{suffix}")
    assert [c.normalized_target for c in extract_package_script_claims(source)] == [
        "typecheck"
    ]


def test_whitespace_and_operators_terminate_without_semantic_parsing() -> None:
    source = InstructionSource(
        RepoPath("AGENTS.md"),
        "pnpm typecheck --watch && yarn test:unit || npm run lint; pnpm build | tool",
    )
    assert [c.normalized_target for c in extract_package_script_claims(source)] == [
        "typecheck",
        "test:unit",
        "lint",
        "build",
    ]


@pytest.mark.parametrize(
    "content",
    [
        "xpnpm typecheck",
        "pnpm typecheck&next",
        "pnpm typecheck@next",
        "pnpm typecheck#next",
        "pnpm typecheck=next",
        "pnpm typecheck>next",
        "pnpm typecheck<next",
        'pnpm "typecheck"',
        "npm typecheck",
        "```sh\npnpm typecheck\n```",
    ],
)
def test_rejects_invalid_package_command_boundaries(content: str) -> None:
    source = InstructionSource(RepoPath("AGENTS.md"), content)
    assert extract_package_script_claims(source) == ()


def test_shorthand_exclusion_sets_are_exact_and_all_entries_are_rejected() -> None:
    expected_pnpm = frozenset(
        "add approve-builds audit bin completion config create deploy dlx env exec "
        "fetch help import init install link list outdated pack patch patch-commit "
        "patch-remove prune publish rebuild remove root self-update server setup store "
        "unlink update view why".split()
    )
    expected_yarn = frozenset(
        "add bin cache completion config constraints create dedupe dlx exec explain help "
        "info init install link npm pack patch patch-commit plugin rebuild remove search "
        "set stage unlink unplug up upgrade version why workspace workspaces".split()
    )
    assert PNPM_SHORTHAND_EXCLUSIONS == expected_pnpm
    assert YARN_SHORTHAND_EXCLUSIONS == expected_yarn
    for manager, exclusions in (
        ("pnpm", expected_pnpm),
        ("yarn", expected_yarn),
    ):
        source = InstructionSource(
            RepoPath("AGENTS.md"),
            "\n".join(f"{manager} {command}" for command in sorted(exclusions)),
        )
        assert extract_package_script_claims(source) == ()


def test_explicit_run_bypasses_shorthand_exclusions() -> None:
    source = InstructionSource(
        RepoPath("AGENTS.md"), "pnpm run install\nyarn run add\n"
    )
    assert [c.normalized_target for c in extract_package_script_claims(source)] == [
        "install",
        "add",
    ]


def test_extracts_inline_path_relative_to_repository_root() -> None:
    source = InstructionSource(RepoPath("docs/AGENTS.md"), "Use `src/auth/service.py`.\n")
    claims = extract_path_claims(source)
    assert [(claim.form, claim.normalized_target.value) for claim in claims] == [
        (ClaimForm.INLINE_PATH, "src/auth/service.py")
    ]


@pytest.mark.parametrize(
    "filename",
    [
        "README.md",
        "Cargo.toml",
        "package.json",
        "pyproject.toml",
        ".pre-commit-config.yaml",
        "Makefile",
        "Dockerfile",
        "Containerfile",
        "Justfile",
        "Procfile",
        "LICENSE",
        "NOTICE",
    ],
)
def test_supports_root_level_inline_filenames(filename: str) -> None:
    assert _is_supported_root_filename(filename)
    source = InstructionSource(RepoPath("AGENTS.md"), f"Use `{filename}`.\n")

    claims = extract_path_claims(source)

    assert [(claim.form, claim.normalized_target.value) for claim in claims] == [
        (ClaimForm.INLINE_PATH, filename)
    ]


@pytest.mark.parametrize(
    "value",
    [
        "pytest",
        "src",
        "main",
        "build",
        "README",
        "v1.0",
        "python3.12",
        "https://example.com/README.md",
        "README.md#usage",
        "README.md?raw=1",
        "*.md",
        "README?.md",
        "${CONFIG}",
        "${CONFIG}.json",
        "$(config).json",
        "$CONFIG.json",
        "README.md;rm",
        "path with spaces.md",
        "/README.md",
        "C:/README.md",
        "dir\\README.md",
        "README\x00.md",
    ],
)
def test_rejects_unsupported_root_filename_shapes(value: str) -> None:
    assert not _is_supported_root_filename(value)
    source = InstructionSource(RepoPath("AGENTS.md"), f"Use `{value}`.\n")

    assert extract_path_claims(source) == ()


def test_root_filename_support_preserves_fences_nested_paths_and_markdown_links() -> None:
    source = InstructionSource(
        RepoPath("docs/AGENTS.md"),
        "```md\nRead `README.md`.\n```\n"
        "Use `src/app.py`.\n"
        "Read [API](api.md).\n",
    )

    claims = extract_path_claims(source)

    assert [(claim.form, claim.normalized_target.value) for claim in claims] == [
        (ClaimForm.MARKDOWN_LINK, "docs/api.md"),
        (ClaimForm.INLINE_PATH, "src/app.py"),
    ]


def test_extracts_markdown_link_relative_to_instruction_document() -> None:
    source = InstructionSource(RepoPath("docs/CLAUDE.md"), "Read [API](api.md).\n")
    claims = extract_path_claims(source)
    assert [(claim.form, claim.normalized_target.value) for claim in claims] == [
        (ClaimForm.MARKDOWN_LINK, "docs/api.md")
    ]


def test_custom_nested_source_preserves_both_path_resolution_bases() -> None:
    source = InstructionSource(
        RepoPath("packages/auth/instructions.md"),
        "See [architecture](docs/architecture.md).\nUse `docs/root-policy.md`.\n",
    )

    assert [claim.normalized_target.value for claim in extract_path_claims(source)] == [
        "packages/auth/docs/architecture.md",
        "docs/root-policy.md",
    ]


def test_ignores_plain_path_like_prose() -> None:
    source = InstructionSource(RepoPath("AGENTS.md"), "Maybe src/auth/service.py is relevant.\n")
    assert extract_path_claims(source) == ()


@pytest.mark.parametrize(
    "content",
    [
        "```\n`src/example.py`\n```\n",
        "~~~md\n[API](api.md)\n~~~\n",
        "Plain src/example.py prose.\n",
        "Use `src/path with spaces.py`.\n",
        "[External](https://example.com/api.md)\n",
        "[Network](//example.com/api.md)\n",
        "[Absolute](/api.md)\n",
        "[Fragment](#api)\n",
        "[Query](api.md?raw=1)\n",
        "![Image](image.png)\n",
        "[Escape](../../api.md)\n",
        "Use `../outside.py`.\n",
        "Use `C:/outside.py`.\n",
        "Use `src\\windows.py`.\n",
        "Use `src/evil\x00.py`.\n",
    ],
)
def test_rejects_unsupported_or_low_confidence_candidates(content: str) -> None:
    source = InstructionSource(RepoPath("docs/AGENTS.md"), content)
    assert extract_path_claims(source) == ()


@pytest.mark.parametrize(
    ("destination", "expected"),
    [
        ("./api.md", "docs/api.md"),
        ("../api.md", "api.md"),
        ("api.md#section", "docs/api.md"),
        ("<api.md>", "docs/api.md"),
    ],
)
def test_normalizes_supported_markdown_destinations(destination: str, expected: str) -> None:
    source = InstructionSource(RepoPath("docs/CLAUDE.md"), f"[API]({destination})\n")
    assert [claim.normalized_target.value for claim in extract_path_claims(source)] == [expected]


@pytest.mark.parametrize(
    "content",
    [
        "```md\n[API](api.md)\n",
        "```md\n[API](api.md)\n````\n",
        "~~~~\n`src/example.py`\n~~~~~\n",
    ],
)
def test_ignores_claims_in_unterminated_or_longer_closed_fences(content: str) -> None:
    source = InstructionSource(RepoPath("docs/AGENTS.md"), content)
    assert extract_path_claims(source) == ()
