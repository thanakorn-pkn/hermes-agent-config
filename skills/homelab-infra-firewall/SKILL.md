---
name: homelab-infra-firewall
description: Manage UFW firewall rules in the homelab-infra Ansible repo. Covers the project structure, playbook patterns, and firewall role conventions.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [homelab, firewall, ansible, ufw, networking, k3s]
    related_skills: []
---

# Homelab Infrastructure Firewall Management

The homelab-infra repo at `~/projects/homelab-infra` manages firewall rules via an Ansible `firewall` role targeting nuc-13-pro and rpi-5 hosts.

## Repo Structure

```
homelab-infra/
├── hosts/
│   ├── inventory/
│   │   ├── hosts.ini           # Host groups (nuc-13-pro, rpi-5)
│   │   └── host_vars/
│   │       ├── nuc-13-pro.yml  # Per-host vars including firewall_rules
│   │       └── rpi-5.yml
│   ├── roles/
│   │   └── firewall/
│   │       ├── tasks/
│   │       │   ├── main.yml      # Imports validate, install, ufw
│   │       │   ├── ufw.yml       # community.general.ufw tasks
│   │       │   ├── install.yml
│   │       │   └── validate.yml
│   │       ├── defaults/main.yml
│   │       └── meta/
│   ├── playbooks/
│   │   ├── bootstrap.yml       # Includes firewall role
│   │   ├── containers.yml
│   │   └── kubernetes.yml
│   └── requirements.yml        # Ansible collections (community.general, etc.)
└── Justfile                    # Task runner with ansible-* recipes
```

## Adding a Firewall Rule

1. Edit the appropriate host vars file:
   `hosts/inventory/host_vars/<hostname>.yml`

2. Add to `firewall_rules` (for direct incoming access):
```yaml
  # Service Name - description
  - rule: allow
    port: <port_number>
    proto: tcp
    from_ip: "{{ network.cidr }}"
    comment: "Service Name from LAN"
  - rule: allow
    port: <port_number>
    proto: tcp
    from_ip: "{{ network.ula_cidr }}"
    comment: "Service Name from LAN (ULA)"
```

3. For Tailscale route rules, add to `firewall_route_rules`:
```yaml
  - rule: allow
    interface_in: tailscale0
    interface_out: "{{ podman_network_interface }}"
    port: <port_number>
    proto: tcp
    comment: "Tailscale to container Service Name"
```

## Running Ansible

Always run from the `hosts/` subdirectory, using `uv run`:

```bash
cd ~/projects/homelab-infra/hosts

# Install collections (first time or when requirements.yml changes)
uv run ansible-galaxy collection install -r requirements.yml

# Run firewall role on specific host
uv run ansible-playbook playbooks/bootstrap.yml -i inventory/hosts.ini \
  --tags firewall --limit nuc-13-pro -c local

# Or via Justfile
cd ~/projects/homelab-infra
just ansible-bootstrap --tags firewall --limit nuc-13-pro -c local
```

## Verifying

```bash
# Check UFW status on target host
sudo ufw status numbered | grep <port>
```

## Network Variables

- `{{ network.cidr }}` → `192.168.1.0/24` (standard IPv4 LAN)
- `{{ network.ula_cidr }}` → `fdca:fe00:beef::/64` (IPv6 ULA)
- `{{ podman_network_interface }}` → `podman0` (container network bridge)
- `tailscale0` → Tailscale VPN interface

## Pitfalls

1. Always add BOTH IPv4 and IPv6 rules (LAN + ULA) — don't skip one
2. Route rules (firewall_route_rules) are for forwarded traffic, rule rules (firewall_rules) for direct input
3. `-c local` flag needed when running on the target host itself
4. Install collections before running if requirements.yml was updated
5. Run from `hosts/` subdirectory, not repo root