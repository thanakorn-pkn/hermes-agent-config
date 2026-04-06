Obsidian vault path: /srv/syncthing/obsidian-second-brain (called "second-brain"). Use this for documenting knowledge, references, and project docs. Set OBSIDIAN_VAULT_PATH to this path.
§
User packages installed via pnpm, not npm. User installs Python packages via uv, not pip.
§
RULE: Never read .env files or credential files with read_file, cat, grep, or any inspection tool. Credentials injected into the runtime environment are available for tool execution — use them, don't peek at the files. Only ask the user if a genuinely new credential is needed that isn't already available.
§
User's homelab-infra repo is at ~/projects/homelab-infra. Ansible commands must be run from the hosts/ subdirectory using uv run (e.g., cd ~/projects/homelab-infra/hosts && uv run ansible-playbook ...). Inventory is at hosts/inventory/. Firewall role is at hosts/roles/firewall/.
§
Homelab: nuc-13-pro has LAN IP 192.168.1.161. Uses k3s with Traefik reverse proxy. UFW firewall managed via Ansible homelab-infra repo. Paperclip AI installed from source at /home/tphat/projects/paperclip, instance at ~/.paperclip/instances/default/.