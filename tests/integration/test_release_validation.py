from pathlib import Path
import os
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate-release.sh"


def test_release_validator_has_valid_shell_syntax() -> None:
    result = subprocess.run(
        ("bash", "-n", str(SCRIPT)),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_release_validator_encodes_required_behavioral_phases() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    for phrase in (
        "Create clean development environment",
        "Run complete test suite",
        "Build wheel and source distribution",
        "Validate package metadata",
        "Inspect artifact contents",
        "Validate wheel installation",
        "Validate source distribution installation",
        "Compare artifact behavior",
    ):
        assert phrase in text

    assert "mktemp -d" in text
    assert "trap cleanup EXIT" in text
    assert "unset PYTHONPATH" in text
    assert "diff-regression" in text
    assert "expected_status=1" in text
    for name in (
        "strict-pass",
        "strict-regression",
        "strict-zero-contracts",
        "strict-analysis-error",
    ):
        assert name in text
    assert 'strict-pass 0' in text
    assert 'strict-regression 1' in text
    assert 'strict-zero-contracts 2' in text
    assert 'strict-analysis-error 2' in text


def test_release_validator_uses_explicit_artifacts_without_publishing() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    assert '"$wheel_path"' in text
    assert '"$sdist_path"' in text
    assert "twine check --strict" in text
    assert "uv build" in text
    assert "pip install instrproof" not in text
    assert "twine upload" not in text
    assert "uv publish" not in text
    assert "PYPI_TOKEN" not in text
    assert "rm -rf" not in text


def test_compare_mode_rejects_unequal_artifact_results(tmp_path: Path) -> None:
    wheel_results = tmp_path / "wheel-results"
    sdist_results = tmp_path / "sdist-results"
    wheel_results.mkdir()
    sdist_results.mkdir()
    (wheel_results / "version.stdout").write_text("instrproof 0.1.0\n")
    (sdist_results / "version.stdout").write_text("instrproof 9.9.9\n")

    result = subprocess.run(
        (str(SCRIPT), "--compare", str(wheel_results), str(sdist_results)),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Compare artifact behavior" in result.stdout
    assert "version.stdout" in result.stdout


def test_smoke_mode_rejects_installed_wheel_without_cli(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    environment = os.environ.copy()
    environment["INSTRPROOF_VALIDATION_PYTHON"] = "/usr/bin/python3"
    environment["UV_PYTHON_INSTALL_DIR"] = str(tmp_path / "managed-python")
    environment.setdefault("UV_CACHE_DIR", str(tmp_path / "uv-cache"))
    build = subprocess.run(
        ("uv", "build", "--wheel", "--out-dir", str(artifacts)),
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert build.returncode == 0, build.stderr
    wheel = next(artifacts.glob("*.whl"))
    with zipfile.ZipFile(wheel, "r") as source:
        members = {
            name: source.read(name)
            for name in source.namelist()
            if not name.endswith("entry_points.txt")
        }
    with zipfile.ZipFile(wheel, "w") as target:
        for name, content in members.items():
            target.writestr(name, content)

    result = subprocess.run(
        (str(SCRIPT), "--smoke", "wheel", str(wheel), str(tmp_path / "results")),
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Validate wheel installation" in result.stdout
    assert "instrproof" in result.stderr
