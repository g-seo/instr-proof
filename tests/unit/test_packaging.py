from pathlib import Path
import tomllib

from instrproof import __version__


ROOT = Path(__file__).resolve().parents[2]


def load_pyproject() -> dict[str, object]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_required_project_metadata() -> None:
    config = load_pyproject()
    project = config["project"]
    assert isinstance(project, dict)

    assert project["name"] == "instrproof"
    assert project["description"]
    assert project["readme"] == "README.md"
    assert project["requires-python"] == ">=3.12"
    assert project["license"] == "Apache-2.0"
    assert project["license-files"] == ["LICENSE"]
    assert project["dependencies"] == []
    assert project["dynamic"] == ["version"]
    assert "version" not in project
    assert project["scripts"] == {"instrproof": "instrproof.cli:main"}
    assert project["urls"] == {
        "Repository": "https://github.com/g-seo/instr-proof",
        "Issues": "https://github.com/g-seo/instr-proof/issues",
    }
    assert project["authors"]


def test_python_classifiers_record_explicit_matrix_without_upper_bound() -> None:
    project = load_pyproject()["project"]
    assert isinstance(project, dict)
    classifiers = project["classifiers"]
    assert isinstance(classifiers, list)

    for version in ("3.12", "3.13", "3.14"):
        assert f"Programming Language :: Python :: {version}" in classifiers
    assert not any("3.15" in classifier for classifier in classifiers)


def test_hatchling_uses_package_version_and_explicit_artifact_contents() -> None:
    config = load_pyproject()
    tool = config["tool"]
    assert isinstance(tool, dict)
    hatch = tool["hatch"]
    assert isinstance(hatch, dict)

    assert hatch["version"] == {"path": "src/instrproof/__init__.py"}
    build = hatch["build"]
    assert isinstance(build, dict)
    targets = build["targets"]
    assert isinstance(targets, dict)
    assert targets["wheel"] == {"packages": ["src/instrproof"]}
    assert set(targets["sdist"]["include"]) >= {
        "/LICENSE",
        "/README.md",
        "/pyproject.toml",
        "/scripts",
        "/src/instrproof",
        "/tests",
    }

    init_text = (ROOT / "src/instrproof/__init__.py").read_text(encoding="utf-8")
    assert init_text.count("__version__") == 1
    assert f'__version__ = "{__version__}"' in init_text
