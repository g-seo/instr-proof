import pytest

from instrproof import __version__
from instrproof.cli import build_parser, main


def test_version_prints_package_version_without_repository_discovery(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_discovery(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("--version must not discover a repository")

    monkeypatch.setattr("instrproof.cli.GitRepository.discover", fail_discovery)

    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert captured.out == f"instrproof {__version__}\n"
    assert captured.err == ""


def test_root_help_lists_version_option() -> None:
    help_text = build_parser().format_help()

    assert "--version" in help_text
