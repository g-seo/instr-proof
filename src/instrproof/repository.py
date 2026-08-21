"""Git-tree and working-tree evidence access."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

from instrproof.models import InstructionSource, RepoPath


INSTRUCTION_NAMES = {"AGENTS.md", "CLAUDE.md"}


class RepositoryError(RuntimeError):
    """Raised when repository evidence cannot be inspected reliably."""


class GitRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._base_path_cache: dict[str, frozenset[RepoPath]] = {}

    @classmethod
    def discover(cls, cwd: Path | None = None) -> GitRepository:
        location = cwd or Path.cwd()
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=location,
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            raise RepositoryError(f"cannot execute Git: {exc}") from exc
        if result.returncode != 0:
            raise RepositoryError("not inside a Git working tree")
        try:
            root = Path(result.stdout.decode("utf-8").strip())
        except UnicodeDecodeError as exc:
            raise RepositoryError("Git returned an invalid repository path") from exc
        return cls(root)

    def _git(self, *args: str) -> bytes:
        try:
            result = subprocess.run(
                ["git", *args], cwd=self.root, capture_output=True, check=False
            )
        except OSError as exc:
            raise RepositoryError(f"cannot execute Git: {exc}") from exc
        if result.returncode == 0:
            return result.stdout
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RepositoryError(detail or f"Git command failed: {' '.join(args)}")

    def resolve_base(self, ref: str) -> str:
        if not ref or "\x00" in ref:
            raise RepositoryError("BASE ref is empty or invalid")
        output = self._git("rev-parse", "--verify", "--end-of-options", f"{ref}^{{tree}}")
        return output.decode("ascii").strip()

    def base_instruction_sources(self, snapshot: str) -> tuple[InstructionSource, ...]:
        output = self._git("ls-tree", "-rz", "--name-only", snapshot)
        paths: list[RepoPath] = []
        for raw in output.split(b"\0"):
            if not raw:
                continue
            try:
                path = RepoPath(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError) as exc:
                raise RepositoryError("BASE contains an unsupported path") from exc
            if path.name in INSTRUCTION_NAMES:
                paths.append(path)
        sources = []
        for path in sorted(paths):
            content = self._git("show", f"{snapshot}:{path.value}")
            try:
                decoded = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise RepositoryError(f"instruction is not valid UTF-8: {path.value}") from exc
            sources.append(InstructionSource(path, decoded))
        return tuple(sources)

    def base_target_exists(self, snapshot: str, path: RepoPath) -> bool:
        paths = self._base_path_cache.get(snapshot)
        if paths is None:
            output = self._git("ls-tree", "-rtz", "--name-only", snapshot)
            try:
                paths = frozenset(
                    RepoPath(raw.decode("utf-8")) for raw in output.split(b"\0") if raw
                )
            except (UnicodeDecodeError, ValueError) as exc:
                raise RepositoryError("BASE contains an unsupported path") from exc
            self._base_path_cache[snapshot] = paths
        if path not in paths:
            return False
        self._git("cat-file", "-e", f"{snapshot}:{path.value}")
        return True

    def head_instruction_sources(self) -> tuple[InstructionSource, ...]:
        output = self._git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
        paths: list[RepoPath] = []
        for raw in output.split(b"\0"):
            if not raw:
                continue
            try:
                path = RepoPath(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError) as exc:
                raise RepositoryError("working tree contains an unsupported path") from exc
            native = self.root.joinpath(*path.value.split("/"))
            if path.name in INSTRUCTION_NAMES and native.is_file():
                paths.append(path)
        sources = []
        for path in sorted(set(paths)):
            native = self.root.joinpath(*path.value.split("/"))
            try:
                content = native.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise RepositoryError(f"cannot read instruction: {path.value}") from exc
            sources.append(InstructionSource(path, content))
        return tuple(sources)

    def head_target_exists(self, path: RepoPath) -> bool:
        return os.path.lexists(self.root.joinpath(*path.value.split("/")))
