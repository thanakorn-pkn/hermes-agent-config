---
name: multica-selfhost-podman
description: Deploy Multica self-hosted on a Podman-only homelab host, including firewall, PAT-based CLI auth, and daemon registration for Claude/Codex/Hermes/Gemini.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [multica, podman, self-host, homelab, firewall, claude-code, codex, gemini, hermes]
    related_skills: [homelab-infra-firewall]
---

# Multica self-host on Podman homelab host

Use when Docker is unavailable but Podman + podman-compose are installed, and the goal is to run Multica locally on a homelab machine with LAN access.

## Host-specific pitfalls discovered
- Official docs assume Docker Compose; Podman works, but `pgvector/pgvector:pg17` must be fully qualified as `docker.io/pgvector/pgvector:pg17` or Podman short-name resolution fails.
- On this host, port `3000` may already belong to an existing Mission Control service; do not reuse it during Multica setup if the assignment is to preserve Mission Control.
- The default Postgres host port `5432` can already be occupied; `5434` was a working workaround for the Multica stack on this machine.
- On this host, non-interactive PATH misses `/data/pnpm`, so `codex` and `gemini` are not auto-discovered unless you set explicit env vars when starting the daemon.
- If you verify through `127.0.0.1`, add `http://127.0.0.1:<frontend_port>` to `CORS_ALLOWED_ORIGINS`; otherwise backend WebSocket origin checks can reject local browser verification.
- `multica login --token` expects a PAT starting with `mul_`, not the JWT returned by `/api/cli-token`.

## Working deployment recipe
1. Clone repo to `~/projects/multica`.
2. Patch `docker-compose.selfhost.yml`:
   - change `image: pgvector/pgvector:pg17`
   - to `image: docker.io/pgvector/pgvector:pg17`
3. Create `.env` from `.env.example` without reading secrets back out.
4. Set ports away from any existing services. Example known-good config on `nuc-13-pro`:
   - `FRONTEND_PORT=3001`
   - `PORT=8081`
   - `POSTGRES_PORT=5434`
   - `APP_ENV=development`
   - `FRONTEND_ORIGIN=http://192.168.1.161:3001`
   - `MULTICA_APP_URL=http://192.168.1.161:3001`
   - `MULTICA_SERVER_URL=ws://localhost:8081/ws`
   - `DATABASE_URL=postgres://multica:multica@localhost:5434/multica?sslmode=disable`
   - `CORS_ALLOWED_ORIGINS=http://localhost:3001,http://127.0.0.1:3001,http://192.168.1.161:3001`
5. Launch with:
   - `cd ~/projects/multica && podman-compose -f docker-compose.selfhost.yml up -d`
6. Verify:
   - `curl http://127.0.0.1:8081/health`
   - `curl -I http://127.0.0.1:3001`
   - `podman ps | grep multica`

## Firewall on Bank's homelab
Use the `homelab-infra-firewall` skill and update `~/projects/homelab-infra/hosts/inventory/host_vars/nuc-13-pro.yml` with both IPv4 and ULA rules for the chosen frontend/backend ports, then apply:

```bash
cd ~/projects/homelab-infra/hosts
uv run ansible-playbook playbooks/bootstrap.yml -i inventory/hosts.ini --tags firewall --limit nuc-13-pro -c local
```

## Browser auth + PAT flow for headless CLI setup
When no desktop browser is available on the server:
1. Use Hermes browser tools to log into the web app on the chosen frontend URL.
2. In `APP_ENV=development`, request a code and read the verification code from backend logs.
3. Submit the code in the browser.
4. Mint a PAT from the authenticated browser session by POSTing to `/api/tokens` with the `multica_csrf` cookie echoed in `X-CSRF-Token`.
   - Body shape:
     - `{"name":"nuc-13-pro-daemon","expires_in_days":90}`
5. Feed the returned `mul_...` token to:
   - `multica login --token`

## CLI installation on Linux without Homebrew
Use GitHub Releases:

```bash
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
[ "$ARCH" = "x86_64" ] && ARCH=amd64
LATEST=$(curl -sI https://github.com/multica-ai/multica/releases/latest | tr -d '\r' | awk '/^location:/ {sub(/.*tag\//, "", $2); print $2}' | tail -n1)
VERSION="${LATEST#v}"
URL="https://github.com/multica-ai/multica/releases/download/${LATEST}/multica-cli-${VERSION}-${OS}-${ARCH}.tar.gz"
curl -fsSL "$URL" -o /tmp/multica.tar.gz
tar -xzf /tmp/multica.tar.gz -C /tmp multica
install -m 0755 /tmp/multica ~/.local/bin/multica
multica version
```

## Start daemon with explicit runtime paths
On hosts where `codex` / `gemini` are only on `/data/pnpm`, set explicit env vars before start:

```bash
export PATH=/home/tphat/.local/bin:$PATH
export MULTICA_CLAUDE_PATH=/home/tphat/.local/bin/claude
export MULTICA_HERMES_PATH=/home/tphat/.local/bin/hermes
export MULTICA_CODEX_PATH=/data/pnpm/codex
export MULTICA_GEMINI_PATH=/data/pnpm/gemini
multica daemon start
multica daemon status
multica runtime list
```

Expected detection on this host:
- `claude`
- `codex`
- `hermes`
- `gemini`

## Verification checklist
- `multica auth status` shows authenticated user and local server URL.
- `multica daemon status` shows `running`.
- `multica runtime list` shows runtimes online.
- Browser `GET /api/runtimes` with `X-Workspace-Slug` returns registered runtime entries.

## Rollback / recovery workflow when the goal is to preserve an existing app
If the user expected another service (for example Mission Control) to remain on its original port, stop and verify before reinstalling Multica:
1. Stop the Multica daemon and self-host containers.
2. Confirm which process owns the target port(s) before touching them.
3. Restore any repo edits from the previous setup.
4. Reinstall Multica only on alternate ports that do not displace the existing app.
5. Verify the original app is still reachable and only then validate Multica.
