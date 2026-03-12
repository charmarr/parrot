"""Theow lifecycle hooks: setup, teardown, and healing state."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from theow._core._logging import get_logger

import parrot._engine as _engine
from parrot._git import (
    comment_on_pr,
    create_fix_pr,
    find_pr_number,
    git,
    stash_checkpoint,
    stash_drop,
    stash_restore,
)

logger = get_logger("parrot.lifecycle")

_healed: bool = False
_pr_url: str = ""


def _resolve_pr_number(charm_path: str) -> str | None:
    pr_number = os.environ.get("GITHUB_PR_NUMBER")
    if pr_number:
        return pr_number

    ref = os.environ.get("GITHUB_REF", "")
    if ref.startswith("refs/pull/") and ref.endswith("/merge"):
        return ref.split("/")[2]

    return find_pr_number(charm_path)


def _capture_parent_pr(state: dict, charm_path: str) -> None:
    if "_parent_pr" not in state:
        state["_parent_pr"] = _resolve_pr_number(charm_path)
        logger.debug("Parent PR", pr=state["_parent_pr"])


def setup(state: dict, attempt: int) -> dict:
    charm_path = state.get("charm_path", ".")
    _capture_parent_pr(state, charm_path)
    stash_checkpoint(state, charm_path, attempt)
    return state


def setup_itest(state: dict, attempt: int) -> dict:
    charm_path = state.get("charm_path", ".")
    _capture_parent_pr(state, charm_path)
    stash_checkpoint(state, charm_path, attempt)

    charm_name = Path(charm_path).name
    charm_file = os.environ.get("CHARM_PATH", "")
    if charm_file:
        subprocess.run(
            ["juju", "refresh", charm_name, "--path", charm_file],
            cwd=charm_path,
            capture_output=True,
            text=True,
            check=False,
        )
        logger.debug("Juju refresh from clean build", charm=charm_name, path=charm_file)

    return state


def teardown(state: dict, attempt: int, success: bool) -> None:
    global _healed, _pr_url  # noqa: PLW0603

    charm_path = state.get("charm_path", ".")
    dry_run = _engine._dry_run

    if success:
        if state.get("_stash_created"):
            stash_drop(charm_path)

        if dry_run:
            logger.info("Dry-run: skipping branch, push, and PR creation")
            _pr_url = "(dry-run)"
        else:
            url = create_fix_pr(charm_path, state)
            _pr_url = url or ""
            if url:
                logger.info("Fix PR created", url=url)
                parent_pr = state.get("_parent_pr")
                if parent_pr:
                    comment_on_pr(charm_path, parent_pr, f"Parrot auto-healed this PR. Fix: {url}")
            else:
                logger.warning("PR creation failed — check git/gh output above")

        _healed = True
        return

    stash_restore(charm_path, dry_run)
    if state.get("_stash_created"):
        git(["stash", "pop"], cwd=charm_path)

    observation = state.get("_observation")
    logger.debug("Teardown failure state", has_observation=bool(observation), has_parent_pr=bool(state.get("_parent_pr")), fn_name=state.get("_fn_name"), keys=list(state.keys()))
    if observation:
        collection = state.get("_fn_name", "unknown")
        outcome = getattr(observation, "outcome", "unknown")
        rule = getattr(observation, "rule", "unknown")
        reason = getattr(observation, "reason", "")
        comment = (
            f"### Parrot recovery failed\n\n"
            f"| Field | Value |\n"
            f"|-------|-------|\n"
            f"| Collection | `{collection}` |\n"
            f"| Rule | `{rule}` |\n"
            f"| Outcome | `{outcome}` |\n"
            f"| Attempt | {attempt} |\n\n"
        )
        if reason:
            comment += f"**LLM message:** {reason}\n"

        parent_pr = state.get("_parent_pr")
        if dry_run:
            logger.info("Dry-run: would post failure comment", comment=comment)
        elif parent_pr:
            comment_on_pr(charm_path, parent_pr, comment)

    logger.debug("Workspace restored", attempt=attempt)
