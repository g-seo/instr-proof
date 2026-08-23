"""Git-tree and working-tree evidence access for paths and root package scripts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from instrproof.discovery import (
    InstructionDiscoveryConfig,
    discover_instruction_paths,
)
from instrproof.models import InstructionSource, RepoPath


CONFIG_NAME = "instrproof.json"


class RepositoryError(RuntimeError):
    """Raised when repository evidence cannot be inspected reliably."""


class BaseReferenceError(RepositoryError):
    """Raised when the exact requested BASE reference cannot be resolved."""

    def __init__(self, requested_ref: str, detail: str) -> None:
        self.requested_ref = requested_ref
        self.detail = detail
        super().__init__(detail)


class GitRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._base_path_cache: dict[str, frozenset[RepoPath]] = {}
        self._base_package_script_cache: dict[str, frozenset[str]] = {}

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
            raise BaseReferenceError(ref, "BASE ref is empty or invalid")
        try:
            output = self._git(
                "rev-parse", "--verify", "--end-of-options", f"{ref}^{{tree}}"
            )
        except RepositoryError as exc:
            raise BaseReferenceError(ref, str(exc)) from exc
        return output.decode("ascii").strip()

    def instruction_discovery_config(self) -> InstructionDiscoveryConfig:
        config_path = self.root / CONFIG_NAME
        if not os.path.lexists(config_path):
            return InstructionDiscoveryConfig()
        try:
            content = config_path.read_bytes()
        except OSError as exc:
            raise RepositoryError(f"cannot read {CONFIG_NAME}") from exc
        try:
            document = json.loads(content.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise RepositoryError(f"{CONFIG_NAME} is not valid UTF-8") from exc
        except json.JSONDecodeError as exc:
            raise RepositoryError(f"{CONFIG_NAME} is malformed JSON") from exc
        if not isinstance(document, dict):
            raise RepositoryError(f"{CONFIG_NAME} root must be an object")
        unsupported = set(document) - {"instructions"}
        if unsupported:
            raise RepositoryError(f"{CONFIG_NAME} contains an unsupported key")
        instructions = document.get("instructions", [])
        if not isinstance(instructions, list):
            raise RepositoryError(f"{CONFIG_NAME} instructions must be an array")
        if any(not isinstance(value, str) for value in instructions):
            raise RepositoryError(f"{CONFIG_NAME} instruction entries must be strings")
        try:
            return InstructionDiscoveryConfig.from_strings(instructions)
        except ValueError as exc:
            raise RepositoryError(f"{CONFIG_NAME} has an invalid instruction rule: {exc}") from exc

    def base_instruction_sources(
        self,
        snapshot: str,
        config: InstructionDiscoveryConfig | None = None,
    ) -> tuple[InstructionSource, ...]:
        output = self._git("ls-tree", "-rz", "--name-only", snapshot)
        paths: list[RepoPath] = []
        for raw in output.split(b"\0"):
            if not raw:
                continue
            try:
                path = RepoPath(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError) as exc:
                raise RepositoryError("BASE contains an unsupported path") from exc
            paths.append(path)
        sources = []
        for path in discover_instruction_paths(paths, config):
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

    def head_instruction_sources(
        self, config: InstructionDiscoveryConfig | None = None
    ) -> tuple[InstructionSource, ...]:
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
            if native.is_file():
                paths.append(path)
        sources = []
        for path in discover_instruction_paths(paths, config):
            native = self.root.joinpath(*path.value.split("/"))
            try:
                content = native.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise RepositoryError(f"cannot read instruction: {path.value}") from exc
            sources.append(InstructionSource(path, content))
        return tuple(sources)

    def head_target_exists(self, path: RepoPath) -> bool:
        return os.path.lexists(self.root.joinpath(*path.value.split("/")))

    @staticmethod
    def _package_scripts(content: bytes, state: str) -> frozenset[str]:
        try:
            manifest = json.loads(content.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise RepositoryError(f"{state} package.json is not valid UTF-8") from exc
        except json.JSONDecodeError as exc:
            raise RepositoryError(f"{state} package.json is malformed JSON") from exc
        if not isinstance(manifest, dict):
            raise RepositoryError(f"{state} package.json root must be an object")
        scripts = manifest.get("scripts", {})
        if not isinstance(scripts, dict):
            raise RepositoryError(f"{state} package.json scripts must be an object")
        return frozenset(scripts)

    def base_package_scripts(self, snapshot: str) -> frozenset[str]:
        """Return exact root package script keys from a BASE Git tree."""
        cached = self._base_package_script_cache.get(snapshot)
        if cached is not None:
            return cached
        if not self.base_target_exists(snapshot, RepoPath("package.json")):
            scripts = frozenset()
        else:
            scripts = self._package_scripts(
                self._git("show", f"{snapshot}:package.json"), "BASE"
            )
        self._base_package_script_cache[snapshot] = scripts
        return scripts

    def head_package_scripts(self) -> frozenset[str]:
        """Return exact root package script keys from the working tree."""
        manifest = self.root / "package.json"
        if not manifest.is_file():
            return frozenset()
        try:
            content = manifest.read_bytes()
        except OSError as exc:
            raise RepositoryError("cannot read HEAD package.json") from exc
        return self._package_scripts(content, "HEAD")
