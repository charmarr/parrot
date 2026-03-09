"""Theow lifecycle hooks: setup, teardown, and healing state."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from theow._core._logging import get_logger

import parrot._engine as _engine
from parrot._git import (
    create_fix_pr,
    git,
    post_observations,
    stash_checkpoint,
    stash_drop,
    stash_restore,
)

logger = get_logger("parrot.lifecycle")

_healed: bool = False
_pr_url: str = ""


def setup(state: dict, attempt: int) -> dict:
    charm_path = state.get("charm_path", ".")
    stash_checkpoint(state, charm_path, attempt)
    return state


def setup_itest(state: dict, attempt: int) -> dict:
    charm_path = state.get("charm_path", ".")
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
            url = create_fix_pr(charm_path)
            _pr_url = url or ""
            if url:
                logger.info("Fix PR created", url=url)
            else:
                logger.warning("PR creation failed — check git/gh output above")

        _healed = True
        return

    stash_restore(charm_path, dry_run)
    if state.get("_stash_created"):
        git(["stash", "pop"], cwd=charm_path)

    max_retries = state.get("_max_retries", 3)
    if attempt >= max_retries:
        observations = state.get("_observations", "")
        if observations:
            if dry_run:
                logger.info(
                    "Dry-run: would post observations", observations=observations
                )
            else:
                post_observations(charm_path, observations)

    logger.debug("Workspace restored", attempt=attempt)
