---
name: hermes-delegate-acp-routing
description: Diagnose and safely route Hermes delegate_task ACP overrides. Explains when acp_command/acp_args are actually honored and how to avoid silent fallback to the parent HTTP transport.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, delegation, acp, routing, debugging]
    related_skills: [hermes-agent, claude-code, codex]
---

# Hermes delegate_task ACP routing

Use this when investigating or using `delegate_task(..., acp_command=..., acp_args=...)` in Hermes.

## Key finding

In the current Hermes implementation, explicit `acp_command` / `acp_args` overrides are only consumed by the `copilot-acp` child runtime.

They do **not** automatically switch a child from a normal HTTP provider transport to an arbitrary subprocess transport.

That means requests like:
- `acp_command: "claude"`
- `acp_command: "codex"`
- `acp_command: "gemini"`

should be treated as unsupported unless the resolved child runtime is already `copilot-acp`.

## Practical rule

Before assuming an ACP override will work, verify the resolved child runtime:
- provider is `copilot-acp`, or
- base URL uses the `acp://copilot` marker

If not, the child is still on a normal provider path and ACP overrides should fail fast instead of being trusted.

## Symptoms of the bug pattern

Watch for these signs:
- delegated child metadata still reports the parent's HTTP model
- `acp_command` is present on the child object, but the instantiated client is still a normal OpenAI-style client
- a request appears to ignore the requested subprocess route and uses the inherited provider instead
- retries end in a generic message like `API call failed after 3 retries: ...`, masking the original transport mismatch

## Separate but related stall class: gateway inactivity timeout

Not every delegation stall is an ACP-routing problem.
A separate failure mode is the parent session appearing idle while a child subagent is still working.

Watch for these signs:
- delegated work runs for a while, then the gateway kills the parent for "no activity"
- the child is busy, but the parent's activity timestamp is not being refreshed
- tests or code mention a delegation heartbeat thread / `_touch_activity`

Current Hermes code includes a heartbeat loop in `tools/delegate_tool.py` that periodically propagates child activity back to the parent, and tests in `tests/tools/test_delegate.py` verify that it fires during child execution and stops after completion.

Practical debugging rule:
- if the symptom is **wrong transport / wrong model / HTTP fallback**, debug ACP routing
- if the symptom is **timeout during long-running child work**, inspect heartbeat propagation separately

## Systematic debug steps

1. Reproduce with a minimal child build.
2. Inspect the resolved child fields:
   - `provider`
   - `api_mode`
   - `base_url`
   - `acp_command`
   - client class
3. Confirm whether transport creation is gated on a specific provider/runtime.
4. Check shell lookup only after confirming the override is actually supposed to launch a subprocess.

## Shell lookup findings to verify separately

If command lookup becomes relevant:
- compare non-interactive shell lookup with interactive `bash -ic`
- verify the target CLI actually supports the expected ACP flags
- use absolute paths for cron or non-interactive launches when PATH differs

### Concrete findings from this machine

- `claude` is on the normal non-interactive PATH, but the installed Claude Code CLI does **not** support `--acp`
- `codex` is typically only available in interactive `bash -ic` via `/data/pnpm/codex`, and the installed CLI does **not** support `--acp` (it exposes `mcp-server`, not the expected ACP stdio flags)
- `gemini` is typically only available in interactive `bash -ic` via `/data/pnpm/gemini`, and **does** expose `--acp`

Practical consequence:
- `acp_command='claude'` is not a valid ACP target on this host
- `acp_command='codex'` will usually fail in non-interactive contexts unless routed via absolute path, and even then is not a valid `--acp` target with the currently installed CLI
- `acp_command='gemini'` may be ACP-capable as a CLI, but Hermes should still reject it unless the resolved child runtime is one that actually consumes explicit ACP overrides

## Safe routing guidance

- Prefer normal provider routing for Claude, Codex, and Gemini child agents unless Hermes has explicit transport support for them.
- Use `acp_command` only with runtimes that are known to consume it.
- If unsupported, return a clear error instead of silently inheriting the parent HTTP transport.

## Good fix pattern

The minimal safe fix is:
1. validate explicit ACP overrides against the resolved runtime
2. reject unsupported combinations early with a clear error
3. update help text/schema docs so they do not promise arbitrary ACP child spawning

## Verification checklist

- unsupported ACP override now returns a clear error
- supported ACP runtime still accepts the override
- no silent fallback to inherited HTTP transport remains
- docs/help text match real behavior
