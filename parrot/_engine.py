"""Parrot Theow instance."""

from __future__ import annotations

import os
from pathlib import Path

from theow import GatewayConfig, Theow

_dry_run = False

parrot = Theow(
    theow_dir=Path(__file__).parent,
    name="Parrot",
    llm="claude-agent/claude-opus-4-6",
    llm_secondary="claude-agent/claude-opus-4-6",
    session_limit=int(os.environ.get("PARROT_SESSION_LIMIT", "10")),
    max_tool_calls_per_session=60,
    max_tokens_per_session=int(os.environ.get("PARROT_MAX_TOKENS", "1000000")),
    archive_llm_attempt=True,
    _gateway_config=GatewayConfig(options={"effort": "high"}),
    logfire=True,
)
