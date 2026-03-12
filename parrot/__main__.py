"""CLI entry point: python -m parrot <collection> --charm-path <path>."""

from __future__ import annotations

import argparse
import sys

from theow.codegraph import CodeGraph

import parrot._engine as _engine
import parrot._lifecycle as _lifecycle
from parrot._engine import parrot
from parrot._runner import run_integration, run_lint, run_static, run_unit

COLLECTIONS = ("lint", "static", "unit", "integration")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="parrot",
        description="CI auto-healing for charmarr charms",
    )
    parser.add_argument(
        "collection",
        choices=COLLECTIONS,
        help="tox collection to run (lint, static, unit, integration)",
    )
    parser.add_argument(
        "--charm-path",
        required=True,
        help="path to the charm directory",
    )
    parser.add_argument(
        "--suite",
        default=None,
        help="integration test file name, required for integration (e.g. test_deploy.py)",
    )
    parser.add_argument(
        "--extra-index",
        action="append",
        default=[],
        help="additional source root for codegraph indexing (repeatable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="skip remote operations (git push, gh pr create/comment)",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.collection == "integration" and not args.suite:
        parser.error("--suite is required for integration collection")

    _engine._dry_run = args.dry_run

    graph = CodeGraph(root=args.charm_path, languages=["python"])
    for root in args.extra_index:
        graph.add_root(root)
    parrot.tool()(graph.search_code)

    dispatch = {
        "lint": lambda: run_lint(args.charm_path),
        "static": lambda: run_static(args.charm_path),
        "unit": lambda: run_unit(args.charm_path),
        "integration": lambda: run_integration(args.charm_path, args.suite),
    }
    dispatch[args.collection]()

    if _lifecycle._healed:
        if _lifecycle._pr_url:
            print(f"Healed by parrot. PR: {_lifecycle._pr_url}")
        else:
            print("Healed by parrot but PR creation failed — check logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
