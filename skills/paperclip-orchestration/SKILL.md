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

## Production Hosting Strategy (Podman + Host App)

For homelab setups where host CLIs (Claude Code, Codex, Gemini, Hermes) must be directly accessible:

**Architecture:**
- **Postgres 17** → Standalone Podman quadlet container (`~/.config/containers/systemd/paperclip-db.container`), publishes port 5432 on localhost
- **Paperclip app** → Runs directly on the host via systemd user service, NOT containerized

**Quadlet file (`~/.config/containers/systemd/paperclip-db.container`):**
```ini
[Unit]
Description=PostgreSQL 17 for Paperclip

[Container]
Image=docker.io/library/postgres:17-alpine
ContainerName=paperclip-db
Volume=paperclip-pgdata:/var/lib/postgresql/data
PublishPort=5432:5432
Environment=POSTGRES_USER=paperclip
Environment=POSTGRES_PASSWORD=<strong_password>
Environment=POSTGRES_DB=paperclip
HealthCmd=pg_isready -U paperclip -d paperclip -h localhost || exit 1
HealthInterval=10s
HealthTimeout=5s
HealthRetries=5
HealthStartPeriod=30s

[Service]
Restart=always
RestartSec=5
TimeoutStartSec=90

[Install]
WantedBy=default.target
```

**systemd app service (`~/.config/systemd/user/paperclip-app.service`):**
```ini
[Unit]
Description=Paperclip AI Agent Orchestrator (host mode)
After=podman.service podman.socket
Wants=podman.socket

[Service]
Type=simple
WorkingDirectory=/home/tphat/projects/paperclip
ExecStart=/home/tphat/.local/share/pnpm/pnpm dev:once
Restart=on-failure
RestartSec=10
Environment=HOME=/home/tphat
Environment=PATH=/home/tphat/.local/share/pnpm:/home/tphat/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=NODE_ENV=production
Environment=PORT=3100
Environment=HOST=0.0.0.0
Environment=DATABASE_URL=postgresql://paperclip:<password>@127.0.0.1:5432/paperclip
Environment=BETTER_AUTH_SECRET=<random_hex_32>
Environment=PAPERCLIP_DEPLOYMENT_MODE=authenticated
Environment=PAPERCLIP_DEPLOYMENT_EXPOSURE=private
Environment=PAPERCLIP_PUBLIC_URL=http://<LAN_IP>:3100
Environment=PAPERCLIP_CONFIG=<path_to_config.json>
Environment=npm_config_tailscale_auth=true
StandardOutput=journal
StandardError=journal
SyslogIdentifier=paperclip-app

[Install]
WantedBy=default.target
```

**config.json** (database section):
```json
"database": {
  "mode": "postgres",
  "connectionString": "postgresql://paperclip:<password>@127.0.0.1:5432/paperclip"
}
```

**Why this pattern:** Docker containerizing the Paperclip app creates painful bind-mount complexity for multiple host-installed CLIs (Claude Code, Codex, Gemini, Hermes). Running the app on the host gives it free access to all CLIs while keeping Postgres isolated and backup-friendly.

**Key pitfalls:**
1. `dev:once` defaults to `local_trusted` mode. You MUST set `Environment=npm_config_tailscale_auth=true` in systemd OR pass `--tailscale-auth` flag to force `authenticated` mode with `0.0.0.0` binding.
2. Postgres must publish port 5432 (not be in a Podman pod) when the app runs on the host.
3. Run `systemctl --user daemon-reload` after any unit file change to regenerate quadlet units.

## Bootstrap Admin Flow (No CLI in Production Image)

When no admin user exists and the CLI isn't available (e.g., production Docker image):

1. Check health: `bootstrapStatus: "bootstrap_pending"`, `bootstrapInviteActive: false`
2. Insert bootstrap invite directly into PostgreSQL:
```sql
-- Generate token: pcp_bootstrap_<48 hex chars>
-- Hash: SHA-256 of the full token string
INSERT INTO invites (id, company_id, invite_type, token_hash, allowed_join_types, defaults_payload, expires_at, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  NULL,
  'bootstrap_ceo',  -- MUST be exactly 'bootstrap_ceo', not 'bootstrap'
  '<sha256_hash_of_token>',
  '[]',
  '{"roles": ["instance_admin"], "preset": null}'::jsonb,
  NOW() + INTERVAL '24 hours',
  NOW(),
  NOW()
);
```
3. Verify: `bootstrapInviteActive` should be `true` on `/api/health`
4. Create user and accept invite via curl:
```bash
# Step 1: Create account
curl -X POST http://localhost:3100/api/auth/sign-up/email \
  -H "Content-Type: application/json" \
  -d '{"email":"you@domain.com","name":"Your Name","password":"StrongPass123!"}' \
  -c /tmp/pc_cookie

# Step 2: Accept bootstrap invite (requires Origin header + session cookie)
curl -X POST "http://localhost:3100/api/invites/<full_token>/accept" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3100" \
  -d '{"requestType":"human"}' \
  -b /tmp/pc_cookie
```
5. Verify: `bootstrapStatus` becomes `"ready"`

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

7. **Full production wipe (Podman quadlet + host systemd):**
   When you want a completely clean slate and set up admin via the UI (no SQL):
   ```bash
   # 1. Stop all services
   systemctl --user stop paperclip-app.service paperclip-db.service

   # 2. Wipe the Podman PG volume (this is where all user/instance data lives)
   podman volume rm paperclip-pgdata

   # 3. Wipe host-mounted instance data (config, logs, secrets, storage)
   rm -rf ~/.local/share/paperclip/instances/default/{config,data,logs,secrets}

   # 4. Restart — Postgres will re-init on a fresh volume
   systemctl --user daemon-reload
   systemctl --user start paperclip-db.service
   sleep 8  # wait for PG init
   systemctl --user start paperclip-app.service

   # 5. Health check should show bootstrap_pending
   curl -s http://localhost:3100/api/health

   # 6. Create a bootstrap invite (UI won't show signup until invite is active)
   TOKEN=$(python3 -c "import secrets; print('pcp_bootstrap_' + secrets.token_hex(24))")
   TOKEN_HASH=$(echo -n "$TOKEN" | python3 -c "import sys,hashlib; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())")
   UUID=$(python3 -c "import uuid; print(uuid.uuid4())")
   EXPIRES=$(python3 -c "import datetime; print((datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)).isoformat())")
   podman exec paperclip-db psql -U paperclip -d paperclip -c "
   INSERT INTO invites (id, company_id, invite_type, token_hash, allowed_join_types, defaults_payload, expires_at, created_at, updated_at)
   VALUES ('${UUID}', NULL, 'bootstrap_ceo', '${TOKEN_HASH}', '[]', '{\"roles\": [\"instance_admin\"], \"preset\": null}'::jsonb, '${EXPIRES}', NOW(), NOW());
   "
   echo "Invite URL: http://<LAN_IP>:3100/invite/${TOKEN}"

   # 7. Visit the invite URL → UI shows admin signup → auto-grants instance_admin
   ```

   **Note for embedded-PG mode** (dev runner, not Podman): replace `podman volume rm paperclip-pgdata` with `rm -rf ~/.paperclip/instances/default/db`.

7b. **Reset local dev data (embedded PG only):**
   ```bash
   rm -rf ~/.paperclip/instances/default/db
   pnpm dev
   ```

8. **Login fails — no admin user exists (dead bootstrap invite):**
   In `authenticated` mode, there is no default admin. If `bootstrapInviteActive` shows `false` in `/api/health`, the signup window closed without anyone registering. Symptoms: sign-in returns 200 but `get-session` returns 401, everything else returns 403.

   **If running from source (pnpm dev):**
   ```bash
   cd ~/projects/paperclip
   pnpm paperclipai auth bootstrap-ceo --force --expires-hours 24
   # This prints a URL: http://localhost:3100/invite/pcp_bootstrap_<TOKEN>
   # Visit the URL to create the first admin account
   ```

   **If running in Podman prod image (CLI not built):**
   ```bash
   # Generate bootstrap invite via SQL directly against the DB
   TOKEN=$(python3 -c "import secrets; print('pcp_bootstrap_' + secrets.token_hex(24))")
   TOKEN_HASH=$(echo -n "$TOKEN" | python3 -c "import sys,hashlib; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())")
   UUID=$(python3 -c "import uuid; print(uuid.uuid4())")
   podman exec paperclip-db psql -U paperclip -d paperclip -c "
   INSERT INTO invites (id, company_id, invite_type, token_hash, allowed_join_types, defaults_payload, expires_at, created_at, updated_at)
   VALUES ('${UUID}', NULL, 'bootstrap_ceo', '${TOKEN_HASH}', '[]', '{\"roles\": [\"instance_admin\"], \"preset\": null}'::jsonb, (NOW() + interval '24 hours'), NOW(), NOW());
   "
   echo "Invite URL: http://192.168.1.161:3100/invite/$TOKEN"
   ```

   After visiting the invite URL:
   1. Create an account (email + password)
   2. The invite auto-accepts because you signed up via the invite link
   3. You become `instance_admin`

9. **Bootstrap invite SQL must use `bootstrap_ceo` type — the API checks for this EXACT string.**
   The health endpoint checks `eq(invites.inviteType, "bootstrap_ceo")`. If you insert with `invite_type = 'bootstrap'` or any other value, `bootstrapInviteActive` stays false, and the UI shows "Instance setup required" even though the admin account doesn't exist. The UI only shows the "sign up" flow when BOTH conditions are met: `bootstrap_status == "bootstrap_pending"` AND `bootstrapInviteActive == true`.
   ~/projects/paperclip/docker/quadlet/paperclip-db.container
   ~/projects/paperclip/docker/quadlet/paperclip.container
   ```
   Podman is installed (`/usr/bin/podman`) but Docker is not. The docker-compose.yml exists but requires Docker. For persistent hosting without Docker, migrate to `podman quadlet --rootless` or run a manual `podman-compose up -d`. Linger is already enabled (`loginctl enable-linger tphat`), so user-level Podman services survive restart.

---

## Production Deployment via Podman Quadlets

This replaces the `pnpm dev:once` + embedded PostgreSQL dev setup with a proper production build (4-stage Dockerfile) + external PostgreSQL 17, managed by rootless Podman quadlets (systemd-activated).

### Prerequisites

- Podman installed (`/usr/bin/podman`), Docker NOT installed
- Node.js 20+ with pnpm 9+ (for building the image)
- `loginctl enable-linger tphat` (already enabled on nuc-13-pro)
- Podman user socket enabled: `systemctl --user enable --now podman.socket podman.service`

### Step 1: Build the production image

```bash
cd ~/projects/paperclip
podman build --build-arg USER_UID=1000 --build-arg USER_GID=1000 -f Dockerfile -t localhost/paperclip:latest .
```

This is a 4-stage build: base (node + deps) -> deps (pnpm install) -> build (compile server + UI) -> production (copy build + install Claude Code / Codex / OpenCode globally). The final image is ~2.4 GB.

Note: The CLI (`cli/dist/index.js`) is **NOT built** in the production image — only `server/` and `ui/` are built. This means `paperclipai auth bootstrap-ceo` cannot be run inside the container. You must generate admin invites via direct SQL.

### Step 2: Create the host volume directory

```bash
mkdir -p ~/.local/share/paperclip/instances/default/{config,data,logs,secrets}
```

**CRITICAL:** This directory **MUST exist before starting the service**. Podman returns `Error: statfs <path>: no such file or directory` (exit 125) if the host volume path doesn't exist.

### Step 3: Create config.json for external PostgreSQL

The container mounts host `~/.local/share/paperclip/` at `/paperclip/` inside. Create `instances/default/config.json` with `"database": {"mode": "postgres", "connectionString": "postgresql://user:pass@localhost:5432/paperclip"}` — NOT embedded-postgres.

```json
{
  "$meta": {"version": 1, "source": "docker"},
  "database": {
    "mode": "postgres",
    "connectionString": "postgresql://paperclip:<PASSWORD>@localhost:5432/paperclip"
  },
  "server": {
    "deploymentMode": "authenticated",
    "host": "0.0.0.0",
    "port": 3100,
    "serveUi": true
  },
  "auth": {"baseUrlMode": "auto", "disableSignUp": false},
  "logging": {"mode": "file", "logDir": "/paperclip/instances/default/logs"},
  "secrets": {
    "provider": "local_encrypted",
    "localEncrypted": {"keyFilePath": "/paperclip/instances/default/secrets/master.key"}
  }
}
```

### Step 4: Generate secrets

```python
import secrets
db_pass = secrets.token_hex(24)
better_auth_secret = secrets.token_hex(32)
# Save these securely — you'll need them in the env vars and config
```

### Step 5: Install quadlet files

Place three files in `~/.config/containers/systemd/` (the quadlet user generator watches this dir):

**`paperclip.pod`:**
```ini
[Pod]
PodName=paperclip
PublishPort=3100:3100
```

**`paperclip-db.container`:**
```ini
[Unit]
Description=PostgreSQL 17 for Paperclip

[Container]
Image=docker.io/library/postgres:17-alpine
ContainerName=paperclip-db
Pod=paperclip.pod
Volume=paperclip-pgdata:/var/lib/postgresql/data
Environment=POSTGRES_USER=paperclip
Environment=POSTGRES_PASSWORD=<DB_PASS>
Environment=POSTGRES_DB=paperclip
HealthCmd=pg_isready -U paperclip -d paperclip -h localhost || exit 1
HealthInterval=10s
HealthTimeout=5s
HealthRetries=5
HealthStartPeriod=30s

[Service]
Restart=always
RestartSec=5
TimeoutStartSec=90

[Install]
WantedBy=default.target
```

**`paperclip.container`:**
```ini
[Unit]
Description=Paperclip AI Agent Orchestrator
Requires=paperclip-db.service
After=paperclip-db.service

[Container]
Image=localhost/paperclip:latest
ContainerName=paperclip
Pod=paperclip.pod
Volume=%h/.local/share/paperclip:/paperclip:Z
Environment=NODE_ENV=production
Environment=HOST=0.0.0.0
Environment=PORT=3100
Environment=SERVE_UI=true
Environment=PAPERCLIP_HOME=/paperclip
Environment=PAPERCLIP_INSTANCE_ID=default
Environment=PAPERCLIP_DEPLOYMENT_MODE=authenticated
Environment=PAPERCLIP_DEPLOYMENT_EXPOSURE=private
Environment=PAPERCLIP_PUBLIC_URL=http://<LAN_IP>:3100
Environment=DATABASE_URL=postgresql://paperclip:<DB_PASS>@localhost:5432/paperclip
Environment=BETTER_AUTH_SECRET=<BETTER_AUTH_SECRET>

[Service]
Restart=always
RestartSec=5
TimeoutStartSec=120

[Install]
WantedBy=default.target
```

**Key networking detail:** Containers in the same Pod share a network namespace (`localhost` works). So `DATABASE_URL=postgresql://...@localhost:5432/paperclip` from the app container connects directly to the Postgres container on its internal port 5432.

### Step 6: Reload and start

```bash
# Reload triggers the user generator (symlinked to /usr/lib/systemd/user-generators/podman-user-generator -> quadlet)
systemctl --user daemon-reload

# Generated units appear as STATE=generated
systemctl --user list-unit-files '*paperclip*'

# Start the pod first (creates pod + opens ports)
systemctl --user start paperclip-pod.service

# DB starts next (auto-watches)
systemctl --user start paperclip-db.service

# App starts last (depends on DB)
systemctl --user start paperclip.service
```

Generated units have `WantedBy=default.target` in their [Install] section and cannot be explicitly enabled/disabled (`Failed to enable unit: Unit ... is transient or generated`). They auto-start on boot via the quadlet generator.

### Step 7: Generate bootstrap invite via SQL

Since the CLI is not built in the production image, create the admin invite directly:

```bash
# Generate a token and hash (Python)
python3 -c "
import secrets, hashlib, datetime
token = 'pcp_bootstrap_' + secrets.token_hex(24)
token_hash = hashlib.sha256(token.encode()).hexdigest()
expires = (datetime.datetime.now() + datetime.timedelta(hours=24)).isoformat() + 'Z'
print(f'Invite token (SAVE THIS): {token}')
print(f'Expires: {expires}')
# Generate SQL with a UUID
import uuid
uid = str(uuid.uuid4())
print(f'UUID: {uid}')
print(f'Token hash: {token_hash}')
"

# Insert the invite
podman exec paperclip-db psql -U paperclip -d paperclip -c "
INSERT INTO invites (id, company_id, invite_type, token_hash, allowed_join_types, defaults_payload, expires_at, created_at, updated_at)
VALUES ('<UUID>', NULL, 'bootstrap_ceo', '<TOKEN_HASH>', '[]', '{\"roles\": [\"instance_admin\"]}'::jsonb, '<EXPIRES>', NOW(), NOW());
"
```

**CRITICAL: the `invite_type` MUST be `'bootstrap_ceo'` (not `'bootstrap'`).** The health endpoint at `/api/health` explicitly checks `eq(invites.inviteType, "bootstrap_ceo")` — any other value means `bootstrapInviteActive` stays `false` and the UI won't let you sign up.

Then visit `http://<LAN_IP>:3100/` and sign up (the UI detects an active bootstrap invite and auto-accepts it).

### Systemd restart behavior

- **Do NOT run `systemctl --user enable` on quadlet-generated units** — they fail with "transient or generated". The `WantedBy=default.target` in the [Install] section is what makes them auto-start on boot.
- On Debian, `systemctl --user daemon-reload` automatically triggers the quadlet generator (via `/usr/lib/systemd/user-generators/podman-user-generator`). No manual generation step needed.
- When you `systemctl --user restart paperclip-pod`, it cleanly restarts the entire pod (pod + DB + app) — no need to restart each service individually.
- `loginctl enable-linger tphat` is required for user-level systemd services to survive logout (already enabled on nuc-13-pro).

### Config notes

- The `config.json` inside the mounted volume (`~/.local/share/paperclip/instances/default/config.json`) must have `"database": {"mode": "postgres"}` matching the external PostgreSQL setup.
- `DATABASE_URL` and `BETTER_AUTH_SECRET` can be set as container `Environment=` vars and take precedence over `config.json`.
- `PAPERCLIP_PUBLIC_URL` must match your LAN IP (e.g., `http://192.168.1.161:3100`) for authenticated mode auth callbacks to work correctly — otherwise sign-in returns 200 but sessions fail with 401.
- The Dockerfile's 4-stage build does NOT compile `cli/dist/index.js` — only `server/` and `ui/` are built. This means `paperclipai auth bootstrap-ceo` CLI commands **cannot be run inside the production container**. Generate invites via direct SQL only.

### Step 8: Rebuild image (when code changes)

```bash
# Kill services
systemctl --user stop paperclip.service

# Rebuild
cd ~/projects/paperclip
podman build --build-arg USER_UID=1000 --build-arg USER_GID=1000 -f Dockerfile -t localhost/paperclip:latest .

# Restart
systemctl --user start paperclip.service
```

### Management Commands

```bash
# Check status
systemctl --user status paperclip-pod.service
systemctl --user status paperclip-db.service  
systemctl --user status paperclip.service

# View logs
journalctl --user -u paperclip.service -f
podman logs -f paperclip

# Restart everything
systemctl --user restart paperclip.service

# Stop everything
systemctl --user stop paperclip.service
systemctl --user stop paperclip-db.service
systemctl --user stop paperclip-pod.service

# Inspect containers
podman ps
podman pod ls

# Health check
curl http://localhost:3100/api/health
```

### Troubleshooting

- **Exit code 125:** Host volume path (`~/.local/share/paperclip`) doesn't exist — create it with `mkdir -p ~/.local/share/paperclip` BEFORE starting the service
- **DB connection refused:** Ensure `DATABASE_URL` uses `localhost:5432` (Pod shared networking)
- **401 on all endpoints:** No admin user exists — create bootstrap invite via SQL (Step 7)
- **503 on health:** Config changes not applied — edit config.json in the host volume, then `systemctl --user restart paperclip.service`
- **"Instance setup required" with active invite:** You must visit the actual invite URL, not just sign up normally. The invite URL auto-accepts the bootstrap invite as part of the signup flow. Visit `http://<IP>:3100/invite/pcp_bootstrap_<TOKEN>` to complete setup.

- **"Instance admin required" when bootstrap is "ready":** An admin exists but your current user session lacks the `instance_admin` role. Diagnose:
  ```bash
  # List all users
  podman exec paperclip-db psql -U paperclip -d paperclip -c "SELECT id, email, name FROM public.user;"

  # Check who has admin roles
  podman exec paperclip-db psql -U paperclip -d paperclip -c "SELECT u.email, r.role FROM public.user u JOIN public.instance_user_roles r ON u.id = r.user_id;"

  # Grant instance_admin to a user (replace USER_ID)
  podman exec paperclip-db psql -U paperclip -d paperclip -c "INSERT INTO public.instance_user_roles (id, user_id, role, created_at, updated_at) VALUES (gen_random_uuid(), '<USER_ID>', 'instance_admin', NOW(), NOW())"
  ```
  Note: the table is `user` (singular), not `users`.

### Company Wizard Plugin

Install via Paperclip UI: Settings > Plugins > Install Plugin
```bash
@yesterday-ai/paperclip-plugin-company-wizard
```
Or globally: `pnpm add -g @yesterday-ai/paperclip-plugin-company-wizard`

## Hermes Adapter Integration

Paperclip has a community `hermes_local` adapter (`@henkey/hermes-paperclip-adapter`) that runs Hermes Agent as a managed employee. The adapter expects the `hermes` CLI and Python available inside the container.

### Prerequisites
- The paperclip Dockerfile includes `python3` but NOT Hermes Agent
- Your host has Hermes at `~/.hermes/` with `~/.hermes/.env` credentials

### Option A: Install Hermes inside the container (recommended)

**1. Modify the Dockerfile** — add Hermes installation before the final COPY:
```dockerfile
RUN pip install hermes-agent \
  && hermes --version
```

Or simpler — add an env var that points to a host-mounted hermes:

**2. Rebuild image with Hermes:**
```bash
cd ~/projects/paperclip
```

Add these lines after `FROM base AS production` stage:
```dockerfile
RUN pip install hermes-agent
ENV HERMES_HOME=/paperclip/.hermes
```

**3. Mount host config into container** — update `paperclip.container`:
```ini
# Add to the [Container] section:
Volume=%h/.hermes:/paperclip/.hermes:ro
```

**4. Rebuild and restart:**
```bash
podman build --build-arg USER_UID=1000 --build-arg USER_GID=1000 -f Dockerfile -t localhost/paperclip:latest .
systemctl --user restart paperclip-pod.service
```

### Option B: Install from inside the container

```bash
podman exec paperclip pip install hermes-agent
podman exec -e HERMES_HOME=/paperclip/.hermes paperclip hermes --version
```

This installs into the container's pip — survives container restarts (overlayfs) but NOT image rebuilds.

### Option C: Bind-mount host binary

Mount the host `hermes` CLI + `~/.hermes/` as additional volumes:
```ini
# In paperclip.container:
Volume=%h/.hermes:/root/.hermes:ro
Volume=/usr/local/bin/hermes:/usr/local/bin/hermes:ro
# Plus Python runtime
Volume=/usr/bin/python3:/usr/bin/python3:ro
# + all Python stdlib libs (complex — not recommended)
```
This approach is fragile due to Python library dependencies. **Option A is preferred.**

### Installing the adapter plugin

The adapter lives at `~/.paperclip/adapter-plugins.json` where `~` is `/paperclip` inside the container, resolving to `/paperclip/.paperclip/`. On the host, this is `~/.local/share/paperclip/.paperclip/`.

```bash
# 1. Create plugins dir (on the host, inside your volume)
mkdir -p ~/.local/share/paperclip/.paperclip/adapter-plugins

# 2. Install the npm package
cd ~/.local/share/paperclip/.paperclip/adapter-plugins
pnpm install @henkey/hermes-paperclip-adapter

# 3. Write the store config
cat > ~/.local/share/paperclip/.paperclip/adapter-plugins.json << 'EOF'
[{
  "packageName": "@henkey/hermes-paperclip-adapter",
  "version": "0.4.2",
  "type": "hermes_local",
  "installedAt": "2026-04-06T15:20:00Z",
  "disabled": false
}]
EOF

# 4. Restart Paperclip to load the adapter
systemctl --user restart paperclip.service
```

Verify in logs:
```
Loaded external adapters from plugin store {"count":1,"adapters":["hermes_local"]}
External adapter "hermes_local" overrides built-in adapter
```

Then go to **Board → Adapter Manager** in the Paperclip UI to configure a Hermes employee.

⚠️ **Gotcha:** Without Hermes CLI inside the container, the adapter installs fine but fails at runtime — the container can't find the `hermes` binary. Install Hermes (Option A/B above) before trying to run agents.

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