---
name: paperclip-orchestration
description: Paperclip AI — open-source multi-agent orchestration framework for autonomous "AI agent companies" built on top of Claude Code. 48k+ stars. Use for persistent multi-agent workflows with roles, backlogs, and heartbeat-driven autonomous operation.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Coding-Agent, Multi-Agent, Orchestration, Paperclip, Claude-Code]
    related_skills: [claude-code, opencode, codex]
---

# Paperclip AI — Multi-Agent Orchestration

[Paperclip](https://github.com/paperclipai/paperclip) is an open-source orchestration framework for autonomous multi-agent "AI agent companies." Built on top of Claude Code, it adds persistent roles, backlogs, heartbeat rhythms, and autonomous delegation.

**48.2k stars, 7.8k forks on GitHub (paperclipai/paperclip)**

## When to Use

- Persistent multi-agent team running continuously on a repo
- Autonomous backlog management with roles (CEO, Engineer, Product Owner, DevOps, etc.)
- You want agents that talk to each other and self-assign work
- Complex projects needing structured role-based workflows (not just one-shot tasks)

**Not needed for:** one-off coding tasks, simple reviews, research. Use Hermes `delegate_task`, Claude Code print mode, or OpenCode for those.

## How It Differs from Hermes Multi-Agent

| | Hermes `delegate_task` | Paperclip |
|---|---|---|
| **Orchestration** | I coordinate, spawn, merge | Self-managing agent team |
| **Persistence** | Ephemeral — returns results | Persistent roles, backlog, heartbeat |
| **Communication** | Agents don't talk to each other | Agents auto-delegate, fallback chains |
| **Best for** | On-demand tasks, parallel work | Continuous autonomous operation |

## Core Concepts

### Roles and Fallbacks

Every "company" starts with a **CEO** — who can handle everything alone. As you add specialists, responsibilities shift:

- **CEO** — strategy, backlog, final fallback for everything
- **Engineer** — implementation, git, technical decisions
- **Product Owner** — backlog management, auto-assignment
- **DevOps** — CI/CD, monitoring
- **Security Engineer** — threat modeling, security review
- **QA** — testing, accessibility audit
- Plus: UX Researcher, UI Designer, Technical Writer, CMO, Customer Success, Game Designer, etc.

No role is ever missing — fallback chains ensure someone always handles the work.

### Presets

| Preset | Best for |
|--------|----------|
| `fast` | Solo engineer, prototypes, MVPs |
| `quality` | Teams, production systems (adds PO + Code Reviewer) |
| `startup` | Strategy-first, grow organically |
| `secure` | Regulated industries, fintech, healthtech |
| `full` | Complete setup — all modules + reviewers |
| `launch-mvp` | Ship a first version end-to-end |
| `build-api` | Build REST/GraphQL API from scratch |
| `build-game` | Game development pipeline |
| `repo-maintenance` | Existing repo triage, dependencies, releases |
| `gtm` | Market-facing products with competitive positioning |
| `content` | Dev tools, documentation-heavy projects |

### Company Wizard Plugin

By [Yesterday-AI](https://github.com/Yesterday-AI): `paperclip-plugin-company-wizard` (71 stars)

Bootstrap companies from templates via CLI or AI mode. Install via npm: `@yesterday-ai/paperclip-plugin-company-wizard`

**Two modes:**
1. **AI mode** — describe your project in plain language, wizard picks preset/modules/roles
2. **Manual mode** — step through preset, modules, roles yourself with hover-card previews

## Installation (Official Steps)

**Prerequisites:** Node.js 20+, pnpm 9+

```bash
# Clone to persistent location (NOT /tmp — dev runner tracks by repo path)
cd ~/projects
git clone --depth 1 https://github.com/paperclipai/paperclip.git
cd paperclip

# Install dependencies
pnpm install

# Start dev server (background for orchestration)
pnpm dev           # watch mode, auto-restarts on changes
# Or pnpm dev:once  # one-shot start without file watching
```

This starts:
- **API server:** http://localhost:3100
- **UI:** http://localhost:3100 (served by API in dev middleware mode)
- **Database:** embedded PostgreSQL at `~/.paperclip/instances/default/db` (auto-created)
- **Migrations:** auto-applied on first boot

**Quick health checks:**
```bash
curl http://localhost:3100/api/health      # {"status":"ok"}
curl http://localhost:3100/api/companies   # [] (empty array = fresh install)
```

### Stop dev runner
```bash
cd ~/projects/paperclip && pnpm dev:stop
# Or force kill: pkill -f "paperclip"; pkill -f "dev-watch"; pkill -f "dev-runner"; sleep 2
```

### LAN Access — Allowed Hostnames

In `authenticated` mode, you must explicitly allow hostnames that can access the UI:
```bash
node /home/tphat/.npm/_npx/*/paperclipai/dist/index.js allowed-hostname <hostname-or-ip>
# Example: add 192.168.1.161
node /home/tphat/.npm/_npx/*/paperclipai/dist/index.js allowed-hostname 192.168.1.161
# Then restart Paperclip for it to take effect.
```
This updates `allowedHostnames` in `config.json`. The npx CLI version works fine for config commands — the ESM bug only affects server startup.

### Firewall / LAN Access

By default Paperclip binds to `127.0.0.1:3100` (localhost only). Paperclip **rejects** non-loopback binding in `local_trusted` mode:
```
Error: local_trusted mode requires loopback host binding (received: 0.0.0.0). Use authenticated mode for non-loopback deployments.
```

**Option 1: Use a reverse proxy or port forward** (keeps `local_trusted` mode):
```bash
# Simple socat relay — forwards LAN port to localhost:3100
socat TCP-LISTEN:3101,fork,reuseaddr,bind=0.0.0.0 TCP:127.0.0.1:3100 &
# Or with iptables:
sudo iptables -t nat -A PREROUTING -p tcp --dport 3100 -j REDIRECT --to-port 3100
# Or with nginx reverse proxy:
nginx -c /path/to/proxy.conf
```

**Option 2: Switch to `authenticated` mode** (recommended for LAN access, requires board claim):
1. Edit `~/.paperclip/instances/default/config.json`:
   ```json
   "deploymentMode": "authenticated",
   "host": "0.0.0.0",
   ```
2. Update `pg_hba.conf` to allow non-loopback connections to the embedded PostgreSQL:
   ```
   # Add these lines after the 127.0.0.1/32 line in ~/.paperclip/instances/default/db/pg_hba.conf
   host    all             all             0.0.0.0/0               password
   host    all             all             ::0/0                   password
   ```
3. Restart Paperclip via `pnpm dev` from the cloned repo directory (NOT the npx cached version — it has ESM/require() crashes).
4. On first boot, visit `http://<LAN-IP>:3100` in a browser to complete the board claim flow.
5. After claiming, the server accepts connections from any interface on port 3100.

**Add UFW rules** (homelab-infra Ansible firewall role):
In `hosts/inventory/host_vars/<hostname>.yml`, add under `firewall_rules`:
```yaml
# Paperclip - AI agent orchestration UI
- rule: allow
  port: 3100
  proto: tcp
  from_ip: "{{ network.cidr }}"
  comment: "Paperclip UI from LAN"
- rule: allow
  port: 3100
  proto: tcp
  from_ip: "{{ network.ula_cidr }}"
  comment: "Paperclip UI from LAN (ULA)"
```
Then reapply: `ansible-playbook -i hosts/inventory/hosts.ini hosts/playbooks/<site>.yml --tags firewall`

## Gemini ACP Delegation Status

`delegate_task` with `acp_command: "gemini"` currently falls back to the parent model. Root cause: the delegation system only activates ACP transport when `provider == "copilot-acp"`. When `acp_command` is provided independently (e.g., for Gemini or OpenCode), the provider/base_url still point to the parent's OpenRouter config, so the ACP transport path is never triggered.

**Workaround:** Use direct CLI execution (`gemini -p "prompt"`) or `delegate_task` with `acp_command` and `acp_args` pointing to models that the routing supports (Claude Code, Codex, OpenCode).

## Related: LLM Benchmark for NUC-13-Pro

For the NUC-13-Pro (i5-1340P, 30GB RAM, CPU-only), recommended local models:

| Role | Model | Quant | Size | Expected TG | 200tok Time |
|------|-------|-------|------|-------------|-------------|
| Brain | Phi-4-mini 3.8B | Q4_K_M | 2.8GB | 6-9 t/s | 22-33s |
| Brain | Qwen3-8B | Q4_K_M | 5.2GB | 4-6 t/s | 35-50s |
| Coder | Qwen2.5-Coder-7B | Q4_K_M | 4.7GB | 4-7 t/s | 30-50s |
| Coder | Qwen2.5-Coder-14B | Q4_K_M | 9.0GB | 2-3 t/s | 67-100s |

Install via Ollama: `ollama pull phi4-mini`, `ollama pull qwen2.5-coder:7b`

## Pitfalls

1. **DO NOT use `npx paperclipai onboard`** — it crashes with ESM/`require()` errors on Node 24:
   ```
   require() cannot be used on an ESM graph with top-level await
   ```
   Always clone + `pnpm install` + `pnpm dev` instead.

2. **DO NOT clone to `/tmp`** — the dev runner tracks sessions by repo path. Use a persistent location like `~/projects/paperclip`.

3. **Kill ALL paperclip processes before restarting:**
   ```bash
   pkill -f "paperclip"; pkill -f "dev-watch"; pkill -f "dev-runner"; sleep 2
   ```
   Otherwise you'll get port conflicts or duplicate embedded PostgreSQL instances. The `pnpm dev` runner also has a stale-session guard that says "already running (pid X)" — full process kill is the only way.

4. **Config changes require restart** — editing `config.json` does NOT take effect until Paperclip is restarted. Kill ALL processes (embedded PG too) then restart.

5. **Persistent process management** — the dev runner spawns a multi-process tree. Use `nohup` from a wrapper script and save the launcher PID. The child PIDs change across restarts.
   ```bash
   # Wrapper: start-paperclip.sh
   #!/usr/bin/env bash
   cd /home/tphat/projects/paperclip
   exec pnpm dev:once  # one-shot without file watching
   # Launch:
   nohup ./start-paperclip.sh > ~/.paperclip/instances/default/logs/paperclip-stdout.log 2>&1 &
   echo $! > ~/.paperclip/instances/default/paperclip.pid
   ```

6. **Board claim requirement** — after switching from `local_trusted` to `authenticated`, the server starts but requires a one-time board ownership claim before full operation. The claim URL is logged on startup: `http://<IP>:3100/board-claim/<hash>?code=<code>`. Replace `localhost` with the LAN IP when accessing remotely.

7. **Reset local dev data:**
   ```bash
   rm -rf ~/.paperclip/instances/default/db
   pnpm dev
   ```

### Company Wizard Plugin

Install via Paperclip UI: Settings > Plugins > Install Plugin
```bash
@yesterday-ai/paperclip-plugin-company-wizard
```
Or globally: `pnpm add -g @yesterday-ai/paperclip-plugin-company-wizard`

## Paperclip + OpenCode

Paperclip runs on Claude Code as its execution engine, not OpenCode. For OpenCode-based multi-agent work that's simpler and cheaper (can use free OpenRouter models), prefer Hermes `delegate_task` with `acp_command: "opencode"`.

You could theoretically wire OpenCode as a Paperclip execution backend, but this isn't a supported pattern. Paperclip deeply integrates with Claude Code's session management and tools.

## Cost Considerations

- Paperclip runs Claude Code agents continuously — costs scale with operation hours
- Hermes `delegate_task` + OpenCode + free OpenRouter models = zero-cost alternative for simpler multi-agent needs
- Paperclip is worth the cost when you need persistent, role-based autonomous operation that Hermes doesn't natively provide

## Rules

1. Paperclip is heavy infrastructure — only use when you need persistent autonomous teams
2. For ad-hoc multi-agent parallelism, Hermes `delegate_task` with ACP routing is faster and cheaper
3. Paperclip requires Claude Code as the execution backend (not OpenCode)
4. Company Wizard plugin is optional but recommended for quick setup
5. The CEO role is always present and handles everything as fallback — you can start with just CEO for simple projects