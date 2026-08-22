from instrproof.compare import compare_contracts, promote_contracts
from instrproof.models import (
    ContractIdentity,
    ContractType,
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
