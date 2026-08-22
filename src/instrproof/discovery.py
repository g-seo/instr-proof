"""Deterministic selection of repository-relative instruction source paths."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from fnmatch import fnmatchcase
import re

from instrproof.models import RepoPath


DEFAULT_INSTRUCTION_NAMES = frozenset({"AGENTS.md", "CLAUDE.md"})
_DRIVE_PATH = re.compile(r"^[A-Za-z]:")
_GLOB_CHARACTERS = frozenset("*?[")


@dataclass(frozen=True)
class InstructionRule:
    written: str
    normalized: str
    is_glob: bool


@dataclass(frozen=True)
class InstructionDiscoveryConfig:
    additional_rules: tuple[InstructionRule, ...] = ()

    @classmethod
    def from_strings(cls, values: Iterable[str]) -> InstructionDiscoveryConfig:
        return cls(tuple(_instruction_rule(value) for value in values))


def _normalize_pattern(value: str) -> str:
    if not value or "\x00" in value or "\\" in value:
        raise ValueError("instruction pattern is empty or contains unsupported characters")
    if value.startswith(("/", "//")) or _DRIVE_PATH.match(value):
        raise ValueError("instruction pattern must be repository-relative")

    normalized: list[str] = []
    for segment in value.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if not normalized:
                raise ValueError("instruction pattern escapes the repository")
            normalized.pop()
            continue
        if "**" in segment and segment != "**":
            raise ValueError("** must occupy a complete path segment")
        _validate_brackets(segment)
        normalized.append(segment)
    if not normalized:
        raise ValueError("instruction pattern does not identify a repository file")
    return "/".join(normalized)


def _validate_brackets(segment: str) -> None:
    index = 0
    while index < len(segment):
        if segment[index] != "[":
            index += 1
            continue
        closing = segment.find("]", index + 1)
        if closing <= index + 1:
            raise ValueError("instruction pattern contains a malformed bracket expression")
        index = closing + 1


def _instruction_rule(value: str) -> InstructionRule:
    if not isinstance(value, str):
        raise ValueError("instruction rule must be a string")
    is_glob = any(character in value for character in _GLOB_CHARACTERS)
    if is_glob:
        normalized = _normalize_pattern(value)
    else:
        normalized = RepoPath(value).value
    return InstructionRule(value, normalized, is_glob)


def _glob_matches(pattern: str, path: str) -> bool:
    pattern_segments = pattern.split("/")
    path_segments = path.split("/")

    def match(pattern_index: int, path_index: int) -> bool:
        if pattern_index == len(pattern_segments):
            return path_index == len(path_segments)
        segment = pattern_segments[pattern_index]
        if segment == "**":
            return match(pattern_index + 1, path_index) or (
                path_index < len(path_segments) and match(pattern_index, path_index + 1)
            )
        return (
            path_index < len(path_segments)
            and fnmatchcase(path_segments[path_index], segment)
            and match(pattern_index + 1, path_index + 1)
        )

    return match(0, 0)


def discover_instruction_paths(
    paths: Iterable[RepoPath],
    config: InstructionDiscoveryConfig | None = None,
) -> tuple[RepoPath, ...]:
    rules = config.additional_rules if config is not None else ()
    discovered: set[RepoPath] = set()
    for path in paths:
        if path.name in DEFAULT_INSTRUCTION_NAMES or any(
            _glob_matches(rule.normalized, path.value)
            if rule.is_glob
            else rule.normalized == path.value
            for rule in rules
        ):
            discovered.add(path)
    return tuple(sorted(discovered))
