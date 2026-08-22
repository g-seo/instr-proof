"""Immutable domain values for typed instruction contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
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


class ContractType(StrEnum):
    PATH_EXISTS = "PathExists"
    PACKAGE_SCRIPT_EXISTS = "PackageScriptExists"


class PackageManager(StrEnum):
    NPM = "npm"
    PNPM = "pnpm"
    YARN = "yarn"


class EvidenceState(StrEnum):
    PRESENT = "present"
    MISSING = "missing"


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


@dataclass(frozen=True)
class PackageScriptClaim:
    source: RepoPath
    package_manager: PackageManager
    written_command: str
    normalized_target: str
    line: int | None = None

    def __post_init__(self) -> None:
        if not self.normalized_target:
            raise ValueError("package script target cannot be empty")
        if self.line is not None and self.line < 1:
            raise ValueError("source line must be positive")


@dataclass(frozen=True)
class SourceLocation:
    source: RepoPath
    line: int | None = None
    written_claim: str | None = None

    def __post_init__(self) -> None:
        if self.line is not None and self.line < 1:
            raise ValueError("source line must be positive")


@dataclass(frozen=True, order=True)
class ContractIdentity:
    source: RepoPath
    contract_type: ContractType
    target: str

    def __post_init__(self) -> None:
        if not isinstance(self.contract_type, ContractType):
            try:
                object.__setattr__(self, "contract_type", ContractType(self.contract_type))
            except ValueError as exc:
                raise ValueError("unsupported contract type") from exc
        if isinstance(self.target, RepoPath):
            object.__setattr__(self, "target", self.target.value)
        if not isinstance(self.target, str) or not self.target:
            raise ValueError("contract target cannot be empty")


@dataclass(frozen=True)
class PathExistsContract:
    identity: ContractIdentity
    base_location: SourceLocation | None = field(default=None, compare=False)


@dataclass(frozen=True)
class PackageScriptExistsContract:
    identity: ContractIdentity
    base_location: SourceLocation | None = field(default=None, compare=False)


@dataclass(frozen=True)
class Regression:
    identity: ContractIdentity
    base_location: SourceLocation | None = field(default=None, compare=False)
    head_location: SourceLocation | None = field(default=None, compare=False)
    base_evidence: EvidenceState | None = field(default=None, compare=False)
    head_evidence: EvidenceState | None = field(default=None, compare=False)


@dataclass(frozen=True)
class ComparisonResult:
    baseline_contract_count: int
    regressions: tuple[Regression, ...]

    def __post_init__(self) -> None:
        if self.baseline_contract_count < 0:
            raise ValueError("baseline contract count cannot be negative")
