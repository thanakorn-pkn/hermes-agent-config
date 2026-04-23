---
name: hermes-errno12-spawn-pressure
description: "Diagnose Hermes Errno 12 Cannot allocate memory failures on tiny local tool calls. Focuses on subprocess spawn pressure vs. true host OOM."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, debugging, subprocess, memory, terminal, file-tools]
    related_skills: [hermes-agent, systematic-debugging, claude-code]
---

# Hermes `Errno 12` Spawn-Pressure Diagnosis

Use this when Hermes starts failing small local tool calls like `terminal`, `read_file`, `search_files`, or `execute_code` with:

- `OSError: [Errno 12] Cannot allocate memory`
- `Command execution failed: OSError: [Errno 12] Cannot allocate memory`

## Key finding

Do **not** assume full host OOM immediately.

On the local backend, Hermes is subprocess-heavy even for small operations:
- `terminal` creates a fresh shell subprocess for each command
- `read_file` and `search_files` route through shell-backed file operations
- `execute_code` spawns a child Python interpreter

That means transient subprocess allocation failure can break many tools at once, even when the host still shows plenty of free RAM.

## What to inspect

### 1. Reconstruct the failure pattern from session evidence
Look for a sequence like:
- long-lived Claude/Codex/tmux work starts
- tiny `terminal(...)` calls begin failing with `Errno 12`
- `read_file(...)`, `search_files(...)`, and `execute_code(...)` start failing too
- killing one stale heavyweight process restores Hermes

This pattern strongly suggests subprocess spawn pressure, not generic app logic breakage.

### 2. Check live host memory and commit state
Use:
```bash
free -h
cat /proc/meminfo | egrep 'MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree|CommitLimit|Committed_AS'
cat /proc/sys/vm/overcommit_memory
cat /proc/sys/vm/overcommit_ratio
```

Interpretation:
- healthy `MemAvailable` does **not** rule out this failure mode
- compare `Committed_AS` against `CommitLimit`
- overcommit settings can make `fork()` fail before host RAM is actually exhausted

### 3. Check for stale heavyweight sibling processes
Inspect long-lived processes first, especially:
- `claude`
- `codex`
- `tmux`
- Hermes/OpenClaw helper processes
- backend/frontend dev servers

If a stale one-shot agent process exists alongside new tmux-backed sessions, suspect that first.

### 4. Check service and cgroup limits
Use systemd/user service inspection to rule out service-local ceilings.

### 5. Inspect the code path before proposing fixes
Confirm that all failing tools converge on subprocess creation.

Relevant files:
- `tools/environments/local.py`
- `tools/environments/base.py`
- `tools/terminal_tool.py`
- `tools/file_tools.py`
- `tools/file_operations.py`
- `tools/code_execution_tool.py`
- `tools/process_registry.py`

Expected conclusion in this failure mode:
- local backend is spawn-per-call
- file tools share that same execution path
- `execute_code` also spawns a child process
- therefore many unrelated small tools fail together once process creation degrades

## Practical operating guidance

- Reuse existing long-lived Claude/Codex sessions instead of stacking more.
- Reap stale one-shot agent processes before launching new tmux-backed sessions.
- Treat tiny-call `Errno 12` as a **spawn-pressure signal first**.
- If killing one stale heavyweight process restores Hermes, prefer that explanation over host-wide OOM.

## Fix guidance

Do not jump straight to a code patch.

Usually this is primarily an operational/runtime issue, not a simple logic bug. A code change may improve resilience, but only after confirming the true cause.

A reasonable hardening idea to consider later:
- reduce shell/subprocess dependence for local file reads so `read_file` can still work during spawn degradation

But do **not** present that as the main fix unless verified.
