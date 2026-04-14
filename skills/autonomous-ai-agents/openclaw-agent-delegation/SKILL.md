---
name: openclaw-agent-delegation
description: Delegate tasks to an existing OpenClaw gateway/agent, verify delivery, and distinguish configured agent identity from the backing model.
---

## When to use
Use this when the user wants Hermes to send a task through OpenClaw, especially on a host where OpenClaw is already installed and running.

## Key findings
1. `openclaw agent` requires an explicit session selector. If you omit `--to`, `--session-id`, and `--agent`, it fails with:
   `Error: Pass --to <E.164>, --session-id, or --agent to choose a session`
2. The model/provider reported by OpenClaw is NOT necessarily the agent's configured name/persona.
3. The configured persona identity lives in the OpenClaw workspace files, especially `~/.openclaw/workspace/IDENTITY.md`.

## Fast path
### 1) Check OpenClaw is available
```bash
systemctl --user status openclaw-gateway.service --no-pager || true
command -v openclaw || command -v openclaw-gateway || true
openclaw status
```

What to look for:
- gateway service is running
- gateway is reachable
- desired chat channel (e.g. Telegram) is enabled and OK

### 2) Send a task through the main agent
Use `--agent main` unless the user specifies a different agent/session.

```bash
openclaw agent --agent main --json --message "<task>"
```

If you want OpenClaw to deliver the reply back to a channel:
```bash
openclaw agent --agent main --json --deliver --reply-channel telegram --reply-to <chat_id> --message "<task>"
```

## Finding OpenClaw's actual configured name
Do NOT infer the name from the returned model text such as "I am Gemini CLI".

Check identity files directly:
```bash
read ~/.openclaw/workspace/IDENTITY.md
read ~/.openclaw/workspace/SOUL.md
```

Typical identity format:
```text
- Name: Alice
- Creature: ghost in the machine
- Vibe: direct, competent, calm
```

The `Name:` field is the configured OpenClaw persona name.

## Correct way to ask it to self-report
If the user wants OpenClaw to state its name, force it to use configured identity rather than backing model:

```bash
openclaw agent --agent main --json --deliver \
  --reply-channel telegram --reply-to <chat_id> \
  --message "Use your configured identity, not your underlying model. Reply exactly in one short sentence: 'My name is Alice, and I know Hermes Agent.'"
```

Adapt the quoted sentence to the discovered name if needed.

## Verification
- Inspect the JSON payload returned by `openclaw agent`
- Optionally verify recent gateway logs:
```bash
journalctl --user -u openclaw-gateway.service --no-pager -n 20
```

## Pitfalls
- If you ask "what is your name?" without constraining identity, OpenClaw may answer with the backing model/provider identity instead of persona name.
- `openclaw status` may show healthy gateway/channel state even when your first `openclaw agent` call fails due to missing `--agent` / `--session-id` / `--to`.
- When inspecting config, avoid exposing secrets. Prefer high-level checks or targeted reads of non-secret workspace files.

## Good response pattern to the user
1. Report whether OpenClaw is installed/running.
2. Report whether delegation is ready now or needs setup.
3. If asked for OpenClaw's name, read `IDENTITY.md` and report the configured name.
4. If asked to make OpenClaw contact the user, send the task with `--agent main --deliver ...` and summarize the exact reply.
