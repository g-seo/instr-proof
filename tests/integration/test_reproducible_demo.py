from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run-demo.sh"
TEMPLATE = ROOT / "examples" / "demo-repo"

STAGES = (
    "[1/3] Baseline: instruction matches repository",
    "[2/3] Refactor: tests pass, instruction is stale",
    "[3/3] Repair: instruction updated",
)


def run_demo(
    *args: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SCRIPT), *args],
        cwd=cwd or ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
        env=env,
    )


def repository_snapshot() -> tuple[bytes, dict[str, tuple[object, ...]]]:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    entries: dict[str, tuple[object, ...]] = {}
    for raw_path in listed.split(b"\0"):
        if not raw_path:
            continue
        relative = os.fsdecode(raw_path)
        path = ROOT / relative
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if stat.S_ISLNK(metadata.st_mode):
            identity = ("symlink", os.readlink(path), mode)
        elif stat.S_ISREG(metadata.st_mode):
            identity = ("regular", hashlib.sha256(path.read_bytes()).hexdigest(), mode)
        elif stat.S_ISDIR(metadata.st_mode):
            identity = ("directory", mode)
        else:
            identity = ("other", stat.S_IFMT(metadata.st_mode), mode)
        entries[relative] = identity
    return status, entries


def add_path_wrapper(directory: Path, name: str, body: str) -> None:
    wrapper = directory / name
    wrapper.write_text(f"#!/usr/bin/env bash\nset -eu\n{body}\n", encoding="utf-8")
    wrapper.chmod(0o755)


def shim_environment(shim_dir: Path) -> dict[str, str]:
    return {**os.environ, "PATH": f"{shim_dir}{os.pathsep}{os.environ['PATH']}"}


def assert_no_demo_directories(directory: Path) -> None:
    assert list(directory.glob("instrproof-demo.*")) == []
    assert list(directory.glob("instrproof-demo-audit.*")) == []


def test_static_template_is_minimal_and_not_a_git_repository() -> None:
    files = {
        path.relative_to(TEMPLATE).as_posix()
        for path in TEMPLATE.rglob("*")
        if path.is_file()
    }
    assert files == {"AGENTS.md", "src/auth/service.py", "tests/test_service.py"}
    assert not any(path.name == ".git" for path in TEMPLATE.rglob(".git"))
    assert (TEMPLATE / "AGENTS.md").read_text() == (
        "Authentication logic is implemented in `src/auth/service.py`.\n"
    )
    assert "def authenticate(token: str) -> bool:" in (
        TEMPLATE / "src/auth/service.py"
    ).read_text()
    assert "from src.auth.service import authenticate" in (
        TEMPLATE / "tests/test_service.py"
    ).read_text()
    result = run_demo()
    assert result.returncode == 0, result.stderr


def test_runner_has_valid_shell_syntax_and_is_executable() -> None:
    assert os.access(SCRIPT, os.X_OK)
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT)], text=True, capture_output=True, check=False
    )
    assert result.returncode == 0, result.stderr
    public_run = run_demo()
    assert public_run.returncode == 0, public_run.stderr


def test_unsupported_argument_returns_usage_status_2() -> None:
    result = run_demo("--unknown")
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "Usage: run-demo.sh [--keep]\n"


def test_complete_workflow_from_outside_checkout(tmp_path: Path) -> None:
    result = run_demo(cwd=tmp_path)
    assert result.returncode == 0, result.stderr

    output = result.stdout
    positions = [output.index(stage) for stage in STAGES]
    assert positions == sorted(positions)
    for stage in STAGES:
        assert output.count(stage) == 1

    assert output.count("Application tests passed.") == 3
    assert output.count("$ instrproof check") == 1
    assert output.count("Found 1 verified instruction contract:") == 1
    assert (
        "PathExists  source=AGENTS.md:1  target=src/auth/service.py  current=present"
        in output
    )

    assert "$ git mv src/auth/service.py src/auth/auth_service.py" in output
    assert "$ git diff HEAD -- src/auth tests/test_service.py" in output
    assert "rename from src/auth/service.py" in output
    assert "rename to src/auth/auth_service.py" in output
    assert "-from src.auth.service import authenticate" in output
    assert "+from src.auth.auth_service import authenticate" in output
    assert output.count("$ instrproof diff --base demo-base --ci") == 2
    assert output.count("Broken comparison status: 1") == 1
    assert output.count("1 instruction contract regression") == 1
    assert output.count("AGENTS.md:1\nPathExists(src/auth/service.py)") == 1

    assert output.count(
        "Authentication logic is implemented in `src/auth/auth_service.py`."
    ) == 1
    assert output.count("Repaired comparison status: 0") == 1
    assert output.count("1 baseline contracts checked.") == 1
    assert output.count("No instruction contract regressions.") == 1
    final_explanation = (
        "An ordinary refactor moved src/auth/service.py to src/auth/auth_service.py "
        "while ordinary tests kept passing.\n"
        "AGENTS.md was unchanged, so its old-path evidence was missing and InstrProof "
        "CI reported the expected status 1.\n"
        "Updating AGENTS.md to match the refactor repaired the instruction contract; "
        "the same immutable demo-base then restored CI success with status 0.\n"
    )
    assert output.endswith(final_explanation)


def test_parent_git_visible_state_and_preexisting_files_are_unchanged() -> None:
    sentinel = ROOT / f".instrproof-demo-sentinel-{uuid.uuid4().hex}"
    sentinel_bytes = b"pre-existing untracked demo sentinel\x00\xff\n"
    tracked = ROOT / "README.md"
    assert not sentinel.exists()
    sentinel_created = False
    try:
        sentinel.write_bytes(sentinel_bytes)
        sentinel_created = True
        tracked_before = tracked.read_bytes()
        before = repository_snapshot()

        result = run_demo(env={**os.environ, "UV_OFFLINE": "1"})

        assert result.returncode == 0, result.stderr
        assert sentinel.exists()
        assert sentinel.read_bytes() == sentinel_bytes
        assert tracked.read_bytes() == tracked_before
        assert repository_snapshot() == before
    finally:
        original_failure = sys.exc_info()[0] is not None
        try:
            if sentinel_created and sentinel.exists():
                sentinel.unlink()
        except OSError:
            if not original_failure:
                raise


def test_three_offline_runs_are_equivalent_fast_and_self_cleaning(
    tmp_path: Path,
) -> None:
    env = {**os.environ, "TMPDIR": str(tmp_path), "UV_OFFLINE": "1"}
    outputs: list[str] = []
    for _ in range(3):
        started = time.monotonic()
        result = run_demo(env=env)
        assert time.monotonic() - started < 30
        assert result.returncode == 0, result.stderr
        outputs.append(result.stdout)
        assert_no_demo_directories(tmp_path)
    assert outputs[0] == outputs[1] == outputs[2]


def test_external_absolute_temp_base_is_cleaned() -> None:
    external_parent = Path("/var/tmp")
    if not external_parent.is_dir() or not os.access(external_parent, os.W_OK):
        raise AssertionError("supported Linux environment requires writable /var/tmp")
    owned_base = Path(tempfile.mkdtemp(prefix="instrproof-demo-test.", dir=external_parent))
    try:
        env = {**os.environ, "TMPDIR": str(owned_base), "UV_OFFLINE": "1"}
        result = run_demo(env=env)
        assert result.returncode == 0, result.stderr
        assert_no_demo_directories(owned_base)
    finally:
        shutil.rmtree(owned_base)


def test_temp_base_inside_parent_is_rejected_without_parent_mutation() -> None:
    before = repository_snapshot()
    result = run_demo(env={**os.environ, "TMPDIR": str(ROOT)})
    assert result.returncode != 0
    assert result.stdout == ""
    assert "temporary base must be outside the InstrProof repository" in result.stderr
    assert repository_snapshot() == before
    assert_no_demo_directories(ROOT)


def test_missing_git_is_an_attributable_setup_failure(tmp_path: Path) -> None:
    shim = tmp_path / "bin"
    shim.mkdir()
    for command in ("bash", "dirname"):
        target = shutil.which(command)
        assert target is not None
        (shim / command).symlink_to(target)
    result = run_demo(env={**os.environ, "PATH": str(shim)})
    assert result.returncode != 0
    assert result.stderr == "Demo failed during setup: Git is required\n"


def test_missing_uv_is_an_attributable_setup_failure(tmp_path: Path) -> None:
    shim = tmp_path / "bin"
    shim.mkdir()
    for command in ("bash", "dirname", "git"):
        target = shutil.which(command)
        assert target is not None
        (shim / command).symlink_to(target)
    result = run_demo(env={**os.environ, "PATH": str(shim)})
    assert result.returncode != 0
    assert result.stderr == "Demo failed during setup: uv is required\n"


def test_unavailable_instrproof_cli_is_an_attributable_failure(tmp_path: Path) -> None:
    shim = tmp_path / "bin"
    work = tmp_path / "work"
    shim.mkdir()
    work.mkdir()
    add_path_wrapper(shim, "uv", "exit 73")
    env = shim_environment(shim)
    env["TMPDIR"] = str(work)
    result = run_demo(env=env)
    assert result.returncode != 0
    assert "InstrProof CLI is unavailable" in result.stderr
    assert_no_demo_directories(work)


def test_git_commit_failure_is_attributed_and_cleaned(tmp_path: Path) -> None:
    shim = tmp_path / "bin"
    work = tmp_path / "work"
    shim.mkdir()
    work.mkdir()
    real_git = shutil.which("git")
    assert real_git is not None
    add_path_wrapper(
        shim,
        "git",
        f'''case " $* " in
    *" commit "*) exit 74 ;;
esac
exec "{real_git}" "$@"''',
    )
    env = shim_environment(shim)
    env["TMPDIR"] = str(work)
    result = run_demo(env=env)
    assert result.returncode != 0
    assert "Demo failed during setup: baseline commit failed" in result.stderr
    assert_no_demo_directories(work)


def test_broken_comparison_rejects_wrong_status(tmp_path: Path) -> None:
    shim = tmp_path / "bin"
    work = tmp_path / "work"
    shim.mkdir()
    work.mkdir()
    real_uv = shutil.which("uv")
    assert real_uv is not None
    add_path_wrapper(
        shim,
        "uv",
        f'''case " $* " in
    *" instrproof diff --base demo-base --ci "*)
        printf 'unexpected success\n'
        exit 0 ;;
esac
exec "{real_uv}" "$@"''',
    )
    env = shim_environment(shim)
    env["TMPDIR"] = str(work)
    result = run_demo(env=env)
    assert result.returncode != 0
    assert "Demo failed during refactor: expected comparison status 1, got 0" in result.stderr
    assert_no_demo_directories(work)


def test_broken_comparison_rejects_wrong_diagnostic(tmp_path: Path) -> None:
    shim = tmp_path / "bin"
    work = tmp_path / "work"
    shim.mkdir()
    work.mkdir()
    real_uv = shutil.which("uv")
    assert real_uv is not None
    add_path_wrapper(
        shim,
        "uv",
        f'''case " $* " in
    *" instrproof diff --base demo-base --ci "*)
        printf 'InstrProof failure with the wrong target\n'
        exit 1 ;;
esac
exec "{real_uv}" "$@"''',
    )
    env = shim_environment(shim)
    env["TMPDIR"] = str(work)
    result = run_demo(env=env)
    assert result.returncode != 0
    assert "broken comparison diagnostic did not match" in result.stderr
    assert_no_demo_directories(work)


def test_repaired_comparison_rejects_nonzero_status(tmp_path: Path) -> None:
    shim = tmp_path / "bin"
    work = tmp_path / "work"
    counter = tmp_path / "diff-count"
    shim.mkdir()
    work.mkdir()
    real_uv = shutil.which("uv")
    assert real_uv is not None
    add_path_wrapper(
        shim,
        "uv",
        f'''case " $* " in
    *" instrproof diff --base demo-base --ci "*)
        count=0
        [ ! -f "{counter}" ] || count=$(cat "{counter}")
        count=$((count + 1))
        printf '%s\n' "$count" >"{counter}"
        if [ "$count" -eq 2 ]; then
            printf 'unexpected repaired regression\n'
            exit 1
        fi ;;
esac
exec "{real_uv}" "$@"''',
    )
    env = shim_environment(shim)
    env["TMPDIR"] = str(work)
    result = run_demo(env=env)
    assert result.returncode != 0
    assert "Demo failed during repair: expected repaired comparison status 0, got 1" in result.stderr
    assert_no_demo_directories(work)


def test_interruption_is_nonzero_and_cleans_temporary_state(tmp_path: Path) -> None:
    shim = tmp_path / "bin"
    work = tmp_path / "work"
    shim.mkdir()
    work.mkdir()
    real_uv = shutil.which("uv")
    assert real_uv is not None
    ready = tmp_path / "uv-ready"
    add_path_wrapper(
        shim,
        "uv",
        f'''if [ "${{*: -2}}" = "instrproof check" ]; then
        : > "{ready}"
        sleep 30
    fi
    exec "{real_uv}" "$@"''',
    )
    env = shim_environment(shim)
    env.update({"TMPDIR": str(work), "UV_OFFLINE": "1"})
    process = subprocess.Popen(
        [str(SCRIPT)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        start_new_session=True,
    )
    deadline = time.monotonic() + 10
    while not ready.exists():
        assert process.poll() is None
        if time.monotonic() >= deadline:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise AssertionError("timed out waiting for the interrupt fixture")
        time.sleep(0.01)

    os.killpg(process.pid, signal.SIGTERM)
    stdout, stderr = process.communicate(timeout=10)

    assert "$ instrproof check" in stdout
    assert process.returncode != 0
    assert "interrupted" in stderr.lower() or process.returncode < 0
    assert_no_demo_directories(work)


def test_keep_retains_repaired_repository_for_manual_inspection(
    tmp_path: Path,
) -> None:
    env = {**os.environ, "TMPDIR": str(tmp_path), "UV_OFFLINE": "1"}
    result = run_demo("--keep", env=env)
    assert result.returncode == 0, result.stderr
    marker = "Retained demo repository: "
    lines = [line for line in result.stdout.splitlines() if line.startswith(marker)]
    assert len(lines) == 1
    retained = Path(lines[0].removeprefix(marker))
    try:
        assert retained.is_absolute()
        assert (retained / ".git").is_dir()
        subprocess.run(
            ["git", "rev-parse", "--verify", "demo-base^{commit}"],
            cwd=retained,
            check=True,
            capture_output=True,
        )
        assert not (retained / "src/auth/service.py").exists()
        assert (retained / "src/auth/auth_service.py").is_file()
        assert (retained / "AGENTS.md").read_text() == (
            "Authentication logic is implemented in `src/auth/auth_service.py`.\n"
        )
        app = subprocess.run(
            ["python3", "-m", "unittest", "discover", "-s", "tests"],
            cwd=retained,
            check=False,
            capture_output=True,
            text=True,
        )
        assert app.returncode == 0, app.stderr
        for command in (
            ["instrproof", "check"],
            ["instrproof", "diff", "--base", "demo-base", "--ci"],
        ):
            manual = subprocess.run(
                ["uv", "run", "--offline", "--project", str(ROOT), *command],
                cwd=retained,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            assert manual.returncode == 0, manual.stderr
    finally:
        shutil.rmtree(retained.parent)


def test_keep_cleans_preinitialization_failure(tmp_path: Path) -> None:
    shim = tmp_path / "bin"
    work = tmp_path / "work"
    shim.mkdir()
    work.mkdir()
    real_git = shutil.which("git")
    assert real_git is not None
    add_path_wrapper(
        shim,
        "git",
        f'''case " $* " in
    *" init "*) exit 91 ;;
esac
exec "{real_git}" "$@"''',
    )
    env = shim_environment(shim)
    env["TMPDIR"] = str(work)
    result = run_demo("--keep", env=env)
    assert result.returncode != 0
    assert "Git initialization failed" in result.stderr
    assert "Retained demo repository:" not in result.stdout
    assert_no_demo_directories(work)


def test_keep_preserves_initialized_repository_on_failure(tmp_path: Path) -> None:
    shim = tmp_path / "bin"
    work = tmp_path / "work"
    shim.mkdir()
    work.mkdir()
    real_uv = shutil.which("uv")
    assert real_uv is not None
    add_path_wrapper(
        shim,
        "uv",
        f'''case " $* " in
    *" instrproof check "*) exit 9 ;;
esac
exec "{real_uv}" "$@"''',
    )
    env = shim_environment(shim)
    env["TMPDIR"] = str(work)
    result = run_demo("--keep", env=env)
    assert result.returncode != 0
    assert "Demo failed during baseline" in result.stderr
    marker = "Retained demo repository: "
    retained_lines = [line for line in result.stdout.splitlines() if line.startswith(marker)]
    assert len(retained_lines) == 1
    retained = Path(retained_lines[0].removeprefix(marker))
    try:
        assert (retained / ".git").is_dir()
        subprocess.run(
            ["git", "rev-parse", "--verify", "demo-base^{commit}"],
            cwd=retained,
            check=True,
            capture_output=True,
        )
    finally:
        shutil.rmtree(retained.parent)
