"""CLI entry point: python -m parrot <collection> --charm-path <path>."""

from __future__ import annotations

import argparse

from parrot._runner import run_itest, run_lint, run_static, run_unit

COLLECTIONS = ("lint", "static", "unit", "itest")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="parrot",
        description="CI auto-healing for charmarr charms",
    )
    parser.add_argument(
        "collection",
        choices=COLLECTIONS,
        help="tox collection to run (lint, static, unit, itest)",
    )
    parser.add_argument(
        "--charm-path",
        required=True,
        help="path to the charm directory",
    )
    parser.add_argument(
        "--suite",
        default=None,
        help="integration test file name, required for itest (e.g. test_deploy.py)",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.collection == "itest" and not args.suite:
        parser.error("--suite is required for itest collection")

    dispatch = {
        "lint": lambda: run_lint(args.charm_path),
        "static": lambda: run_static(args.charm_path),
        "unit": lambda: run_unit(args.charm_path),
        "itest": lambda: run_itest(args.charm_path, args.suite),
    }
    dispatch[args.collection]()


if __name__ == "__main__":
    main()
