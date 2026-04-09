---
name: openclaw-troubleshoot
description: Diagnose and fix OpenClaw gateway service issues on homelab
category: null
---

## OpenClaw Troubleshooting

### Service location
- Systemd service: `openclaw-gateway.service` (user-level)
- Config: `~/.openclaw/openclaw.json`
- Port: 18789 (LAN binding on 0.0.0.0)

### Common issue: crash-loop due to missing GEMINI_API_KEY

**Symptom:** OpenClaw gateway status shows `activating (auto-restart)` with repeated exit code 1, restart counter climbing rapidly.

**Diagnosis:**
```bash
journalctl --user -u openclaw-gateway.service --no-pager -n 20
```

Look for:
```
Error: [WEB_SEARCH_KEY_UNRESOLVED_NO_FALLBACK]
plugins.entries.google.config.webSearch.apiKey SecretRef is unresolved (env:default:GEMINI_API_KEY).
```

**Root cause:** The Google web search plugin in `~/.openclaw/openclaw.json` is configured with `enabled: true` but `GEMINI_API_KEY` is not available in the environment. OpenClaw treats this as a required secret and refuses to start.

**Fix — disable the Google plugin:**
```bash
# Edit ~/.openclaw/openclaw.json
# Change the google plugin entry:
# "google": { "enabled": false, ... }
```

Or with jq:
```bash
jq '.plugins.entries.google.enabled = false' ~/.openclaw/openclaw.json > /tmp/openclaw-tmp.json && mv /tmp/openclaw-tmp.json ~/.openclaw/openclaw.json
```

**Restart the service:**
```bash
systemctl --user stop openclaw-gateway.service
sleep 1
systemctl --user start openclaw-gateway.service
sleep 3
systemctl --user status openclaw-gateway.service
```

### Service management
```bash
# Status
systemctl --user status openclaw-gateway.service

# Restart
systemctl --user restart openclaw-gateway.service

# Stop (disable for maintenance)
systemctl --user stop openclaw-gateway.service

# View logs
journalctl --user -u openclaw-gateway.service --no-pager -f

# View recent errors
journalctl --user -u openclaw-gateway.service --no-pager -n 50
```

### Paperclip relationship
- Paperclip may have a `hermes_local` agent heartbeat configured
- Paperclip is NOT using the OpenClaw gateway adapter by default (it uses `hermes_local`)
- Paperclip can be stopped independently: `systemctl --user stop paperclip-app.service`
- Paperclip heartbeats fail silently if JWT secret is missing — they don't consume API usage
