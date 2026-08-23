from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/ci.yml"


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_ci_triggers_and_permissions_are_minimal() -> None:
    text = workflow_text()
    assert "pull_request:" in text
    assert "push:" in text
    assert "branches: [main]" in text
    assert "permissions:\n  contents: read" in text
    assert "permissions: write" not in text


def test_ci_has_complete_supported_python_matrix_and_one_build() -> None:
    text = workflow_text()
    validator = (ROOT / "scripts/validate-release.sh").read_text(encoding="utf-8")
    assert 'python-version: ["3.12", "3.13", "3.14"]' in text
    assert "uv sync --locked --dev" in text
    assert "uv run pytest" in text
    assert text.count("--build") == 1
    assert 'python-version: "3.12"' in text
    assert "twine check --strict" in validator
    assert "scripts/inspect_artifacts.py" in validator
    assert "- name: Build wheel and source distribution" in text
    assert "- name: Validate package metadata and artifact contents" in text
    assert "--validate-artifacts" in text
    assert text.index("--build") < text.index("--validate-artifacts")


def test_ci_transfers_and_validates_each_artifact_separately() -> None:
    text = workflow_text()
    for job in (
        "tests:",
        "build-distributions:",
        "validate-wheel:",
        "validate-sdist:",
        "compare-artifacts:",
    ):
        assert job in text
    assert "actions/upload-artifact@v4" in text
    assert text.count("actions/download-artifact@v4") >= 3
    assert "--smoke wheel" in text
    assert "--smoke sdist" in text
    assert "--compare" in text


def test_ci_uses_stable_major_actions_without_publishing() -> None:
    text = workflow_text()
    for action in (
        "actions/checkout@v4",
        "actions/setup-python@v5",
        "astral-sh/setup-uv@v6",
    ):
        assert action in text
    lowered = text.lower()
    for forbidden in ("twine upload", "uv publish", "pypi_token", "id-token: write"):
        assert forbidden not in lowered
