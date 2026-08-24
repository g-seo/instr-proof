from pathlib import Path
import os
import subprocess
import sys

import pytest

from instrproof import __version__


ROOT = Path(__file__).resolve().parents[2]


def run(*args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )


def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["UV_CACHE_DIR"] = str(Path(os.environ.get("UV_CACHE_DIR", "/tmp/instrproof-test-cache")))
    return env


@pytest.fixture(scope="module")
def built_artifacts(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    output = tmp_path_factory.mktemp("artifacts")
    result = run("uv", "build", "--out-dir", str(output), cwd=ROOT, env=clean_env())
    assert result.returncode == 0, result.stderr
    wheels = list(output.glob("*.whl"))
    sdists = list(output.glob("*.tar.gz"))
    assert len(wheels) == 1
    assert len(sdists) == 1
    return wheels[0], sdists[0]


def assert_installed_cli(artifact: Path, tmp_path: Path) -> None:
    env = clean_env()
    venv = tmp_path / "venv"
    neutral = tmp_path / "outside-repository"
    neutral.mkdir()
    assert run("uv", "venv", "--python", sys.executable, str(venv), cwd=neutral, env=env).returncode == 0
    python = venv / "bin/python"
    cli = venv / "bin/instrproof"
    install = run(
        "uv", "pip", "install", "--offline", "--python", str(python),
        str(artifact), cwd=neutral, env=env
    )
    assert install.returncode == 0, install.stderr

    help_result = run(str(cli), "--help", cwd=neutral, env=env)
    assert help_result.returncode == 0
    assert "check" in help_result.stdout
    assert "diff" in help_result.stdout

    diff_help = run(str(cli), "diff", "--help", cwd=neutral, env=env)
    assert diff_help.returncode == 0
    assert "--require-contracts" in diff_help.stdout

    version_result = run(str(cli), "--version", cwd=neutral, env=env)
    assert version_result.returncode == 0
    assert version_result.stdout == f"instrproof {__version__}\n"

    imported = run(
        str(python),
        "-I",
        "-c",
        "import instrproof; print(instrproof.__version__); print(instrproof.__file__)",
        cwd=neutral,
        env=env,
    )
    assert imported.returncode == 0
    lines = imported.stdout.splitlines()
    assert lines[0] == __version__
    assert str(venv) in lines[1]
    assert str(ROOT) not in lines[1]

    repository = tmp_path / "strict-repository"
    repository.mkdir()
    (repository / "AGENTS.md").write_text("Use `src/app.py`.\n", encoding="utf-8")
    target = repository / "src" / "app.py"
    target.parent.mkdir()
    target.write_text("app\n", encoding="utf-8")
    for command in (
        ("git", "init", "-q"),
        ("git", "config", "user.email", "instrproof@example.test"),
        ("git", "config", "user.name", "InstrProof Test"),
        ("git", "add", "."),
        ("git", "commit", "-qm", "strict fixture"),
    ):
        result = run(*command, cwd=repository, env=env)
        assert result.returncode == 0, result.stderr

    strict_pass = run(
        str(cli), "diff", "--base", "HEAD", "--ci", "--require-contracts",
        cwd=repository, env=env,
    )
    assert strict_pass.returncode == 0
    assert strict_pass.stdout == (
        "InstrProof ✓\n\n"
        "1 baseline contracts checked.\n"
        "No instruction contract regressions.\n"
    )
    assert strict_pass.stderr == ""

    target.unlink()
    strict_regression = run(
        str(cli), "diff", "--base", "HEAD", "--ci", "--require-contracts",
        cwd=repository, env=env,
    )
    assert strict_regression.returncode == 1
    assert strict_regression.stdout == (
        "InstrProof ✗\n\n"
        "1 instruction contract regression\n\n"
        "AGENTS.md:1\n"
        "PathExists(src/app.py)\n"
    )
    assert strict_regression.stderr == ""

    analysis_error = run(
        str(cli), "diff", "--base", "missing-ref", "--ci", "--require-contracts",
        cwd=repository, env=env,
    )
    assert analysis_error.returncode == 2
    assert analysis_error.stdout == ""
    assert analysis_error.stderr == (
        "InstrProof ✗\n\n"
        "Analysis error: BASE reference 'missing-ref' is unavailable. Ensure the "
        "exact reference exists in the local checkout.\n"
    )

    empty_repository = tmp_path / "empty-repository"
    empty_repository.mkdir()
    (empty_repository / "README.md").write_text("empty\n", encoding="utf-8")
    for command in (
        ("git", "init", "-q"),
        ("git", "config", "user.email", "instrproof@example.test"),
        ("git", "config", "user.name", "InstrProof Test"),
        ("git", "add", "."),
        ("git", "commit", "-qm", "empty fixture"),
    ):
        result = run(*command, cwd=empty_repository, env=env)
        assert result.returncode == 0, result.stderr

    zero_contracts = run(
        str(cli), "diff", "--base", "HEAD", "--ci", "--require-contracts",
        cwd=empty_repository, env=env,
    )
    assert zero_contracts.returncode == 2
    assert zero_contracts.stdout == ""
    assert zero_contracts.stderr == (
        "InstrProof ✗\n\n"
        "Analysis error: no baseline instruction contracts were found. Verify "
        "instruction discovery, supported claim syntax, and BASE evidence.\n"
    )


def test_wheel_installs_and_runs_outside_checkout(
    built_artifacts: tuple[Path, Path], tmp_path: Path
) -> None:
    assert_installed_cli(built_artifacts[0], tmp_path)


def test_source_distribution_installs_and_runs_outside_checkout(
    built_artifacts: tuple[Path, Path], tmp_path: Path
) -> None:
    assert_installed_cli(built_artifacts[1], tmp_path)


def test_local_git_vcs_install_runs_outside_checkout(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for name in ("LICENSE", "README.md", "pyproject.toml"):
        (source / name).write_bytes((ROOT / name).read_bytes())
    package = source / "src/instrproof"
    package.mkdir(parents=True)
    for path in (ROOT / "src/instrproof").glob("*.py"):
        (package / path.name).write_bytes(path.read_bytes())
    scripts = source / "scripts"
    scripts.mkdir()

    env = clean_env()
    for command in (
        ("git", "init"),
        ("git", "config", "user.email", "instrproof@example.test"),
        ("git", "config", "user.name", "InstrProof Test"),
        ("git", "add", "."),
        ("git", "commit", "-m", "fixture"),
    ):
        result = run(*command, cwd=source, env=env)
        assert result.returncode == 0, result.stderr

    venv = tmp_path / "vcs-venv"
    neutral = tmp_path / "vcs-outside"
    neutral.mkdir()
    assert run("uv", "venv", "--python", sys.executable, str(venv), cwd=neutral, env=env).returncode == 0
    python = venv / "bin/python"
    install = run(
        "uv",
        "pip",
        "install",
        "--python",
        str(python),
        f"git+file://{source}",
        cwd=neutral,
        env=env,
    )
    assert install.returncode == 0, install.stderr
    result = run(str(venv / "bin/instrproof"), "--version", cwd=neutral, env=env)
    assert result.returncode == 0
    assert result.stdout == f"instrproof {__version__}\n"
