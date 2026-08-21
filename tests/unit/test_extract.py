from instrproof.extract import extract_path_claims
import pytest

from instrproof.models import ClaimForm, InstructionSource, RepoPath


def test_extracts_inline_path_relative_to_repository_root() -> None:
    source = InstructionSource(RepoPath("docs/AGENTS.md"), "Use `src/auth/service.py`.\n")
    claims = extract_path_claims(source)
    assert [(claim.form, claim.normalized_target.value) for claim in claims] == [
        (ClaimForm.INLINE_PATH, "src/auth/service.py")
    ]


def test_extracts_markdown_link_relative_to_instruction_document() -> None:
    source = InstructionSource(RepoPath("docs/CLAUDE.md"), "Read [API](api.md).\n")
    claims = extract_path_claims(source)
    assert [(claim.form, claim.normalized_target.value) for claim in claims] == [
        (ClaimForm.MARKDOWN_LINK, "docs/api.md")
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
        "Use `service.py`.\n",
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
