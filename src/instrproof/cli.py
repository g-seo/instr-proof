"""Command-line parsing and presentation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from collections.abc import Sequence

from instrproof.compare import (
    analyze_current_repository,
    compare_repository,
    lookup_current_occurrences,
    parse_source_location_selector,
)
from instrproof.models import ComparisonResult, CurrentAnalysisResult, CurrentOccurrence
from instrproof.repository import BaseReferenceError, GitRepository, RepositoryError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="instrproof")
    subcommands = parser.add_subparsers(dest="command", required=True)
    diff = subcommands.add_parser("diff", help="compare instruction contracts with a BASE ref")
    diff.add_argument("--base", required=True, metavar="BASE_REF")
    diff.add_argument("--ci", action="store_true", help="format the result for CI logs")
    subcommands.add_parser("check", help="inspect current verified instruction contracts")
    explain = subcommands.add_parser(
        "explain", help="explain current evidence at a source location"
    )
    explain.add_argument("source_location", metavar="SOURCE:LINE")
    return parser


def format_result(result: ComparisonResult) -> str:
    if not result.regressions:
        return "No instruction contract regressions found."
    count = len(result.regressions)
    noun = "regression" if count == 1 else "regressions"
    rows = [f"Found {count} instruction contract {noun}:"]
    for item in result.regressions:
        source = item.identity.source.value
        if item.head_location is not None and item.head_location.line is not None:
            source = f"{source}:{item.head_location.line}"
        rows.append(
            f"{item.identity.contract_type}  source={source}  "
            f"target={item.identity.target}  base={item.base_evidence}  "
            f"head={item.head_evidence}"
        )
    return "\n".join(rows)


def format_ci_result(result: ComparisonResult) -> str:
    if not result.regressions:
        return "\n".join(
            (
                "InstrProof ✓",
                "",
                f"{result.baseline_contract_count} baseline contracts checked.",
                "No instruction contract regressions.",
            )
        )

    count = len(result.regressions)
    noun = "regression" if count == 1 else "regressions"
    sections = ["InstrProof ✗", f"{count} instruction contract {noun}"]
    for item in result.regressions:
        source = item.identity.source.value
        if item.head_location is not None and item.head_location.line is not None:
            source = f"{source}:{item.head_location.line}"
        sections.append(
            "\n".join(
                (
                    source,
                    f"{item.identity.contract_type}({item.identity.target})",
                )
            )
        )
    return "\n\n".join(sections)


def format_ci_error(message: str) -> str:
    return f"InstrProof ✗\n\nAnalysis error: {message}"


def format_check_result(result: CurrentAnalysisResult) -> str:
    count = len(result.verified_contracts)
    if count == 0:
        return "Found 0 verified instruction contracts."
    noun = "contract" if count == 1 else "contracts"
    rows = [f"Found {count} verified instruction {noun}:"]
    for contract in result.verified_contracts:
        source = contract.identity.source.value
        location = contract.source_location
        if location is not None and location.line is not None:
            source = f"{source}:{location.line}"
        rows.append(
            f"{contract.identity.contract_type}  source={source}  "
            f"target={contract.identity.target}  current=present"
        )
    return "\n".join(rows)


def format_explanations(occurrences: Sequence[CurrentOccurrence]) -> str:
    sections = []
    for occurrence in occurrences:
        location = occurrence.source_location
        source = location.source.value
        if location.line is not None:
            source = f"{source}:{location.line}"
        sections.append(
            "\n".join(
                (
                    "Contract",
                    "",
                    "Source",
                    f"  {source}",
                    "",
                    "Type",
                    f"  {occurrence.identity.contract_type}",
                    "",
                    "Target",
                    f"  {occurrence.identity.target}",
                    "",
                    "Evidence",
                    f"  {occurrence.evidence_reference}",
                    "",
                    "CURRENT",
                    f"  {occurrence.evidence_state.name}",
                )
            )
        )
    return "\n\n".join(sections)


def main(argv: Sequence[str] | None = None, *, cwd: Path | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        try:
            repository = GitRepository.discover(cwd)
            current = analyze_current_repository(repository)
        except RepositoryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        except Exception:
            print("error: internal analysis failure", file=sys.stderr)
            return 2
        print(format_check_result(current))
        return 0

    if args.command == "explain":
        try:
            selector = parse_source_location_selector(args.source_location)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        try:
            repository = GitRepository.discover(cwd)
            current = analyze_current_repository(repository)
            matches = lookup_current_occurrences(current, selector)
        except RepositoryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        except Exception:
            print("error: internal analysis failure", file=sys.stderr)
            return 2
        if not matches:
            print(
                "No supported instruction contract at "
                f"{selector.source.value}:{selector.line}."
            )
            return 1
        print(format_explanations(matches))
        return 0

    try:
        repository = GitRepository.discover(cwd)
        result = compare_repository(repository, args.base)
    except BaseReferenceError as exc:
        if args.ci:
            print(
                format_ci_error(
                    f"BASE reference '{exc.requested_ref}' is unavailable. "
                    "Ensure the exact reference exists in the local checkout."
                ),
                file=sys.stderr,
            )
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2
    except RepositoryError as exc:
        if args.ci:
            print(format_ci_error(str(exc)), file=sys.stderr)
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception:
        if not args.ci:
            raise
        print(format_ci_error("internal analysis failure."), file=sys.stderr)
        return 2
    print(format_ci_result(result) if args.ci else format_result(result))
    return 1 if result.regressions else 0
