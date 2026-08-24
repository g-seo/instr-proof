"""Deterministic extraction of supported path and package-script claims."""

from __future__ import annotations

import posixpath
import re
from urllib.parse import urlsplit

from instrproof.models import (
    ClaimForm,
    InstructionSource,
    PackageManager,
    PackageScriptClaim,
    PathClaim,
    RepoPath,
)


_FENCE_OPEN = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})")
_MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")
_INLINE_CODE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
_INLINE_PATH = re.compile(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+")
_ROOT_FILENAME_CHARACTERS = re.compile(r"[A-Za-z0-9._-]+")
_ROOT_EXTENSION = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
SUPPORTED_EXTENSIONLESS_ROOT_FILENAMES = frozenset(
    {
        "Makefile",
        "Dockerfile",
        "Containerfile",
        "Justfile",
        "Procfile",
        "LICENSE",
        "NOTICE",
    }
)
PNPM_SHORTHAND_EXCLUSIONS = frozenset(
    {
        "add",
        "approve-builds",
        "audit",
        "bin",
        "completion",
        "config",
        "create",
        "deploy",
        "dlx",
        "env",
        "exec",
        "fetch",
        "help",
        "import",
        "init",
        "install",
        "link",
        "list",
        "outdated",
        "pack",
        "patch",
        "patch-commit",
        "patch-remove",
        "prune",
        "publish",
        "rebuild",
        "remove",
        "root",
        "self-update",
        "server",
        "setup",
        "store",
        "unlink",
        "update",
        "view",
        "why",
    }
)
YARN_SHORTHAND_EXCLUSIONS = frozenset(
    {
        "add",
        "bin",
        "cache",
        "completion",
        "config",
        "constraints",
        "create",
        "dedupe",
        "dlx",
        "exec",
        "explain",
        "help",
        "info",
        "init",
        "install",
        "link",
        "npm",
        "pack",
        "patch",
        "patch-commit",
        "plugin",
        "rebuild",
        "remove",
        "search",
        "set",
        "stage",
        "unlink",
        "unplug",
        "up",
        "upgrade",
        "version",
        "why",
        "workspace",
        "workspaces",
    }
)
_PACKAGE_SCRIPT_COMMAND = re.compile(
    r"(?P<prefix>^|[ \t\r\n`(\[{:])"
    r"(?P<manager>npm|pnpm|yarn)[ \t]+"
    r"(?:(?P<run>run)[ \t]+)?"
    r"(?P<script>[A-Za-z0-9](?:[A-Za-z0-9._:/-]*[A-Za-z0-9_:/-])?)"
    r"(?=$|[ \t\r\n`,)\]}!?.]|&&|\|\||;|\|)"
)


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _is_supported_root_filename(value: str) -> bool:
    """Return whether one inline token has the supported root-file shape."""
    if value in SUPPORTED_EXTENSIONLESS_ROOT_FILENAMES:
        return True
    if _ROOT_FILENAME_CHARACTERS.fullmatch(value) is None:
        return False
    stem, separator, extension = value.rpartition(".")
    return bool(stem and separator and _ROOT_EXTENSION.fullmatch(extension))


def _is_supported_inline_path(value: str) -> bool:
    return _INLINE_PATH.fullmatch(value) is not None or _is_supported_root_filename(value)


def _mask_fenced_blocks(text: str) -> str:
    """Mask fenced blocks while preserving offsets and line numbers."""
    masked: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        if fence_character is None:
            opening = _FENCE_OPEN.match(line)
            if opening is None:
                masked.append(line)
                continue
            fence = opening.group("fence")
            fence_character = fence[0]
            fence_length = len(fence)
        else:
            closing = re.match(
                rf"^[ \t]*{re.escape(fence_character)}{{{fence_length},}}[ \t]*(?:\r?\n)?$",
                line,
            )
            if closing is not None:
                fence_character = None
                fence_length = 0
        masked.append("".join(char if char in "\r\n" else " " for char in line))
    return "".join(masked)


def _resolve(target: str, source: RepoPath, *, markdown: bool) -> RepoPath | None:
    if not target or "\x00" in target or "\\" in target:
        return None
    candidate = target
    if markdown:
        candidate = candidate.strip()
        if candidate.startswith("<") and candidate.endswith(">"):
            candidate = candidate[1:-1]
        elif any(char.isspace() for char in candidate):
            return None
        parsed = urlsplit(candidate)
        if parsed.scheme or parsed.netloc or parsed.query or not parsed.path:
            return None
        candidate = parsed.path
    if candidate.startswith("/") or re.match(r"^[A-Za-z]:", candidate):
        return None
    joined = posixpath.join(source.parent, candidate) if markdown else candidate
    try:
        return RepoPath(joined)
    except ValueError:
        return None


def extract_path_claims(source: InstructionSource) -> tuple[PathClaim, ...]:
    """Extract supported claims from one instruction document."""
    text = _mask_fenced_blocks(source.content)
    claims: list[PathClaim] = []

    for match in _MARKDOWN_LINK.finditer(text):
        written = match.group(1)
        target = _resolve(written, source.path, markdown=True)
        if target is not None:
            claims.append(
                PathClaim(source.path, ClaimForm.MARKDOWN_LINK, written, target, _line_number(text, match.start()))
            )

    for match in _INLINE_CODE.finditer(text):
        written = match.group(1)
        if not _is_supported_inline_path(written):
            continue
        target = _resolve(written, source.path, markdown=False)
        if target is not None:
            claims.append(
                PathClaim(source.path, ClaimForm.INLINE_PATH, written, target, _line_number(text, match.start()))
            )

    return tuple(claims)


def extract_package_script_claims(
    source: InstructionSource,
) -> tuple[PackageScriptClaim, ...]:
    """Extract supported package-script command forms from one instruction."""
    text = _mask_fenced_blocks(source.content)
    claims: list[PackageScriptClaim] = []
    for match in _PACKAGE_SCRIPT_COMMAND.finditer(text):
        manager = PackageManager(match.group("manager"))
        explicit_run = match.group("run") is not None
        script = match.group("script")
        if manager is PackageManager.NPM and not explicit_run:
            continue
        if not explicit_run and (
            (manager is PackageManager.PNPM and script in PNPM_SHORTHAND_EXCLUSIONS)
            or (manager is PackageManager.YARN and script in YARN_SHORTHAND_EXCLUSIONS)
        ):
            continue
        claims.append(
            PackageScriptClaim(
                source.path,
                manager,
                text[match.start("manager") : match.end("script")],
                script,
                _line_number(text, match.start("manager")),
            )
        )
    return tuple(claims)
