---
name: codex
description: Delegate coding tasks to OpenAI Codex CLI agent. Use for building features, refactoring, PR reviews, and batch issue fixing. Requires the codex CLI and a git repository.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

Delegate coding tasks to [Codex](https://github.com/openai/codex) via the Hermes terminal. Codex is OpenAI's autonomous coding agent CLI.

## Prerequisites

- Codex installed: `npm install -g @openai/codex`
- OpenAI API key configured
- **Must run inside a git repository** — Codex refuses to run outside one
- Use `pty=true` in terminal calls — Codex is an interactive terminal app

## Usage / auth probes

Use these live checks before assuming Codex usage or billing state:

```bash
codex login status
codex exec --json "reply with usage stats only"
```

Observed on this host:
- `codex login status` prints `Logged in using ChatGPT`
- `codex exec --json ...` returns a JSON usage block even when the agent reply is `Usage stats: unavailable`
- `codex -p "/status"` is not a valid probe on this CLI and can fail with config-profile errors

## Programmatic quota check (preferred)

Codex session logs in `~/.codex/sessions/` contain structured `token_count` events with a `rate_limits` payload. That is the best zero-touch source for quota checks.

Use the helper script:
```bash
python ~/.hermes/scripts/codex_quota.py --json
```

It returns:
- `source: session-log`
- `plan_type`
- `primary.used_percent` / `primary.left_percent` + reset time
- `secondary.used_percent` / `secondary.left_percent` + reset time
- source file + event timestamp

## Interactive fallback

If the logs are missing or stale, use the interactive `/status` screen in a Codex TUI session. On this host it shows:
- Account type and collaboration mode
- Current model and permission mode
- 5h limit remaining percentage and reset time
- Weekly limit remaining percentage and reset time
- A pointer to the web usage page: `https://chatgpt.com/codex/settings/usage`

Example flow:
```bash
tmpdir=$(mktemp -d)
git init "$tmpdir"
tmux new-session -d -s codexquota -x 140 -y 40 "bash -ic 'cd $tmpdir && codex'"
# accept the workspace trust prompt with Enter
tmux send-keys -t codexquota Enter
# once inside Codex, run:
/status
```

Notes:
- A temporary empty git repo is sufficient for quota/status checks.
- `~/.hermes/scripts/codex_quota.py` is the preferred low-token path.
- The TUI can be driven via tmux or a background PTY process if you need the interactive panel for verification.
## One-Shot Tasks

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (Codex needs a git repo):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Background Mode (Long Tasks)

```
# Start in background with PTY
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Interactive tmux Sessions

For multi-turn interactive Codex work, use a named tmux session the same way you would for Claude Code-style long-lived agent sessions.

### Current machine notes

On this machine, `codex` may be missing from the default non-interactive PATH even though it exists at `/data/pnpm/codex` and works inside `bash -ic`.

When a foreground or cron-style launch says `codex: command not found`, verify both:
- `command -v codex`
- `bash -ic 'command -v codex && codex --version'`

For unattended automation, prefer one of these:
- absolute path: `/data/pnpm/codex`
- interactive shell wrapper: `bash -ic 'codex ...'`

Codex may also show an updater prompt on startup:
- `1. Update now`
- `2. Skip`
- `3. Skip until next version`

For autonomous tmux sessions, send `2` + Enter first if that prompt appears, then send the actual task.

Why use tmux:
- keeps Codex alive across multiple checks/messages
- makes it easy to capture output incrementally
- works well when you want a durable interactive session rather than a one-shot `codex exec`

Pattern:

```
# Start Codex in a repo inside tmux
terminal(command="tmux new-session -d -s codex-agent -x 120 -y 40 'cd ~/project && codex'", timeout=10)

# Give it a moment to start, then send the task
terminal(command="sleep 5 && tmux send-keys -t codex-agent 'Review this repo and propose a refactor plan' Enter", timeout=10)

# Read the current screen contents
terminal(command="tmux capture-pane -t codex-agent -p", timeout=5)

# Send follow-up instructions
terminal(command="tmux send-keys -t codex-agent 'Now implement step 1' Enter", timeout=5)

# End the session when done
terminal(command="tmux send-keys -t codex-agent C-c && sleep 1 && tmux kill-session -t codex-agent", timeout=10)
```

Notes:
- Codex still must run inside a git repo
- prefer `codex exec ...` for simple one-shot tasks
- prefer tmux when you want iterative control, durable state, or repeated follow-ups

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes in workspace |
| `--dangerously-bypass-approvals-and-sandbox` | No sandbox, no approvals (fastest, most dangerous; current CLI flag) |

## PR Reviews

Clone to a temp directory for safe review:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex --dangerously-bypass-approvals-and-sandbox exec 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex --dangerously-bypass-approvals-and-sandbox exec 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Batch PR Reviews

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## Rules

1. **Always use `pty=true`** — Codex is an interactive terminal app and hangs without a PTY
2. **Git repo required** — Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch
3. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly
4. **`--full-auto` for building** — auto-approves changes within the sandbox
5. **Background for long tasks** — use `background=true` and monitor with `process` tool
6. **Don't interfere** — monitor with `poll`/`log`, be patient with long-running tasks
7. **Parallel is fine** — run multiple Codex processes at once for batch work
