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
