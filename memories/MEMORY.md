Obsidian vault path: /srv/syncthing/obsidian-second-brain (called "second-brain"). Use this for documenting knowledge, references, and project docs. Set OBSIDIAN_VAULT_PATH to this path.
§
User packages installed via pnpm, not npm. User installs Python packages via uv, not pip.
§
RULE: Never read .env files or credential files with read_file, cat, grep, or any inspection tool. Credentials injected into the runtime environment are available for tool execution — use them, don't peek at the files. Only ask the user if a genuinely new credential is needed that isn't already available.
§
User's homelab-infra repo is at ~/projects/homelab-infra. Ansible commands must be run from the hosts/ subdirectory using uv run (e.g., cd ~/projects/homelab-infra/hosts && uv run ansible-playbook ...). Inventory is at hosts/inventory/. Firewall role is at hosts/roles/firewall/.
§
Homelab: nuc-13-pro has LAN IP 192.168.1.161. Uses k3s with Traefik reverse proxy. UFW firewall managed via Ansible homelab-infra repo. Paperclip AI installed from source at /home/tphat/projects/paperclip, instance at ~/.paperclip/instances/default/.
§
Paperclip preferred architecture for homelab: Postgres 17 as standalone Podman quadlet container (port 5432 published), Paperclip app runs directly on host via systemd service using `pnpm dev:once`. This gives the app direct access to host CLIs (Claude Code, Codex, Gemini, Hermes) without bind-mount complexity.
§
When running `pnpm dev:once` in a systemd service (non-interactive), you MUST set `Environment=npm_config_tailscale_auth=true` — otherwise Paperclip defaults to `local_trusted` mode and refuses `0.0.0.0` binding with error "local_trusted mode requires loopback host binding". This env var triggers `authenticated` mode in dev-runner.ts.