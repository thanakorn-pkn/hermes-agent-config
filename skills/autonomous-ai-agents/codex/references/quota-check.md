# Codex quota check

Preferred path:
- Run `python ~/.hermes/scripts/codex_quota.py --json`
- It reads the newest Codex session log under `~/.codex/sessions/`
- It extracts the structured `token_count.rate_limits` payload

Fallback path:
- Use the interactive `/status` screen in a temporary git repo if no session log is available
- This is slower and more brittle, so only use it as a backup
