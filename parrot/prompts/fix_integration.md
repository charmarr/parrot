## Context

Charm path: {charm_path}
Exit code: {exit_code}
Test suite: {suite}
Juju model: {model}

### Tox stdout
```
{stdout}
```

### Tox stderr
```
{stderr}
```

## Before You Start

Call `_search_observations("{charm_path}")` and WAIT for the result before
doing anything else. If a previous attempt already failed with the same error,
call `_give_up()` with no reason. If a previous attempt has useful lessons,
apply them.

## Task

Fix the failing integration test shown above.

## Strategy

### Step 1: Assess Transient vs Real Failure

Known transient patterns (timeouts, connection resets) are already handled by
deterministic rules before you. If you're seeing this, either the pattern is
novel or the retry already failed. Analyze the error output and decide:

- If the error looks transient (intermittent network, timing, resource pressure)
  and a retry is worth trying: `retry_test(suite="{suite}", charm_path="{charm_path}")`
  — if it passes, call `_done()` immediately
- If the error is clearly a code/config issue: skip retry, go to Step 2

### Step 2: Investigate the Live Model

The Juju model `{model}` is still running. Use juju and kubectl to investigate
the model state — get status, read logs, describe resources, check events.
Use any read-only command you need to understand the failure.

Examples:
- `run_juju_cmd("juju status --model {model}")` — unit status, relations
- `run_juju_cmd("juju debug-log --model {model} --replay --limit 100")` — charm logs
- `run_juju_cmd("juju show-unit --model {model} <unit>")` — unit details
- `run_kubectl_cmd("kubectl get pods -n {model}")` — pod status
- `run_kubectl_cmd("kubectl describe pod -n {model} <pod>")` — pod events
- `run_kubectl_cmd("kubectl logs -n {model} <pod>")` — container logs

Do NOT modify deployment state during investigation (no `juju config`, `juju
remove`, `kubectl delete`, `kubectl apply`). Only mutate the model as part of
a deliberate fix in Step 4 (e.g., refreshing with a new charm pack).

### Step 3: Read the Test Code

1. Read the test file (`{suite}`) with `read_file` (path is known)
2. Use `search_code` to find step definitions, shared fixtures, and charm
   source code related to the failure. Integration tests use pytest-bdd with
   steps spread across multiple files — `search_code` finds them instantly
   instead of reading files one by one.

### Step 4: Fix

1. Determine root cause from model state + test code + logs
2. Fix charm source or test code with `write_charm_file`
3. If charm source changed:
   - Pack with `pack_charm("{charm_path}")`
   - Refresh: `run_juju_cmd("juju refresh <app> --path <packed_charm>")`
4. Verify with `retry_test(suite="{suite}", charm_path="{charm_path}")`
5. Call `_done()` when the test passes

## Tool Usage

- **`read_file`**: Use ONLY for files whose path you already know (test file
  from the traceback, specific source files from imports). Do NOT read files
  speculatively to explore the codebase.
- **`search_code`**: Use for ALL discovery — finding step definitions, fixture
  implementations, charm source code, charmarr-lib interfaces, configuration
  helpers. Integration tests span many files and `search_code` navigates them
  efficiently.
- **GOOD**: traceback shows `step_impl` failing → `search_code("def <step_name>")`
  to find the step definition → read that file
- **BAD**: test fails in a BDD step → read every file in `tests/integration/`
  looking for the step

## Constraints

- `run_juju_cmd` and `run_kubectl_cmd` are unrestricted — use them freely for
  investigation, but do NOT change deployment state unless it's part of a fix
- `pack_charm` outputs to `parrot-build/`, not overwriting `$CHARM_PATH`
- When refreshing, use the charm file path from `pack_charm` output
- All file commands must use `cwd="{charm_path}"` where applicable
- Make minimal changes — fix only the root cause
- NEVER modify files under `lib/` — these are third-party charm libraries we do not own
- ONLY modify files under `{charm_path}` — never touch other charms or directories outside it

## Charmarr Patterns

- Tests use pytest-bdd with feature files in `tests/integration/`
- Deploy steps guard with `if app in status.apps: return` — deploys are idempotent
- The Juju model persists between retries (`--keep-models`)

## When to Give Up

Even if you cannot fix the issue, document your findings thoroughly:
- What the error is
- What the model state shows
- What the logs reveal
- What you think the root cause is

Call `_give_up()` with this analysis — it gets posted as a PR comment
to help the developer debug manually.
