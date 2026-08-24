from pathlib import Path

import pytest

from instrproof.models import RepoPath
from instrproof.discovery import InstructionDiscoveryConfig
from instrproof.repository import BaseReferenceError, GitRepository, RepositoryError

from conftest import git


def write_package_json(repo: Path, script_body: str = "tsc --noEmit") -> None:
    (repo / "package.json").write_text(
        '{"scripts":{"typecheck":' + f'"{script_body}"' + '}}\n', encoding="utf-8"
    )


def test_discovers_repository_and_reads_base_and_head(committed_repo: Path) -> None:
    repository = GitRepository.discover(committed_repo / "src")
    commit = repository.resolve_base("HEAD")
    base = repository.base_instruction_sources(commit)
    head = repository.head_instruction_sources()

    assert repository.root == committed_repo
    assert [source.path.value for source in base] == ["AGENTS.md"]
    assert [source.content for source in head] == ["Use `src/auth/service.py`.\n"]
    assert repository.base_target_exists(commit, RepoPath("src/auth/service.py"))
    assert repository.head_target_exists(RepoPath("src/auth/service.py"))


def test_head_omits_deleted_instruction(committed_repo: Path) -> None:
    (committed_repo / "AGENTS.md").unlink()
    assert GitRepository.discover(committed_repo).head_instruction_sources() == ()


def test_reads_all_default_instruction_names_from_base_and_head(git_repo: Path) -> None:
    for relative in ("AGENTS.md", "CLAUDE.md", "packages/auth/AGENTS.md", "docs/CLAUDE.md"):
        path = git_repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative + "\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "default sources")
    repository = GitRepository.discover(git_repo)
    snapshot = repository.resolve_base("HEAD")

    expected = ["AGENTS.md", "CLAUDE.md", "docs/CLAUDE.md", "packages/auth/AGENTS.md"]
    assert [source.path.value for source in repository.base_instruction_sources(snapshot)] == expected
    assert [source.path.value for source in repository.head_instruction_sources()] == expected


def test_configured_sources_are_loaded_and_deduplicated(git_repo: Path) -> None:
    for relative in ("AGENTS.md", "docs/agent-instructions.md", ".claude/rules/a.md", ".claude/rules/deep/b.md"):
        path = git_repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative + "\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "configured sources")
    repository = GitRepository.discover(git_repo)
    snapshot = repository.resolve_base("HEAD")
    config = InstructionDiscoveryConfig.from_strings(
        ["docs/agent-instructions.md", ".claude/rules/**/*.md", "AGENTS.md"]
    )
    expected = [
        ".claude/rules/a.md",
        ".claude/rules/deep/b.md",
        "AGENTS.md",
        "docs/agent-instructions.md",
    ]

    assert [source.path.value for source in repository.base_instruction_sources(snapshot, config)] == expected
    assert [source.path.value for source in repository.head_instruction_sources(config)] == expected


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"\xff", "not valid UTF-8"),
        (b"{", "malformed JSON"),
        (b"[]", "root must be an object"),
        (b'{"unknown":[]}', "unsupported key"),
        (b'{"instructions":{}}', "instructions must be an array"),
        (b'{"instructions":[1]}', "entries must be strings"),
        (b'{"instructions":["../outside.md"]}', "invalid instruction rule"),
    ],
)
def test_invalid_discovery_configuration_is_explicit(
    git_repo: Path, content: bytes, message: str
) -> None:
    (git_repo / "instrproof.json").write_bytes(content)
    with pytest.raises(RepositoryError, match=message):
        GitRepository.discover(git_repo).head_instruction_discovery_config()


def test_absent_configuration_has_no_additional_rules(git_repo: Path) -> None:
    assert GitRepository.discover(git_repo).head_instruction_discovery_config() == InstructionDiscoveryConfig()


def test_unreadable_discovery_configuration_is_explicit(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = git_repo / "instrproof.json"
    config.write_text("{}\n", encoding="utf-8")
    original = Path.read_bytes

    def fail(path: Path) -> bytes:
        if path.name == "instrproof.json":
            raise PermissionError("denied")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", fail)
    with pytest.raises(RepositoryError, match="cannot read HEAD instrproof.json"):
        GitRepository.discover(git_repo).head_instruction_discovery_config()


def test_base_and_head_discovery_configurations_are_independent(git_repo: Path) -> None:
    (git_repo / "instrproof.json").write_text(
        '{"instructions":["docs/base.md"]}\n', encoding="utf-8"
    )
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base config")
    repository = GitRepository.discover(git_repo)
    snapshot = repository.resolve_base("HEAD")
    status_before = git(git_repo, "status", "--short")

    (git_repo / "instrproof.json").write_text(
        '{"instructions":["docs/head.md"]}\n', encoding="utf-8"
    )

    base = repository.base_instruction_discovery_config(snapshot)
    head = repository.head_instruction_discovery_config()

    assert [rule.normalized for rule in base.additional_rules] == ["docs/base.md"]
    assert [rule.normalized for rule in head.additional_rules] == ["docs/head.md"]
    assert status_before == ""
    assert git(git_repo, "status", "--short") == "M instrproof.json"


def test_absent_base_config_uses_defaults_when_head_adds_config(git_repo: Path) -> None:
    (git_repo / "README.md").write_text("base\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base without config")
    repository = GitRepository.discover(git_repo)
    snapshot = repository.resolve_base("HEAD")
    (git_repo / "instrproof.json").write_text(
        '{"instructions":["docs/head.md"]}\n', encoding="utf-8"
    )

    assert repository.base_instruction_discovery_config(snapshot) == InstructionDiscoveryConfig()
    assert repository.head_instruction_discovery_config() != InstructionDiscoveryConfig()


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"\xff", "BASE instrproof.json is not valid UTF-8"),
        (b"{", "BASE instrproof.json is malformed JSON"),
        (b"[]", "BASE instrproof.json root must be an object"),
        (b'{"unknown":[]}', "BASE instrproof.json contains an unsupported key"),
        (
            b'{"instructions":{}}',
            "BASE instrproof.json instructions must be an array",
        ),
        (
            b'{"instructions":[1]}',
            "BASE instrproof.json instruction entries must be strings",
        ),
        (b'{"instructions":["../outside.md"]}', "BASE instrproof.json has an invalid instruction rule"),
    ],
)
def test_invalid_base_discovery_configuration_is_attributable(
    git_repo: Path, content: bytes, message: str
) -> None:
    (git_repo / "instrproof.json").write_bytes(content)
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "invalid base config")
    repository = GitRepository.discover(git_repo)

    with pytest.raises(RepositoryError, match=message):
        repository.base_instruction_discovery_config(repository.resolve_base("HEAD"))


def test_retained_head_sources_are_sorted_deduplicated_and_loaded_once(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = git_repo / "docs" / "rules.md"
    source.parent.mkdir()
    source.write_text("Use `README.md`.\n", encoding="utf-8")
    (git_repo / "instrproof.json").write_text(
        '{"instructions":["docs/*.md","docs/rules.md"]}\n', encoding="utf-8"
    )
    reads = 0
    original = Path.read_text

    def count_reads(path: Path, *args, **kwargs):
        nonlocal reads
        if path == source:
            reads += 1
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", count_reads)
    repository = GitRepository.discover(git_repo)
    retained = (RepoPath("docs/rules.md"), RepoPath("docs/rules.md"))

    sources = repository.head_instruction_sources(
        repository.head_instruction_discovery_config(), retained
    )

    assert [item.path.value for item in sources] == ["docs/rules.md"]
    assert reads == 1


def test_same_rules_discover_base_and_head_sources_independently(git_repo: Path) -> None:
    docs = git_repo / "docs"
    docs.mkdir()
    (docs / "base.md").write_text("BASE instructions.\n", encoding="utf-8")
    (git_repo / "instrproof.json").write_text(
        '{"instructions":["docs/*.md"]}\n', encoding="utf-8"
    )
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base source set")
    repository = GitRepository.discover(git_repo)
    snapshot = repository.resolve_base("HEAD")
    config = repository.instruction_discovery_config()

    (docs / "base.md").unlink()
    (docs / "head.md").write_text("HEAD instructions.\n", encoding="utf-8")

    assert [
        source.path.value
        for source in repository.base_instruction_sources(snapshot, config)
    ] == ["docs/base.md"]
    assert [
        source.path.value for source in repository.head_instruction_sources(config)
    ] == ["docs/head.md"]


def test_head_discovery_reads_tracked_modifications_and_nonignored_untracked_sources(
    git_repo: Path,
) -> None:
    tracked = git_repo / "AGENTS.md"
    tracked.write_text("Committed instructions.\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "tracked instructions")

    tracked.write_text("Modified instructions.\n", encoding="utf-8")
    untracked = git_repo / "docs" / "CLAUDE.md"
    untracked.parent.mkdir()
    untracked.write_text("Untracked instructions.\n", encoding="utf-8")

    sources = GitRepository.discover(git_repo).head_instruction_sources()

    assert [(source.path.value, source.content) for source in sources] == [
        ("AGENTS.md", "Modified instructions.\n"),
        ("docs/CLAUDE.md", "Untracked instructions.\n"),
    ]


def test_invalid_base_is_explicit(committed_repo: Path) -> None:
    with pytest.raises(RepositoryError):
        GitRepository.discover(committed_repo).resolve_base("does-not-exist")


def test_invalid_base_retains_exact_requested_reference(committed_repo: Path) -> None:
    with pytest.raises(BaseReferenceError) as raised:
        GitRepository.discover(committed_repo).resolve_base("origin/missing")

    assert isinstance(raised.value, RepositoryError)
    assert raised.value.requested_ref == "origin/missing"
    assert raised.value.detail
    assert str(raised.value) == raised.value.detail


def test_non_repository_is_explicit(tmp_path: Path) -> None:
    with pytest.raises(RepositoryError, match="not inside"):
        GitRepository.discover(tmp_path)


def test_invalid_utf8_base_instruction_is_explicit(git_repo: Path) -> None:
    (git_repo / "AGENTS.md").write_bytes(b"\xff")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "invalid base instruction")
    repository = GitRepository.discover(git_repo)

    with pytest.raises(RepositoryError, match="not valid UTF-8"):
        repository.base_instruction_sources(repository.resolve_base("HEAD"))


def test_invalid_utf8_head_instruction_is_explicit(committed_repo: Path) -> None:
    (committed_repo / "AGENTS.md").write_bytes(b"\xff")

    with pytest.raises(RepositoryError, match="cannot read instruction"):
        GitRepository.discover(committed_repo).head_instruction_sources()


def test_head_target_existence_counts_a_dangling_symlink(committed_repo: Path) -> None:
    link = committed_repo / "dangling-link"
    try:
        link.symlink_to("missing-target")
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are unavailable on this platform")

    assert GitRepository.discover(committed_repo).head_target_exists(RepoPath("dangling-link"))


def test_base_target_missing_is_false(committed_repo: Path) -> None:
    repository = GitRepository.discover(committed_repo)
    snapshot = repository.resolve_base("HEAD")
    assert not repository.base_target_exists(snapshot, RepoPath("missing/file.py"))


def test_base_target_inspection_failure_is_explicit(
    committed_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = GitRepository.discover(committed_repo)
    snapshot = repository.resolve_base("HEAD")

    def fail(*_args: str, **_kwargs):
        raise RepositoryError("BASE inspection failed")

    monkeypatch.setattr(repository, "_git", fail)
    with pytest.raises(RepositoryError, match="BASE inspection failed"):
        repository.base_target_exists(snapshot, RepoPath("src/auth/service.py"))


def test_missing_base_object_is_not_treated_as_an_absent_path(committed_repo: Path) -> None:
    blob = git(committed_repo, "rev-parse", "HEAD:src/auth/service.py")
    object_file = committed_repo / ".git" / "objects" / blob[:2] / blob[2:]
    object_file.unlink()
    repository = GitRepository.discover(committed_repo)

    with pytest.raises(RepositoryError):
        repository.base_target_exists(
            repository.resolve_base("HEAD"), RepoPath("src/auth/service.py")
        )


def test_tree_object_is_a_valid_base(committed_repo: Path) -> None:
    tree = git(committed_repo, "rev-parse", "HEAD^{tree}")
    repository = GitRepository.discover(committed_repo)
    snapshot = repository.resolve_base(tree)

    assert snapshot == tree
    assert [source.path.value for source in repository.base_instruction_sources(snapshot)] == [
        "AGENTS.md"
    ]
    assert repository.base_target_exists(snapshot, RepoPath("src/auth/service.py"))


def test_reads_root_package_scripts_from_base_and_head(git_repo: Path) -> None:
    write_package_json(git_repo)
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base package")
    repository = GitRepository.discover(git_repo)
    snapshot = repository.resolve_base("HEAD")

    assert repository.base_package_scripts(snapshot) == frozenset({"typecheck"})
    assert repository.head_package_scripts() == frozenset({"typecheck"})


def test_script_command_body_does_not_change_script_evidence(git_repo: Path) -> None:
    write_package_json(git_repo)
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base package")
    repository = GitRepository.discover(git_repo)
    snapshot = repository.resolve_base("HEAD")
    write_package_json(git_repo, "tsc --noEmit --pretty false")

    assert repository.base_package_scripts(snapshot) == frozenset({"typecheck"})
    assert repository.head_package_scripts() == frozenset({"typecheck"})


def test_absent_or_scripts_free_root_manifest_has_no_script_evidence(git_repo: Path) -> None:
    (git_repo / "README.md").write_text("base\n", encoding="utf-8")
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "base")
    repository = GitRepository.discover(git_repo)
    snapshot = repository.resolve_base("HEAD")

    assert repository.base_package_scripts(snapshot) == frozenset()
    assert repository.head_package_scripts() == frozenset()
    (git_repo / "package.json").write_text('{"name":"demo"}\n', encoding="utf-8")
    assert repository.head_package_scripts() == frozenset()


def test_nested_package_manifest_is_ignored(git_repo: Path) -> None:
    nested = git_repo / "packages" / "app"
    nested.mkdir(parents=True)
    (nested / "package.json").write_text(
        '{"scripts":{"typecheck":"tsc"}}\n', encoding="utf-8"
    )
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "nested only")
    repository = GitRepository.discover(git_repo)

    assert repository.base_package_scripts(repository.resolve_base("HEAD")) == frozenset()
    assert repository.head_package_scripts() == frozenset()


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"\xff", "not valid UTF-8"),
        (b"{", "malformed JSON"),
        (b"[]", "root must be an object"),
        (b'{"scripts":[]}', "scripts must be an object"),
    ],
)
def test_invalid_required_base_package_manifest_is_explicit(
    git_repo: Path, content: bytes, message: str
) -> None:
    (git_repo / "package.json").write_bytes(content)
    git(git_repo, "add", ".")
    git(git_repo, "commit", "-qm", "invalid manifest")
    repository = GitRepository.discover(git_repo)

    with pytest.raises(RepositoryError, match=message):
        repository.base_package_scripts(repository.resolve_base("HEAD"))


def test_unreadable_head_package_manifest_is_explicit(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_package_json(git_repo)
    repository = GitRepository.discover(git_repo)
    original = Path.read_bytes

    def fail_manifest(path: Path) -> bytes:
        if path.name == "package.json":
            raise PermissionError("denied")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", fail_manifest)
    with pytest.raises(RepositoryError, match="cannot read HEAD package.json"):
        repository.head_package_scripts()
