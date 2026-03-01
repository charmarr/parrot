"""Parrot Theow instance and lifecycle hooks."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

from theow import Theow

logger = logging.getLogger("parrot")

parrot = Theow(
    theow_dir=Path(__file__).parent,
    name="Parrot",
    llm="copilot/gpt-5.3-codex",
    llm_secondary="copilot/claude-opus-4-6",
    session_limit=int(os.environ.get("PARROT_SESSION_LIMIT", "10")),
    max_tool_calls_per_session=60,
    max_tokens_per_session=int(os.environ.get("PARROT_MAX_TOKENS", "200000")),
    archive_llm_attempt=True,
)


class ParrotHealed(Exception):
    """Raised in teardown when parrot successfully fixes a failure."""


def _git(args: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def _stash_checkpoint(state: dict, charm_path: str, attempt: int) -> None:
    result = _git(
        ["stash", "push", "--include-untracked", "-m", "parrot-recovery"], cwd=charm_path
    )
    stash_created = "No local changes" not in result.stdout
    state["_stash_created"] = stash_created

    if stash_created:
        _git(["stash", "apply"], cwd=charm_path)

    logger.debug("setup: attempt=%d stash_created=%s", attempt, stash_created)


def setup(state: dict, attempt: int) -> dict:
    """Git stash checkpoint for lint/static/unit."""
    charm_path = state.get("charm_path", ".")
    _stash_checkpoint(state, charm_path, attempt)
    return state


def setup_itest(state: dict, attempt: int) -> dict:
    """Git stash checkpoint + juju refresh from clean build for itest."""
    charm_path = state.get("charm_path", ".")
    _stash_checkpoint(state, charm_path, attempt)

    charm_name = Path(charm_path).name
    charm_file = os.environ.get("CHARM_PATH", "")
    if charm_file:
        subprocess.run(
            ["juju", "refresh", charm_name, "--path", charm_file],
            cwd=charm_path, capture_output=True, text=True, check=False,
        )
        logger.debug("setup_itest: refreshed %s from %s", charm_name, charm_file)

    return state


def teardown(state: dict, attempt: int, success: bool) -> None:
    charm_path = state.get("charm_path", ".")

    if success:
        if state.get("_stash_created"):
            _git(["stash", "drop"], cwd=charm_path)

        collection = state.get("_collection", "fix")
        base_branch = _git(
            ["rev-parse", "--abbrev-ref", "HEAD"], cwd=charm_path
        ).stdout.strip()
        fix_branch = f"parrot/{base_branch}/{collection}"

        _git(["checkout", "-b", fix_branch], cwd=charm_path)
        _git(["add", "-A"], cwd=charm_path)
        _git(
            ["commit", "-m", f"fix({collection}): auto-healed by parrot"],
            cwd=charm_path,
        )
        _git(["push", "-u", "origin", fix_branch], cwd=charm_path)

        pr_result = subprocess.run(
            [
                "gh", "pr", "create",
                "--title", f"fix({collection}): auto-healed by parrot",
                "--body", "Automated fix by parrot CI auto-healing.",
                "--base", base_branch,
            ],
            cwd=charm_path, capture_output=True, text=True, check=False,
        )
        pr_url = pr_result.stdout.strip()
        logger.info("fix PR created: %s", pr_url)

        state["suppress_exc"] = False
        raise ParrotHealed(f"Fixed by parrot. PR: {pr_url}")

    _git(["checkout", "--", "."], cwd=charm_path)
    _git(["clean", "-fd"], cwd=charm_path)
    if state.get("_stash_created"):
        _git(["stash", "pop"], cwd=charm_path)

    max_retries = state.get("_max_retries", 3)
    if attempt >= max_retries:
        observations = state.get("_observations", "")
        if observations:
            _post_observations(charm_path, observations)

    logger.debug("teardown: attempt=%d restored workspace", attempt)


def _post_observations(charm_path: str, observations: str) -> None:
    pr_number = _find_pr_number(charm_path)
    if not pr_number:
        logger.warning("no PR found to post observations")
        return

    subprocess.run(
        ["gh", "pr", "comment", pr_number, "--body", observations],
        cwd=charm_path, capture_output=True, text=True, check=False,
    )


def _find_pr_number(charm_path: str) -> str | None:
    result = subprocess.run(
        ["gh", "pr", "view", "--json", "number", "-q", ".number"],
        cwd=charm_path, capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() or None
