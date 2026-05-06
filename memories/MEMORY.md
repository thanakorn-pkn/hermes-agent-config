Obsidian vault path: /data/syncthing/obsidian-second-brain (called "second-brain"). Use this for documenting knowledge, references, and project docs. Set OBSIDIAN_VAULT_PATH to this path.
§
User packages installed via pnpm, not npm. User installs Python packages via uv, not pip.
§
RULE: Never read .env files or credential files with read_file, cat, grep, or any inspection tool. Credentials injected into the runtime environment are available for tool execution — use them, don't peek at the files. Only ask the user if a genuinely new credential is needed that isn't already available.
§
User's homelab-infra repo is at ~/projects/homelab-infra; run Ansible from hosts/ with uv run. Inventory is in hosts/inventory/ and firewall role in hosts/roles/firewall/.
§
Homelab: nuc-13-pro has LAN IP 192.168.1.161. Uses k3s with Traefik reverse proxy. UFW firewall managed via Ansible homelab-infra repo. Paperclip AI installed from source at /home/tphat/projects/paperclip, instance at ~/.paperclip/instances/default/.
§
Paperclip prefers Postgres 17 quadlet on 5432 and app via pnpm dev:once.
§
For Paperclip `pnpm dev:once` under systemd, set `Environment=npm_config_tailscale_auth=true`; otherwise it stays in `local_trusted` mode and rejects `0.0.0.0` binding.
§
Mission Control is Hermes-first, solo-user, homelab-only, low-maintenance; OpenClaw is on hold. tmux-wrapped `claude -p` can hide output, so foreground JSON + resume is preferred.
§
The vault’s MOC files live in `30_resources/` and use the `*-moc.md` naming suffix (for example, `homelab-moc.md`); `INDEX.md` is the root registry for MOCs.
§
Mission Control backend origin is localhost:8000.
§
Codex CLI quota can be checked in the interactive TUI with `/status`; it shows 5h limit, weekly limit, reset times, and the usage page URL `https://chatgpt.com/codex/settings/usage`. On this host `codex login status` reports ChatGPT login.
§
Codex quota is available from ~/.codex/session logs.