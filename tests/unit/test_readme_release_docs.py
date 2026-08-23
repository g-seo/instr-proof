from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"


def readme() -> str:
    return README.read_text(encoding="utf-8")


def test_installation_paths_are_separate_and_copyable() -> None:
    text = readme()
    for heading in (
        "## Install from PyPI",
        "## Install from GitHub",
        "## Install a built artifact",
        "## Local contributor installation",
    ):
        assert heading in text
    assert "python -m pip install instrproof" in text
    assert "git+https://github.com/g-seo/instr-proof.git" in text
    assert "dist/instrproof-*.whl" in text
    assert "uv sync --locked --dev" in text


def test_consumer_workflow_selects_version_and_materializes_base() -> None:
    text = readme()
    assert 'INSTRPROOF_VERSION: "0.1.0"' in text
    assert "fetch-depth: 0" in text
    assert 'python-version: "3.12"' in text
    assert 'instrproof==${INSTRPROOF_VERSION}' in text
    assert "+refs/heads/main:refs/remotes/origin/main" in text
    assert "instrproof diff --base origin/main --ci" in text


def test_statuses_and_pre_release_boundary_are_documented() -> None:
    text = readme()
    for status in ("`0`", "`1`", "`2`"):
        assert status in text
    assert "./scripts/validate-release.sh" in text
    assert "configured package indexes" in text
    assert "does not install or query a published InstrProof release" in text
    assert "does not upload" in text


def test_publication_is_manual_and_post_release_check_is_exact() -> None:
    text = readme()
    assert "## Manual publication" in text
    assert "uv run twine upload dist/*" in text
    assert "## Post-publication verification" in text
    assert 'INSTRPROOF_VERSION="0.1.0"' in text
    assert 'instrproof==$INSTRPROOF_VERSION' in text
    assert "instrproof --help" in text
    assert "instrproof --version" in text
    assert "instrproof check" in text
    assert "instrproof diff --base HEAD" in text
