<div align="center">

# parrot

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
[![theow](https://img.shields.io/badge/theow-%E2%89%A50.0.20-green)](https://pypi.org/project/theow/)
![License](https://img.shields.io/badge/license-GPL--3.0-red)
[![charmarr](https://img.shields.io/badge/scope-charmarr%20charms-orange)](https://github.com/charmarr/charmarr)

CI auto-healing for charmarr charms using [theow](https://github.com/adhityaravi/theow).

</div>

Parrot wraps tox invocations with theow's recovery loop. When tox fails, deterministic rules handle known patterns (ruff, codespell, transient errors) and LLM rules investigate novel failures. Fixes are delivered as PRs against the feature branch.

## Usage

```bash
python -m parrot <collection> --charm-path <path> [--suite <test_file>]
```

Collections: `lint`, `static`, `unit`, `itest`

```bash
# lint a charm
python -m parrot lint --charm-path charms/prowlarr-k8s

# run integration test
python -m parrot itest --charm-path charms/prowlarr-k8s --suite test_deploy.py
```

## How it works

```
tox passes  → exit 0, no overhead
tox fails   → theow recovery loop
            → deterministic rule? → auto-fix → retry tox
            → LLM rule?          → investigate with gated tools → retry tox
            → fix found?         → create PR, CI fails with PR link
            → no fix?            → post observations as PR comment, CI fails
```

## Setup

```bash
uv run --project . python -m parrot --help
```

Requires `GITHUB_TOKEN` in CI for PR creation. LLM rules support Copilot, Anthropic, and Gemini APIs via theow.
