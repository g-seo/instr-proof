"""Immutable domain values for instruction path contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import posixpath
import re


_DRIVE_PATH = re.compile(r"^[A-Za-z]:")


def normalize_repo_path(value: str) -> str:
    """Return a canonical Git-style repository-relative path."""
    if not value or "\x00" in value or "\\" in value:
        raise ValueError("repository path is empty or contains unsupported characters")
    if value.startswith(("/", "//")) or _DRIVE_PATH.match(value):
        raise ValueError("repository path must be relative")
    normalized = posixpath.normpath(value)
    if normalized in ("", ".", "..") or normalized.startswith("../"):
        raise ValueError("repository path escapes the repository")
    return normalized


@dataclass(frozen=True, order=True)
class RepoPath:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", normalize_repo_path(self.value))

    @property
    def name(self) -> str:
        return self.value.rsplit("/", 1)[-1]

    @property
    def parent(self) -> str:
        return self.value.rsplit("/", 1)[0] if "/" in self.value else ""

    def __str__(self) -> str:
        return self.value


class ClaimForm(StrEnum):
    INLINE_PATH = "INLINE_PATH"
    MARKDOWN_LINK = "MARKDOWN_LINK"


@dataclass(frozen=True)
class InstructionSource:
    path: RepoPath
    content: str

    def __post_init__(self) -> None:
        if self.path.name not in {"AGENTS.md", "CLAUDE.md"}:
            raise ValueError("unsupported instruction source")


@dataclass(frozen=True)
class PathClaim:
    source: RepoPath
    form: ClaimForm
    written_target: str
    normalized_target: RepoPath
    line: int | None = None


@dataclass(frozen=True, order=True)
class ContractIdentity:
    source: RepoPath
    contract_type: str
    target: RepoPath

    def __post_init__(self) -> None:
        if self.contract_type != "PathExists":
            raise ValueError("unsupported contract type")


@dataclass(frozen=True)
class PathExistsContract:
    identity: ContractIdentity


@dataclass(frozen=True)
class Regression:
    identity: ContractIdentity


@dataclass(frozen=True)
class ComparisonResult:
    baseline_contract_count: int
    regressions: tuple[Regression, ...]

    def __post_init__(self) -> None:
        if self.baseline_contract_count < 0:
            raise ValueError("baseline contract count cannot be negative")
