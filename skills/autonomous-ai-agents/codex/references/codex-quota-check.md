# Codex quota check

Preferred path:
- Run `python ~/.hermes/scripts/codex_quota.py --json`
- This reads the newest Codex session log in `~/.codex/sessions/`
- It extracts the structured `token_count.rate_limits` payload

Returned fields:
- `source: session-log`
- `plan_type`
- `primary.used_percent` / `primary.left_percent` + reset time
- `secondary.used_percent` / `secondary.left_percent` + reset time
- source file + event timestamp

Fallback path if logs are missing or stale:
- Start Codex in a temporary git repo
- Use the interactive `/status` screen in tmux
- Capture the quota panel from the TUI
