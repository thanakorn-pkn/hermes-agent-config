# Hermes Dashboard LAN-Only Startup Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Make `hermes dashboard` survive reboot, start only after the Hermes gateway is up, and expose it on the LAN only through `hermes.bp-house.com`.

**Architecture:**
Manage Hermes gateway and Hermes dashboard as **Ansible-owned systemd services** on the host, not as ad-hoc local files. Use system scope so the services start at boot without relying on user login or lingering. Run both services as the existing `tphat` user so they keep the same Hermes config/state directory they use today. The gateway stays the primary long-lived process; the dashboard is a dependent service with explicit ordering, restart policy, sandboxing, and readiness checks. For network access, publish the dashboard through the existing homelab LAN DNS / Traefik pattern and route Traefik to the host LAN IP; keep the hostname inside the home network and do not publish it via Cloudflared.

**Tech Stack:**
- Hermes CLI / dashboard / gateway
- Ansible in `~/projects/homelab-infra/hosts`
- systemd system services managed by Ansible
- run-as user: `tphat`
- Homelab GitOps repo (`~/projects/homelab-infra`)
- Traefik + internal DNS (Pi-hole/Unbound)
- UFW / host firewall rules

---

## Proposed approach

### Recommended design
1. **Gateway stays authoritative**
   - Ensure `hermes gateway` is deployed as a system service and enabled at boot.
   - Treat the gateway as the prerequisite for dashboard startup.

2. **Dashboard gets its own managed system service**
   - Create a `hermes-dashboard.service` system unit, with the file owned by Ansible.
   - Run it as `tphat` (`User=tphat`, `Group=tphat`) so it reads the same Hermes home/config/state.
   - Make it restart automatically after failure or host reboot.
   - Use `After=hermes-gateway.service network-online.target` and default to `Requires=hermes-gateway.service` unless Task 0 explicitly chooses stricter follow semantics.
   - Bind the dashboard to the chosen backend address/port, and keep the exposed surface as small as practical.

3. **LAN-only hostname exposure**
   - Add an internal DNS override for `hermes.bp-house.com`.
   - Route that hostname through the existing LAN ingress/proxy path.
   - Do **not** add Cloudflared/public DNS exposure for this hostname.

4. **Security hardening**
   - Keep the dashboard off broad exposure if possible.
   - If the backend must be reachable by a proxy, allow only the Traefik/k3s source range or the specific proxy node IPs.
   - Apply systemd sandboxing defaults in the unit template, not just network firewall rules.

5. **Verification**
   - Verify both services survive reboot.
   - Confirm gateway starts before dashboard.
   - Confirm DNS resolves only on LAN.
   - Confirm HTTPS reaches the dashboard at `https://hermes.bp-house.com` from LAN clients.

---

## Step-by-step plan

### Task 0: Decide the host exposure topology, TLS story, and lifecycle semantics

**Objective:** Resolve the design choices that determine the rest of the implementation: how Traefik reaches the host dashboard, how HTTPS is terminated, and what should happen when the gateway dies.

**Files likely involved:**
- `~/projects/homelab-infra/docs/operations.md`
- `~/projects/homelab-infra/docs/traefik.md`
- `~/projects/homelab-infra/k8s/flux/homelab/infrastructure/traefik.yaml`
- `~/projects/homelab-infra/k8s/infrastructure/controllers/traefik/values.yaml`

**Decisions to make:**
- Choose the backend bridge:
  - Traefik/cluster reaches the host on its LAN IP, or
  - a host-local proxy sits in front of the dashboard.
- Confirm the existing Traefik cert path covers `hermes.bp-house.com` by checking the SANs on the active certificate.
- Decide whether dashboard lifecycle should strictly follow the gateway (`BindsTo=`) or merely require it (`Requires=`). Default recommendation: `Requires=`.
- Decide whether the gateway should expose a health endpoint or whether dashboard readiness should be a pre-start loop.

**Acceptance criteria:**
- One explicit backend topology is selected.
- One explicit TLS termination story is selected.
- One explicit lifecycle/readiness strategy is selected.
- Later tasks can reference those choices without ambiguity.

---

### Task 1: Make the deployment model Ansible-owned

**Objective:** Move gateway/dashboard service management into the homelab-infra repo so the service definitions are versioned and reproducible.

**Files likely involved:**
- `~/projects/homelab-infra/hosts/inventory/host_vars/nuc-13-pro.yml`
- `~/projects/homelab-infra/hosts/roles/<new-or-existing-service-role>/tasks/*.yml`
- `~/projects/homelab-infra/hosts/roles/<new-or-existing-service-role>/templates/*.service.j2`
- `~/projects/homelab-infra/hosts/playbooks/*.yml`

**Plan:**
- Prefer an Ansible role to manage the service units rather than hand-editing files on the host.
- Keep the unit files in templates.
- Keep host-specific settings in inventory vars.
- Ensure the role is idempotent and can remove/replace any pre-existing manual unit cleanly.

**Acceptance criteria:**
- Re-running Ansible does not duplicate or corrupt service files.
- The service definition lives in git and can be reviewed like any other infra change.

---

### Task 2: Create or extend the systemd service management role

**Objective:** Define the exact service units for gateway and dashboard under Ansible control.

**Files likely involved:**
- `~/projects/homelab-infra/hosts/roles/systemd-services/tasks/main.yml` or similar
- `~/projects/homelab-infra/hosts/roles/systemd-services/templates/hermes-gateway.service.j2`
- `~/projects/homelab-infra/hosts/roles/systemd-services/templates/hermes-dashboard.service.j2`
- `~/projects/homelab-infra/hosts/roles/systemd-services/defaults/main.yml`
- `~/projects/homelab-infra/hosts/inventory/host_vars/nuc-13-pro.yml`

**Plan:**
- Create a dedicated role if one does not exist, or extend the most appropriate service role.
- Render both service units from templates.
- Explicitly set:
  - `User=tphat`
  - `Group=tphat`
  - `WorkingDirectory=/home/tphat`
  - `Environment=HOME=/home/tphat`
  - `Environment=HERMES_HOME=/home/tphat/.hermes`
  - `Environment=XDG_CONFIG_HOME=/home/tphat/.config`
  - `Environment=XDG_STATE_HOME=/home/tphat/.local/state`
- Add unit sandboxing defaults:
  - `NoNewPrivileges=true`
  - `PrivateTmp=true`
  - `ProtectSystem=` as appropriate
  - `ProtectHome=read-only` with explicit `ReadWritePaths=` for the Hermes state/config dirs
  - `RestrictAddressFamilies=` as appropriate
- Ensure `hermes-dashboard.service` includes the chosen ordering/lifecycle semantics from Task 0.
- Add explicit readiness handling from Task 0:
  - either a small pre-start health loop,
  - or a separate oneshot readiness unit,
  - or a gateway `Type=notify` path if the gateway supports it.
- If the dashboard must wait on Hermes readiness, do not leave that as an optional note — implement one strategy.

**Acceptance criteria:**
- The units are generated from Ansible templates.
- The dashboard restarts automatically and comes back after reboot.
- The unit file is complete enough that no manual post-editing is required.
- The unit does not run as root.

---

### Task 3: Remove or supersede any prior manual/user-scope Hermes services

**Objective:** Avoid two competing startup paths for the same dashboard/gateway pair.

**Files likely involved:**
- `~/projects/homelab-infra/hosts/roles/systemd-services/tasks/main.yml`
- `~/projects/homelab-infra/hosts/roles/systemd-services/templates/*.service.j2`
- existing host-level service locations if present

**Plan:**
- Disable and remove any old manually installed `hermes-dashboard.service` or user-scope units that would conflict with the new system service.
- Ensure the Ansible role cleans up stale enablement bits before enabling the managed unit.
- Document the migration path so the old launch method is not left behind accidentally.
- Define the rollback path: stop/disable the new unit and re-enable the prior launch method if the migration needs to be reversed.

**Acceptance criteria:**
- Only one dashboard service path remains active after the migration.
- No stale manual unit can shadow the Ansible-managed version.
- Rollback is documented and reversible.

---

### Task 4: Wire the services into bootstrap / site playbooks

**Objective:** Make the dashboard and gateway service deployment part of normal homelab bootstrap.

**Files likely involved:**
- `~/projects/homelab-infra/hosts/playbooks/bootstrap.yml`
- `~/projects/homelab-infra/hosts/playbooks/containers.yml` or a dedicated service playbook
- `~/projects/homelab-infra/hosts/inventory/host_vars/nuc-13-pro.yml`

**Plan:**
- Include the role in the appropriate playbook.
- Run it only for the host(s) that should host Hermes.
- Make sure the playbook enables and starts the services after file deployment.
- Add a `daemon-reload` handler.
- Define a clear tag name, such as `hermes`, and use it consistently.

**Acceptance criteria:**
- A single Ansible run can deploy/update the service unit and start it.
- Host boot order remains correct after reboots.

---

### Task 5: Expose `hermes.bp-house.com` only on LAN

**Objective:** Publish the dashboard behind your LAN DNS / proxy path and keep it private.

**Files likely involved in homelab repo:**
- `~/projects/homelab-infra/hosts/inventory/host_vars/nuc-13-pro.yml` or the relevant DNS host vars file
- `~/projects/homelab-infra/k8s/flux/homelab/...` or a new app manifest for the reverse proxy target
- `~/projects/homelab-infra/docs/operations.md` if you want the runbook updated

**Plan:**
- Add a LAN DNS record for `hermes.bp-house.com`.
- Point it at the chosen internal backend path from Task 0.
- Add an internal proxy route that forwards to the host dashboard endpoint.
- Keep the hostname out of Cloudflared/public DNS.
- If the existing Traefik wildcard cert already covers this hostname, reuse it. If it does not, add a cert task immediately rather than assuming it exists.

**Acceptance criteria:**
- `dig hermes.bp-house.com` from LAN returns the internal address.
- The hostname is not published via public DNS or Cloudflared.
- HTTPS works from LAN clients without exposing the dashboard publicly.

---

### Task 6: Harden access

**Objective:** Prevent accidental wide-network exposure.

**Files likely involved:**
- UFW / host firewall config in `~/projects/homelab-infra/hosts/inventory/host_vars/nuc-13-pro.yml`
- Traefik middleware / ingress values if a proxy route is used

**Plan:**
- Do not bind the dashboard to `0.0.0.0` by default.
- Bind to the chosen host LAN IP or localhost+proxy path from Task 0.
- Allow only the Traefik/k3s source range or the specific proxy node IPs to reach the backend port if it is exposed on the host.
- Treat UFW as defense-in-depth rather than the only control.
- If Traefik is used, consider an IP allow-list middleware for extra defense in depth.
- Keep journald as the source of service logs and set the unit to log to journal explicitly.

**Acceptance criteria:**
- The dashboard backend is not reachable from outside LAN.
- The hostname works normally from LAN clients.
- The unit is hardened beyond just firewall rules.

---

### Task 7: Verify restart behavior and LAN access

**Objective:** Prove the setup is stable and discoverable.

**Verification commands:**

```bash
cd ~/projects/homelab-infra/hosts
uv run ansible-playbook playbooks/bootstrap.yml -i inventory/hosts.ini --tags hermes --limit nuc-13-pro -c local
```

```bash
systemctl status hermes-gateway hermes-dashboard
journalctl -u hermes-dashboard -f
systemctl list-dependencies hermes-dashboard
systemd-analyze verify /etc/systemd/system/hermes-gateway.service /etc/systemd/system/hermes-dashboard.service
```

```bash
dig hermes.bp-house.com
curl -I https://hermes.bp-house.com
```

```bash
# Optional direct bind / firewall check if needed
ss -ltnp | grep 9119
```

**Failure-mode checks:**
- Reboot the host and confirm both services start automatically.
- Stop the gateway service and confirm the dashboard follows the intended lifecycle behavior.
- From a non-LAN host, confirm the hostname is not reachable.

**Acceptance criteria:**
- Both services come back after reboot.
- Dashboard starts only after gateway.
- LAN clients can reach `https://hermes.bp-house.com`.
- No public exposure path exists for this hostname.

---

## Risks and tradeoffs

- **Startup ordering vs readiness:** `After=` guarantees order, not readiness. The plan now requires a concrete readiness strategy rather than leaving it optional.
- **Security vs simplicity:** Binding the dashboard broadly is simpler for proxying but riskier. Prefer the narrowest backend exposure the chosen topology allows.
- **Traefik integration complexity:** If the dashboard runs outside Kubernetes, you may need an external service/endpoints pattern or a small host proxy.
- **TLS story must be explicit:** If internal HTTPS is required, specify the cert source now instead of assuming it exists.
- **VCS-managed services add upfront work:** The Ansible role takes a little more setup, but it is easier to audit, reproduce, and roll back than local custom files.

---

## Open questions

1. Do you want the dashboard exposed through the existing Traefik stack, or would a small host-local reverse proxy be acceptable?
2. Should the dashboard backend stay as narrow as possible, or is a LAN bind with firewall controls acceptable?
3. Do you want HTTPS termination at Traefik, or is HTTP on LAN acceptable for this one service?
4. Do you want the gateway/dashboard services managed by a new dedicated Ansible role, or folded into an existing host/service role?
5. What exact source IPs or CIDRs should be allowed to reach the host dashboard backend?

---

## Recommendation

Use the following default design unless you prefer otherwise:
- `hermes gateway` and `hermes dashboard` are both managed by **Ansible**, not by hand-edited host files
- services are deployed as **systemd system units** so they survive reboot without user login
- run as the existing `tphat` user so Hermes keeps its current config/state
- default to `Requires=` + `After=` and only use stricter lifecycle binding if Task 0 explicitly chooses it
- gateway starts first; dashboard has a concrete readiness check
- `hermes.bp-house.com` is published only via your LAN DNS/proxy stack
- no public Cloudflared route for this hostname
- firewall remains LAN-only and the service is sandboxed with systemd hardening

This gives you:
- reboot persistence
- correct service ordering
- least-privilege security
- VCS-managed infrastructure
- a stable LAN hostname that fits the rest of your homelab
