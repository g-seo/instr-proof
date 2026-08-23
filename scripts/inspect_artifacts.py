#!/usr/bin/env python3
"""Validate stable metadata and content invariants of release artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.message import Message
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
import argparse
import tarfile
import zipfile


@dataclass(frozen=True)
class ReleaseIdentity:
    name: str
    version: str


@dataclass(frozen=True)
class NormalizedMember:
    content: bytes
    mode: int


def normalized_member_records(path: Path) -> dict[str, NormalizedMember]:
    """Return stable member content and permission modes without extracting."""
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return {
                info.filename: NormalizedMember(
                    archive.read(info), (info.external_attr >> 16) & 0o777
                )
                for info in archive.infolist()
                if not info.is_dir()
            }
    if path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            result: dict[str, NormalizedMember] = {}
            for info in archive.getmembers():
                if not info.isfile():
                    continue
                stream = archive.extractfile(info)
                if stream is None:
                    raise ValueError(f"cannot read archive member: {info.name}")
                result[info.name] = NormalizedMember(stream.read(), info.mode & 0o777)
            if result:
                roots = {PurePosixPath(name).parts[0] for name in result}
                if len(roots) == 1:
                    root = next(iter(roots))
                    return {
                        str(PurePosixPath(name).relative_to(root)): record
                        for name, record in result.items()
                    }
            return result
    raise ValueError(f"unsupported artifact format: {path.name}")


def normalized_members(path: Path) -> dict[str, bytes]:
    """Return content by normalized member name, ignoring order and timestamps."""
    return {
        name: record.content
        for name, record in normalized_member_records(path).items()
    }


def _only_member(members: dict[str, bytes], suffix: str, label: str) -> tuple[str, bytes]:
    matches = [(name, content) for name, content in members.items() if name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"{label} must contain exactly one {suffix}")
    return matches[0]


def _parse_metadata(content: bytes, label: str) -> Message:
    message = BytesParser(policy=policy.default).parsebytes(content)
    required = {
        "Name": "instrproof",
        "Requires-Python": ">=3.12",
        "License-Expression": "Apache-2.0",
    }
    for field, expected in required.items():
        if message.get(field) != expected:
            raise ValueError(f"{label} metadata {field} must be {expected!r}")
    if not message.get("Version"):
        raise ValueError(f"{label} metadata Version is required")
    if not message.get("Summary"):
        raise ValueError(f"{label} metadata Summary is required")
    urls = set(message.get_all("Project-URL", []))
    expected_urls = {
        "Repository, https://github.com/g-seo/instr-proof",
        "Issues, https://github.com/g-seo/instr-proof/issues",
    }
    if not expected_urls.issubset(urls):
        raise ValueError(f"{label} metadata project URLs are incomplete")
    return message


def _assert_license(members: dict[str, bytes], names: list[str], label: str) -> None:
    matches = [members[name] for name in names if name.endswith("LICENSE")]
    if not matches:
        raise ValueError(f"{label} must include LICENSE")
    if not any(b"Apache License" in content and b"Version 2.0" in content for content in matches):
        raise ValueError(f"{label} LICENSE must contain Apache License 2.0")


def _inspect_wheel(path: Path) -> ReleaseIdentity:
    members = normalized_members(path)
    _, metadata_content = _only_member(members, ".dist-info/METADATA", "wheel")
    metadata = _parse_metadata(metadata_content, "wheel")
    _, entry_points = _only_member(
        members, ".dist-info/entry_points.txt", "wheel entry point"
    )
    if b"instrproof = instrproof.cli:main" not in entry_points:
        raise ValueError("wheel console entry point is missing")
    for package_file in ("instrproof/__init__.py", "instrproof/cli.py"):
        if package_file not in members:
            raise ValueError(f"wheel package file is missing: {package_file}")
    _assert_license(members, list(members), "wheel")
    return ReleaseIdentity(metadata["Name"], metadata["Version"])


def _inspect_sdist(path: Path) -> ReleaseIdentity:
    members = normalized_members(path)
    _, metadata_content = _only_member(members, "PKG-INFO", "source distribution")
    metadata = _parse_metadata(metadata_content, "source distribution")
    required = (
        "LICENSE",
        "README.md",
        "pyproject.toml",
        "src/instrproof/__init__.py",
        "src/instrproof/cli.py",
    )
    for member in required:
        if member not in members:
            raise ValueError(f"source distribution file is missing: {member}")
    if not any(name.startswith("scripts/") for name in members):
        raise ValueError("source distribution scripts are missing")
    if not any(name.startswith("tests/") for name in members):
        raise ValueError("source distribution tests are missing")
    _assert_license(members, list(members), "source distribution")
    return ReleaseIdentity(metadata["Name"], metadata["Version"])


def inspect_directory(directory: Path) -> ReleaseIdentity:
    wheels = sorted(directory.glob("*.whl"))
    sdists = sorted(directory.glob("*.tar.gz"))
    if len(wheels) != 1:
        raise ValueError("release directory must contain exactly one wheel")
    if len(sdists) != 1:
        raise ValueError("release directory must contain exactly one source distribution")
    wheel = _inspect_wheel(wheels[0])
    sdist = _inspect_sdist(sdists[0])
    if wheel.name != sdist.name:
        raise ValueError("artifact names differ")
    if wheel.version != sdist.version:
        raise ValueError("artifact versions differ")
    return wheel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        identity = inspect_directory(args.directory)
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"artifact validation failed: {exc}\n")
    print(f"Validated instrproof {identity.version} wheel and source distribution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
