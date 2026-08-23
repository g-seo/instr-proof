from email.message import Message
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import io
import os
import subprocess
import sys
import tarfile
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = spec_from_file_location("inspect_artifacts", ROOT / "scripts/inspect_artifacts.py")
assert SPEC is not None and SPEC.loader is not None
inspect_artifacts = module_from_spec(SPEC)
sys.modules[SPEC.name] = inspect_artifacts
SPEC.loader.exec_module(inspect_artifacts)


def metadata(version: str = "0.1.0") -> bytes:
    return (
        "Metadata-Version: 2.4\n"
        "Name: instrproof\n"
        f"Version: {version}\n"
        "Summary: Detect broken instruction contracts\n"
        "Requires-Python: >=3.12\n"
        "License-Expression: Apache-2.0\n"
        "Project-URL: Repository, https://github.com/g-seo/instr-proof\n"
        "Project-URL: Issues, https://github.com/g-seo/instr-proof/issues\n"
        "\nDescription\n"
    ).encode()


def write_wheel(path: Path, *, version: str = "0.1.0", license_file: bool = True) -> None:
    dist_info = f"instrproof-{version}.dist-info"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("instrproof/__init__.py", f'__version__ = "{version}"\n')
        archive.writestr("instrproof/cli.py", "def main(): return 0\n")
        archive.writestr(f"{dist_info}/METADATA", metadata(version))
        archive.writestr(
            f"{dist_info}/entry_points.txt",
            "[console_scripts]\ninstrproof = instrproof.cli:main\n",
        )
        if license_file:
            archive.writestr(f"{dist_info}/licenses/LICENSE", "Apache License\nVersion 2.0")


def write_sdist(
    path: Path, *, version: str = "0.1.0", license_file: bool = True
) -> None:
    prefix = f"instrproof-{version}"
    members = {
        f"{prefix}/PKG-INFO": metadata(version),
        f"{prefix}/README.md": b"# InstrProof\n",
        f"{prefix}/pyproject.toml": b"[build-system]\n",
        f"{prefix}/src/instrproof/__init__.py": f'__version__ = "{version}"\n'.encode(),
        f"{prefix}/src/instrproof/cli.py": b"def main(): return 0\n",
        f"{prefix}/scripts/inspect_artifacts.py": b"pass\n",
        f"{prefix}/tests/test_example.py": b"pass\n",
    }
    if license_file:
        members[f"{prefix}/LICENSE"] = b"Apache License\nVersion 2.0"
    with tarfile.open(path, "w:gz") as archive:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mtime = 123
            archive.addfile(info, io.BytesIO(content))


def valid_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    wheel = tmp_path / "instrproof-0.1.0-py3-none-any.whl"
    sdist = tmp_path / "instrproof-0.1.0.tar.gz"
    write_wheel(wheel)
    write_sdist(sdist)
    return wheel, sdist


def rewrite_artifact(
    path: Path, *, remove_suffix: str | None = None,
    replace_suffix: str | None = None, replacement: bytes = b"",
) -> None:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path, "r") as source:
            members = {
                name: source.read(name)
                for name in source.namelist()
                if not name.endswith("/") and not (
                    remove_suffix and name.endswith(remove_suffix)
                )
            }
        with zipfile.ZipFile(path, "w") as target:
            for name, content in members.items():
                target.writestr(
                    name, replacement if replace_suffix and name.endswith(replace_suffix)
                    else content,
                )
        return

    with tarfile.open(path, "r:gz") as source:
        members = {
            info.name: (source.extractfile(info).read(), info.mode)
            for info in source.getmembers()
            if info.isfile() and not (
                remove_suffix and info.name.endswith(remove_suffix)
            )
        }
    with tarfile.open(path, "w:gz") as target:
        for name, (content, mode) in members.items():
            if replace_suffix and name.endswith(replace_suffix):
                content = replacement
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = mode
            target.addfile(info, io.BytesIO(content))


def test_valid_artifacts_have_matching_release_contract(tmp_path: Path) -> None:
    valid_artifacts(tmp_path)

    result = inspect_artifacts.inspect_directory(tmp_path)

    assert result.name == "instrproof"
    assert result.version == "0.1.0"


def test_rejects_unexpected_artifact_count(tmp_path: Path) -> None:
    valid_artifacts(tmp_path)
    write_wheel(tmp_path / "duplicate.whl")

    with pytest.raises(ValueError, match="exactly one wheel"):
        inspect_artifacts.inspect_directory(tmp_path)


@pytest.mark.parametrize("artifact", ["wheel", "sdist"])
def test_rejects_missing_license(tmp_path: Path, artifact: str) -> None:
    wheel, sdist = valid_artifacts(tmp_path)
    if artifact == "wheel":
        wheel.unlink()
        write_wheel(wheel, license_file=False)
    else:
        sdist.unlink()
        write_sdist(sdist, license_file=False)

    with pytest.raises(ValueError, match="LICENSE"):
        inspect_artifacts.inspect_directory(tmp_path)


def test_rejects_mismatched_versions(tmp_path: Path) -> None:
    wheel, sdist = valid_artifacts(tmp_path)
    sdist.unlink()
    write_sdist(sdist, version="0.2.0")

    with pytest.raises(ValueError, match="versions differ"):
        inspect_artifacts.inspect_directory(tmp_path)


def test_rejects_missing_entry_point(tmp_path: Path) -> None:
    wheel, _ = valid_artifacts(tmp_path)
    with zipfile.ZipFile(wheel, "r") as source:
        members = {name: source.read(name) for name in source.namelist() if not name.endswith("entry_points.txt")}
    with zipfile.ZipFile(wheel, "w") as target:
        for name, content in members.items():
            target.writestr(name, content)

    with pytest.raises(ValueError, match="entry point"):
        inspect_artifacts.inspect_directory(tmp_path)


@pytest.mark.parametrize(
    ("artifact", "metadata_name"), (("wheel", "METADATA"), ("sdist", "PKG-INFO"))
)
def test_rejects_missing_core_metadata(
    tmp_path: Path, artifact: str, metadata_name: str
) -> None:
    wheel, sdist = valid_artifacts(tmp_path)
    rewrite_artifact(
        wheel if artifact == "wheel" else sdist, remove_suffix=metadata_name
    )

    with pytest.raises(ValueError, match=metadata_name):
        inspect_artifacts.inspect_directory(tmp_path)


@pytest.mark.parametrize(
    ("artifact", "metadata_name"), (("wheel", "METADATA"), ("sdist", "PKG-INFO"))
)
def test_rejects_invalid_required_metadata(
    tmp_path: Path, artifact: str, metadata_name: str
) -> None:
    wheel, sdist = valid_artifacts(tmp_path)
    invalid = metadata().replace(b"Requires-Python: >=3.12", b"Requires-Python: >=3.11")
    rewrite_artifact(
        wheel if artifact == "wheel" else sdist,
        replace_suffix=metadata_name,
        replacement=invalid,
    )

    with pytest.raises(ValueError, match="Requires-Python"):
        inspect_artifacts.inspect_directory(tmp_path)


@pytest.mark.parametrize(
    ("artifact", "package_file"),
    (("wheel", "instrproof/cli.py"), ("sdist", "src/instrproof/cli.py")),
)
def test_rejects_missing_required_package_file(
    tmp_path: Path, artifact: str, package_file: str
) -> None:
    wheel, sdist = valid_artifacts(tmp_path)
    rewrite_artifact(
        wheel if artifact == "wheel" else sdist, remove_suffix=package_file
    )

    with pytest.raises(ValueError, match="file is missing"):
        inspect_artifacts.inspect_directory(tmp_path)


def test_normalization_ignores_archive_order_and_timestamps(tmp_path: Path) -> None:
    first = tmp_path / "first.whl"
    second = tmp_path / "second.whl"
    members = {"a.txt": b"a", "b.txt": b"b"}
    with zipfile.ZipFile(first, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    with zipfile.ZipFile(second, "w") as archive:
        for name, content in reversed(tuple(members.items())):
            info = zipfile.ZipInfo(name, date_time=(2025, 2, 3, 4, 5, 6))
            archive.writestr(info, content)

    assert inspect_artifacts.normalized_members(first) == inspect_artifacts.normalized_members(second)


def test_independent_builds_have_equivalent_stable_members(tmp_path: Path) -> None:
    build_dirs = (tmp_path / "first", tmp_path / "second")
    environment = os.environ.copy()
    environment.setdefault("UV_CACHE_DIR", str(tmp_path / "uv-cache"))
    for output_dir in build_dirs:
        result = subprocess.run(
            ("uv", "build", "--out-dir", str(output_dir)),
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr

    for pattern in ("*.whl", "*.tar.gz"):
        first = next(build_dirs[0].glob(pattern))
        second = next(build_dirs[1].glob(pattern))
        assert inspect_artifacts.normalized_member_records(first) == (
            inspect_artifacts.normalized_member_records(second)
        )
