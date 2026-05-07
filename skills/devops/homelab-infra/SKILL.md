---
name: homelab-infra
description: Operate the homelab-infra Ansible repository through its `just` entrypoints, with Ansible runs loading 1Password-backed credentials from the repo `.env` via the wrapper. Use when inspecting, running, automating, or modifying homelab-infra tasks.
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [devops, homelab, ansible, just, 1password, gitops, k8s, firewall]
    category: devops
---

# homelab-infra

## Overview

Use this skill for the `~/projects/homelab-infra` Ansible repo and anything that depends on it.

This is the umbrella skill for the whole homelab infrastructure workflow, including:

- `just`-driven Ansible execution
- firewall/UFW management
- Kubernetes/GitOps operations
- repo-specific host inventory, role, and playbook conventions
- safe verification of live infra changes

Supporting repo notes and session-specific conventions live in:
- `references/homelab-infra-workflow.md`
- `references/hermes-dashboard-routing.md`
- `references/hermes-built-in-dashboard-proxy.md`
- `references/project-monitoring-cron.md`

The Hermes routing references capture two distinct failure modes from the `hermes.bp-house.com` work:
- a stale Traefik dashboard alias hijacking the hostname
- confusing the built-in Hermes dashboard with the Mission Control app on `:3000`

## When to Use

Use this skill when the user asks to:

- run or inspect a homelab-infra playbook or role
- change firewall rules, host vars, or service exposure
- deploy or reconcile Kubernetes workloads through the repo’s GitOps flow
- debug why a homelab-infra task failed
- understand the repo’s operational conventions before making changes

Do not use it for unrelated ad hoc shell tasks outside the repo’s scope.

## Core conventions

- Use the repo's `just` commands as the entrypoint for Ansible and related automation.
- Do not improvise direct Ansible invocation if a `just` target exists.
- Assume the `just` wrapper loads required 1Password credentials from the repo `.env` during execution.
- Do not read `.env` or credential files directly.
- Firewall/UFW work is part of this skill’s Ansible scope.
- Kubernetes work is GitOps-managed in this repo; prefer declarative changes and the repo’s GitOps flow over ad hoc cluster mutations.
- For internal dashboards exposed through the cluster, verify the full chain: hostname -> ingress -> service -> backend process. Do not assume a healthy HTTP 200 from the hostname means the correct app is being served.
- If the repo instructions are unclear, pause and report that uncertainty.

## Typical workflow

1. Inspect the repo guidance first:
   - `AGENTS.md`
   - `justfile`
   - relevant playbook, inventory, or role docs
2. Identify the correct `just` target for the task.
3. Run the target through `just`, not bare Ansible, unless the repo explicitly requires it.
4. Verify the result from command output or live checks.
5. Update the repo notes or project docs when the workflow changes in a durable way.
6. If the task changed repo state and the user did not ask for a scratch diff, commit the change and leave the tree clean before wrapping up.

## Recurring project monitors

Use the same repo discipline when setting up or changing cron-based project monitors for homelab work.

- List existing jobs before removing, replacing, or consolidating a tracker.
- Prefer a quiet monitor that only pings on meaningful updates, blockers, regressions, or explicit user-action needs.
- If the project is already complete and stable, report completion once and then stop unless a regression appears.
- Encode silence as an explicit requirement in the monitor prompt; do not assume the scheduler will stay quiet by default.

## Common pitfalls

1. **Using bare Ansible when a `just` target exists.** Follow the repo’s wrapper flow first.
2. **Reading `.env` or secrets directly.** The wrapper should supply credentials.
3. **Treating firewall as a separate domain.** It belongs inside this umbrella skill.
4. **Treating Kubernetes as imperative cluster admin.** Prefer GitOps/declarative repo changes.
5. **Skipping verification after live infra changes.** Always confirm the resulting state.
6. **Assuming a hostname is correct because DNS resolves.** Verify the live HTTPS route and the actual backend before adding aliases.
7. **Assuming Traefik is not still matching the hostname.** If `hermes.bp-house.com` lands on Traefik or another admin surface, inspect the live `IngressRoute`/Ingress first; a stale proxy alias may still be claiming the host.
8. **Confusing the built-in Hermes dashboard with Mission Control.** `hermes.bp-house.com` should be tested against the live browser title and nav. Mission Control on `:3000` is not a valid proxy target for the built-in dashboard.
9. **Forcing Flux with the CLI when it is unavailable.** If `flux` is not installed locally, use `kubectl annotate ... reconcile.fluxcd.io/requestedAt=<timestamp>` on the GitRepository/Kustomization/HelmRelease objects to trigger reconciliation.
10. **Leaving git work uncommitted after completing a repo change.** If the user has not asked for a scratch diff, commit the change and leave the tree clean.
11. **Creating many tiny skills for adjacent repo operations.** Keep this as one umbrella skill and use references for detail.
12. **Leaving recurring project monitors noisy after the work is done.** Confirm whether the monitor should stay silent on unchanged checks, and remove or downshift trackers once the project is stable.
13. **Assuming DNS reachability implies ingress reachability.** If a private hostname resolves but returns `404`, verify the Traefik/IngressRoute host rule and add the hostname alias there before concluding the service is down.

## Verification checklist

- [ ] Confirm the repo guidance (`AGENTS.md` / `justfile`) was checked
- [ ] Confirm the correct `just` target was used
- [ ] Confirm secret handling stayed inside the wrapper flow
- [ ] Confirm any live change was verified after application
- [ ] Confirm HTTP/S reachability was checked for the exact hostname, not just DNS resolution
- [ ] Confirm the live browser page title/nav were checked when the goal is a dashboard UI, not just an HTTP status code
- [ ] Confirm the live `IngressRoute`/Ingress host match was checked when a hostname lands on the wrong service
- [ ] Confirm repo notes or project docs were updated if the workflow changed

## Notes

If a task cannot be done through `just`, state why and point to the repo guidance that supports the exception.
