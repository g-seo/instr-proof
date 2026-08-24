import pytest

from instrproof.compare import (
    analyze_current_repository,
    compare_contracts,
    compare_repository,
    inspect_claim_occurrences,
    lookup_current_occurrences,
    parse_source_location_selector,
    promote_contracts,
)
from instrproof.extract import extract_path_claims
from instrproof.models import (
    ContractIdentity,
    ContractType,
    CurrentAnalysisResult,
    CurrentOccurrence,
    EvidenceState,
    InstructionSource,
    PackageManager,
    PackageScriptClaim,
    PackageScriptExistsContract,
    ClaimForm,
    PathClaim,
    RepoPath,
    SourceLocation,
)


def claim(source: str = "AGENTS.md", target: str = "src/service.py") -> PathClaim:
    return PathClaim(
        RepoPath(source), ClaimForm.INLINE_PATH, target, RepoPath(target), line=4
    )


def package_claim(target: str = "typecheck") -> PackageScriptClaim:
    return PackageScriptClaim(
        RepoPath("AGENTS.md"), PackageManager.PNPM, f"pnpm {target}", target, line=3
    )


def test_promotes_package_script_and_passes_when_head_script_exists() -> None:
    baseline = promote_contracts(
        [package_claim()], lambda _path: False, lambda name: name == "typecheck"
    )
    result = compare_contracts(
        baseline, [package_claim()], lambda _path: False, lambda name: name == "typecheck"
    )

    assert {contract.identity.target for contract in baseline} == {"typecheck"}
    assert result.regressions == ()


def test_surviving_package_claim_regresses_when_script_removed_or_renamed() -> None:
    baseline = promote_contracts(
        [package_claim()], lambda _path: False, lambda name: name == "typecheck"
    )

    for head_scripts in (frozenset(), frozenset({"check-types"})):
        result = compare_contracts(
            baseline,
            [package_claim()],
            lambda _path: False,
            lambda name, scripts=head_scripts: name in scripts,
        )
        assert [regression.identity.target for regression in result.regressions] == [
            "typecheck"
        ]


def test_package_syntax_prose_and_line_changes_preserve_identity_and_current_location() -> None:
    base = PackageScriptClaim(
        RepoPath("AGENTS.md"), PackageManager.PNPM, "pnpm run typecheck", "typecheck", 8
    )
    head = PackageScriptClaim(
        RepoPath("AGENTS.md"), PackageManager.YARN, "yarn typecheck", "typecheck", 42
    )
    baseline = promote_contracts([base], lambda _path: False, lambda _name: True)
    result = compare_contracts(
        baseline, [head], lambda _path: False, lambda _name: False
    )

    assert len(result.regressions) == 1
    assert result.regressions[0].head_location == SourceLocation(
        RepoPath("AGENTS.md"), 42, "yarn typecheck"
    )


def test_duplicate_claims_choose_lowest_line_for_diagnostics() -> None:
    claims = [
        PackageScriptClaim(
            RepoPath("AGENTS.md"), PackageManager.PNPM, "pnpm typecheck", "typecheck", line
        )
        for line in (20, 3, 11)
    ]
    baseline = promote_contracts(claims, lambda _path: False, lambda _name: True)
    result = compare_contracts(
        baseline, reversed(claims), lambda _path: False, lambda _name: False
    )

    contract = next(iter(baseline))
    assert contract.base_location is not None and contract.base_location.line == 3
    assert result.regressions[0].head_location is not None
    assert result.regressions[0].head_location.line == 3


def test_package_target_change_or_claim_removal_retires_old_contract() -> None:
    baseline = promote_contracts(
        [package_claim("typecheck")], lambda _path: False, lambda _name: True
    )
    changed = compare_contracts(
        baseline,
        [package_claim("check-types")],
        lambda _path: False,
        lambda _name: False,
    )
    removed = compare_contracts(
        baseline, [], lambda _path: False, lambda _name: False
    )

    assert changed.regressions == ()
    assert removed.regressions == ()


def test_contract_diagnostic_location_does_not_affect_equality() -> None:
    identity = ContractIdentity(
        RepoPath("AGENTS.md"), ContractType.PACKAGE_SCRIPT_EXISTS, "typecheck"
    )
    first = PackageScriptExistsContract(
        identity, SourceLocation(RepoPath("AGENTS.md"), 2, "pnpm typecheck")
    )
    moved = PackageScriptExistsContract(
        identity, SourceLocation(RepoPath("AGENTS.md"), 99, "yarn run typecheck")
    )

    assert first == moved
    assert hash(first) == hash(moved)


def test_mixed_contracts_coexist_deduplicate_and_count_all_baselines() -> None:
    path = claim(target="src/service.py")
    package = package_claim("typecheck")
    baseline = promote_contracts(
        [path, path, package, package], lambda _path: True, lambda _name: True
    )
    result = compare_contracts(
        baseline,
        [package, path],
        lambda _path: False,
        lambda _name: False,
    )

    assert result.baseline_contract_count == 2
    assert [
        (item.identity.source.value, item.identity.contract_type.value, item.identity.target)
        for item in result.regressions
    ] == [
        ("AGENTS.md", "PackageScriptExists", "typecheck"),
        ("AGENTS.md", "PathExists", "src/service.py"),
    ]


def test_mixed_regressions_sort_by_source_type_and_target() -> None:
    claims = [
        package_claim("z-script"),
        package_claim("a-script"),
        claim(target="z/file.py"),
        PathClaim(
            RepoPath("docs/CLAUDE.md"),
            ClaimForm.INLINE_PATH,
            "a/file.py",
            RepoPath("a/file.py"),
            line=1,
        ),
    ]
    baseline = promote_contracts(
        claims, lambda _path: True, lambda _name: True
    )
    result = compare_contracts(
        baseline, claims, lambda _path: False, lambda _name: False
    )

    assert [
        (item.identity.source.value, item.identity.contract_type.value, item.identity.target)
        for item in result.regressions
    ] == [
        ("AGENTS.md", "PackageScriptExists", "a-script"),
        ("AGENTS.md", "PackageScriptExists", "z-script"),
        ("AGENTS.md", "PathExists", "z/file.py"),
        ("docs/CLAUDE.md", "PathExists", "a/file.py"),
    ]


def test_promotes_only_claims_with_base_evidence() -> None:
    claims = [claim(target="src/exists.py"), claim(target="src/missing.py")]
    contracts = promote_contracts(claims, lambda path: path.value == "src/exists.py")
    assert {contract.identity.target for contract in contracts} == {"src/exists.py"}


def test_root_filename_promotion_requires_exact_case_sensitive_base_evidence() -> None:
    claims = [
        claim(target="README.md"),
        claim(target="output.json"),
        claim(target="Makefile"),
    ]

    contracts = promote_contracts(
        claims,
        lambda path: path.value in {"README.md", "Makefile", "readme.md"},
    )

    assert {contract.identity.target for contract in contracts} == {
        "Makefile",
        "README.md",
    }


def test_differently_cased_root_evidence_does_not_promote_claim() -> None:
    contracts = promote_contracts(
        [claim(target="README.md")], lambda path: path.value == "readme.md"
    )

    assert contracts == frozenset()


def test_repository_evidence_cannot_promote_unsupported_root_tokens() -> None:
    source = InstructionSource(
        RepoPath("AGENTS.md"),
        "Use `pytest`, `src`, `v1.0`, `*.md`, and `${CONFIG}`.\n",
    )
    claims = extract_path_claims(source)

    contracts = promote_contracts(claims, lambda _path: True)

    assert claims == ()
    assert contracts == frozenset()


def test_existing_head_target_passes() -> None:
    baseline = promote_contracts([claim()], lambda _path: True)
    result = compare_contracts(baseline, [claim()], lambda _path: True)
    assert result.regressions == ()


def test_surviving_claim_with_missing_head_target_regresses() -> None:
    baseline = promote_contracts([claim()], lambda _path: True)
    result = compare_contracts(baseline, [claim()], lambda _path: False)
    assert [item.identity.target for item in result.regressions] == ["src/service.py"]


def test_changed_claim_retires_old_contract() -> None:
    baseline = promote_contracts([claim(target="src/old.py")], lambda _path: True)
    result = compare_contracts(
        baseline,
        [claim(target="src/new.py")],
        lambda _path: False,
    )
    assert result.regressions == ()


def test_removed_claim_retires_old_contract() -> None:
    baseline = promote_contracts([claim()], lambda _path: True)
    assert compare_contracts(baseline, [], lambda _path: False).regressions == ()


def test_duplicate_claims_collapse_to_one_contract() -> None:
    contracts = promote_contracts([claim(), claim()], lambda _path: True)
    result = compare_contracts(contracts, [claim(), claim()], lambda _path: False)
    assert len(contracts) == 1
    assert len(result.regressions) == 1


def test_line_and_written_spelling_do_not_change_identity() -> None:
    base = claim()
    moved = PathClaim(
        base.source,
        ClaimForm.MARKDOWN_LINK,
        "src/./service.py",
        RepoPath("src/./service.py"),
        line=99,
    )
    baseline = promote_contracts([base], lambda _path: True)
    assert len(compare_contracts(baseline, [moved], lambda _path: False).regressions) == 1


def test_equivalent_normalized_targets_deduplicate() -> None:
    first = claim(target="src/service.py")
    second = PathClaim(
        first.source,
        ClaimForm.MARKDOWN_LINK,
        "src/./service.py",
        RepoPath("src/./service.py"),
    )
    contracts = promote_contracts([first, second], lambda _path: True)
    assert len(contracts) == 1


def test_nonexistent_base_targets_never_become_contracts() -> None:
    contracts = promote_contracts([claim(target="missing/file.py")], lambda _path: False)
    assert contracts == frozenset()


def test_inspects_supported_path_occurrences_as_present_or_missing() -> None:
    occurrences = inspect_claim_occurrences(
        [claim(target="src/exists.py"), claim(target="src/missing.py")],
        lambda path: path.value == "src/exists.py",
    )

    assert [(item.identity.target, item.evidence_state) for item in occurrences] == [
        ("src/exists.py", EvidenceState.PRESENT),
        ("src/missing.py", EvidenceState.MISSING),
    ]
    assert [item.evidence_reference for item in occurrences] == [
        "src/exists.py",
        "src/missing.py",
    ]


def test_inspects_package_script_occurrences_with_exact_evidence_reference() -> None:
    occurrences = inspect_claim_occurrences(
        [package_claim("typecheck"), package_claim("missing")],
        lambda _path: False,
        lambda name: name == "typecheck",
    )

    assert [(item.identity.target, item.evidence_state) for item in occurrences] == [
        ("missing", EvidenceState.MISSING),
        ("typecheck", EvidenceState.PRESENT),
    ]
    assert {item.evidence_reference for item in occurrences} == {
        "package.json:scripts.typecheck",
        "package.json:scripts.missing",
    }


def test_inspection_checks_evidence_once_per_identity_but_retains_occurrences() -> None:
    calls: list[str] = []
    first = claim(target="src/service.py")
    moved = PathClaim(
        first.source,
        ClaimForm.MARKDOWN_LINK,
        "src/./service.py",
        RepoPath("src/./service.py"),
        line=9,
    )

    def missing(path: RepoPath) -> bool:
        calls.append(path.value)
        return False

    occurrences = inspect_claim_occurrences([moved, first], missing)

    assert calls == ["src/service.py"]
    assert [item.source_location.line for item in occurrences] == [4, 9]
    assert all(item.evidence_state is EvidenceState.MISSING for item in occurrences)


def test_inspection_is_lazy_for_package_scripts_when_none_are_present() -> None:
    def unexpected(_name: str) -> bool:
        raise AssertionError("script evidence must stay lazy")

    assert inspect_claim_occurrences([claim()], lambda _path: True, unexpected)


def test_inspection_propagates_evidence_failures() -> None:
    def fail(_path: RepoPath) -> bool:
        raise RuntimeError("repository failed")

    with pytest.raises(RuntimeError, match="repository failed"):
        inspect_claim_occurrences([claim()], fail)


class CurrentRepositoryStub:
    def __init__(
        self,
        sources: tuple[InstructionSource, ...],
        paths: frozenset[RepoPath] = frozenset(),
        scripts: frozenset[str] = frozenset(),
    ) -> None:
        self.sources = sources
        self.paths = paths
        self.scripts = scripts
        self.script_reads = 0

    def head_instruction_discovery_config(self):
        return None

    def head_instruction_sources(self, _config, _retained_paths=()):
        return self.sources

    def head_target_exists(self, path: RepoPath) -> bool:
        return path in self.paths

    def head_package_scripts(self) -> frozenset[str]:
        self.script_reads += 1
        return self.scripts


class ComparisonRepositoryStub:
    def __init__(self) -> None:
        self.head_source_calls = 0
        self.retained_paths: tuple[RepoPath, ...] = ()
        self.source = InstructionSource(RepoPath("docs/rules.md"), "Use `README.md`.\n")

    def resolve_base(self, _ref: str) -> str:
        return "snapshot"

    def base_instruction_discovery_config(self, _snapshot: str):
        return None

    def base_instruction_sources(self, _snapshot: str, _config):
        return (self.source,)

    def base_target_exists(self, _snapshot: str, path: RepoPath) -> bool:
        return path == RepoPath("README.md")

    def base_package_scripts(self, _snapshot: str) -> frozenset[str]:
        return frozenset()

    def head_instruction_discovery_config(self):
        return None

    def head_instruction_sources(self, _config, retained_paths=()):
        self.head_source_calls += 1
        self.retained_paths = retained_paths
        return (self.source,)

    def head_target_exists(self, _path: RepoPath) -> bool:
        return False

    def head_package_scripts(self) -> frozenset[str]:
        return frozenset()


def test_compare_repository_carries_base_paths_and_loads_head_sources_once() -> None:
    repository = ComparisonRepositoryStub()

    result = compare_repository(repository, "HEAD")  # type: ignore[arg-type]

    assert repository.head_source_calls == 1
    assert repository.retained_paths == (RepoPath("docs/rules.md"),)
    assert [item.identity.target for item in result.regressions] == ["README.md"]


def test_analyze_current_repository_returns_present_contracts_and_all_occurrences() -> None:
    repository = CurrentRepositoryStub(
        (
            InstructionSource(
                RepoPath("AGENTS.md"),
                "Use `src/service.py`.\nUse `src/service.py`.\nRun pnpm typecheck.\n",
            ),
            InstructionSource(
                RepoPath("docs/AGENTS.md"), "Use `src/missing.py`.\n"
            ),
        ),
        frozenset({RepoPath("src/service.py")}),
        frozenset({"typecheck"}),
    )

    result = analyze_current_repository(repository)  # type: ignore[arg-type]

    assert [item.identity.target for item in result.verified_contracts] == [
        "typecheck",
        "src/service.py",
    ]
    assert [item.source_location.line for item in result.occurrences] == [3, 1, 2, 1]
    assert result.verified_contracts[1].source_location.line == 1
    assert result.occurrences[-1].evidence_state is EvidenceState.MISSING
    assert repository.script_reads == 1


def test_analyze_current_repository_handles_zero_contracts_without_manifest_read() -> None:
    repository = CurrentRepositoryStub(
        (InstructionSource(RepoPath("AGENTS.md"), "General guidance only.\n"),)
    )

    result = analyze_current_repository(repository)  # type: ignore[arg-type]

    assert result.occurrences == ()
    assert result.verified_contracts == ()
    assert repository.script_reads == 0


def test_parse_source_location_selector_uses_final_colon_and_normalizes_path() -> None:
    selector = parse_source_location_selector("docs/a:b/../AGENTS.md:37")
    assert selector.source == RepoPath("docs/AGENTS.md")
    assert selector.line == 37


@pytest.mark.parametrize(
    "value",
    [
        "AGENTS.md",
        "AGENTS.md:",
        "AGENTS.md:zero",
        "AGENTS.md:0",
        "/AGENTS.md:1",
        "../AGENTS.md:1",
    ],
)
def test_parse_source_location_selector_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match="source location"):
        parse_source_location_selector(value)


def test_lookup_current_occurrences_matches_exact_source_and_line() -> None:
    identity_path = ContractIdentity(
        RepoPath("AGENTS.md"), ContractType.PATH_EXISTS, "src/service.py"
    )
    identity_script = ContractIdentity(
        RepoPath("AGENTS.md"), ContractType.PACKAGE_SCRIPT_EXISTS, "typecheck"
    )
    occurrences = (
        CurrentOccurrence(
            identity_path,
            SourceLocation(RepoPath("AGENTS.md"), 4),
            "src/service.py",
            EvidenceState.MISSING,
        ),
        CurrentOccurrence(
            identity_script,
            SourceLocation(RepoPath("AGENTS.md"), 4),
            "package.json:scripts.typecheck",
            EvidenceState.PRESENT,
        ),
        CurrentOccurrence(
            identity_path,
            SourceLocation(RepoPath("AGENTS.md"), 9),
            "src/service.py",
            EvidenceState.MISSING,
        ),
    )
    result = CurrentAnalysisResult(occurrences, ())

    matches = lookup_current_occurrences(
        result, parse_source_location_selector("AGENTS.md:4")
    )

    assert [match.identity for match in matches] == [identity_script, identity_path]
    assert [match.evidence_reference for match in matches] == [
        "package.json:scripts.typecheck",
        "src/service.py",
    ]
    assert lookup_current_occurrences(
        result, parse_source_location_selector("docs/AGENTS.md:4")
    ) == ()
    assert lookup_current_occurrences(
        result, parse_source_location_selector("AGENTS.md:8")
    ) == ()


def test_lookup_deduplicates_same_identity_at_requested_line() -> None:
    identity = ContractIdentity(
        RepoPath("AGENTS.md"), ContractType.PATH_EXISTS, "src/service.py"
    )
    occurrence = CurrentOccurrence(
        identity,
        SourceLocation(RepoPath("AGENTS.md"), 4),
        "src/service.py",
        EvidenceState.PRESENT,
    )
    result = CurrentAnalysisResult((occurrence, occurrence), ())

    assert lookup_current_occurrences(
        result, parse_source_location_selector("AGENTS.md:4")
    ) == (occurrence,)


def test_current_analysis_line_movement_changes_location_not_identity() -> None:
    first = analyze_current_repository(
        CurrentRepositoryStub(
            (InstructionSource(RepoPath("AGENTS.md"), "Use `src/service.py`.\n"),),
            frozenset({RepoPath("src/service.py")}),
        )  # type: ignore[arg-type]
    )
    moved = analyze_current_repository(
        CurrentRepositoryStub(
            (
                InstructionSource(
                    RepoPath("AGENTS.md"), "Surrounding prose.\n\nUse `src/service.py`.\n"
                ),
            ),
            frozenset({RepoPath("src/service.py")}),
        )  # type: ignore[arg-type]
    )

    assert first.verified_contracts[0] == moved.verified_contracts[0]
    assert hash(first.verified_contracts[0]) == hash(moved.verified_contracts[0])
    assert first.verified_contracts[0].source_location.line == 1
    assert moved.verified_contracts[0].source_location.line == 3


def test_equal_current_targets_from_different_sources_remain_distinct() -> None:
    result = analyze_current_repository(
        CurrentRepositoryStub(
            (
                InstructionSource(RepoPath("AGENTS.md"), "Use `src/service.py`.\n"),
                InstructionSource(
                    RepoPath("docs/AGENTS.md"), "Use `src/service.py`.\n"
                ),
            ),
            frozenset({RepoPath("src/service.py")}),
        )  # type: ignore[arg-type]
    )

    assert len(result.verified_contracts) == 2
    assert {item.identity.source.value for item in result.verified_contracts} == {
        "AGENTS.md",
        "docs/AGENTS.md",
    }
