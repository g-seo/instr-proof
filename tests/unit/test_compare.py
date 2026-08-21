from instrproof.compare import compare_contracts, promote_contracts
from instrproof.models import ClaimForm, PathClaim, RepoPath


def claim(source: str = "AGENTS.md", target: str = "src/service.py") -> PathClaim:
    return PathClaim(
        RepoPath(source), ClaimForm.INLINE_PATH, target, RepoPath(target), line=4
    )


def test_promotes_only_claims_with_base_evidence() -> None:
    claims = [claim(target="src/exists.py"), claim(target="src/missing.py")]
    contracts = promote_contracts(claims, lambda path: path.value == "src/exists.py")
    assert {contract.identity.target.value for contract in contracts} == {"src/exists.py"}


def test_existing_head_target_passes() -> None:
    baseline = promote_contracts([claim()], lambda _path: True)
    result = compare_contracts(baseline, [claim()], lambda _path: True)
    assert result.regressions == ()


def test_surviving_claim_with_missing_head_target_regresses() -> None:
    baseline = promote_contracts([claim()], lambda _path: True)
    result = compare_contracts(baseline, [claim()], lambda _path: False)
    assert [item.identity.target.value for item in result.regressions] == ["src/service.py"]


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
