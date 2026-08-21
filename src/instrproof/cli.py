"""Command-line parsing and presentation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from collections.abc import Sequence

from instrproof.compare import compare_repository
from instrproof.models import ComparisonResult
from instrproof.repository import GitRepository, RepositoryError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="instrproof")
    subcommands = parser.add_subparsers(dest="command", required=True)
    diff = subcommands.add_parser("diff", help="compare instruction contracts with a BASE ref")
    diff.add_argument("--base", required=True, metavar="BASE_REF")
    return parser


def format_result(result: ComparisonResult) -> str:
    if not result.regressions:
        return "No instruction contract regressions found."
    count = len(result.regressions)
    noun = "regression" if count == 1 else "regressions"
    rows = [f"Found {count} instruction contract {noun}:"]
    rows.extend(
        f"{item.identity.contract_type}  source={item.identity.source.value}  target={item.identity.target.value}"
        for item in result.regressions
    )
    return "\n".join(rows)


def main(argv: Sequence[str] | None = None, *, cwd: Path | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        repository = GitRepository.discover(cwd)
        result = compare_repository(repository, args.base)
    except RepositoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(format_result(result))
    return 1 if result.regressions else 0
