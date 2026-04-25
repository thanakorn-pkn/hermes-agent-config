---
name: homelab-quadlet-deploy-validation
description: Validate and roll out self-hosted homelab services that run on the host via Ansible-rendered Podman quadlets and systemd, with a plan-first approval gate and reboot-persistence checks.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [homelab, ansible, podman, quadlet, systemd, reboot-persistence, validation, deployment]
    related_skills: [subagent-driven-development, writing-plans, systematic-debugging]
---

# Homelab Podman Quadlet Deployment Validation

Use when deploying or modifying a self-hosted service that must survive host restart and is managed via Ansible + Podman quadlets/systemd on a homelab machine.

## Trigger conditions
- The service is meant to run on the host, not inside Kubernetes.
- The deployment uses Ansible roles to render quadlet/container/systemd units.
- You need the service to survive reboot and come back automatically.
- You want a plan-first workflow before any execution.

## Core workflow
1. **Plan first, then pause.**
   - Draft the implementation/deployment plan before touching files or running apply steps.
   - Present the plan to the user and wait for approval when the user asked for an approval gate.

2. **Verify the service contract before wiring automation.**
   - Check entrypoint, build args, ports, and required environment variables in the app repo.
   - Confirm helper scripts and Dockerfiles agree on arg names and runtime expectations.

3. **Validate in isolation before touching the real inventory.**
   - Create a temporary/scratch inventory or playbook that exercises only the target role.
   - Prefer isolated validation over applying directly to production inventory.

4. **Run check mode, but know the limits.**
   - Use `ansible-playbook --check` for fast validation.
   - If a module does not support check mode, treat that as a tooling limitation, not automatic failure of the whole approach.
   - Re-run with targeted live validation only for the module/step that needs it.

5. **Verify boot persistence explicitly.**
   - Confirm the generated systemd user units exist and are enabled.
   - Restart the host or service boundary and verify the app still comes back.
   - Check that the service binds the correct host interface after restart.

6. **Stop on credential/runtime blockers.**
   - If the live apply depends on external auth or injected credentials that are not available in the current runtime, do not guess.
   - Report the blocker clearly and ask for the missing auth/context.

## Common pitfalls discovered
- Some Podman/Ansible modules may not fully support check mode.
- Rootless-user role variables must match the role schema exactly; drift here causes confusing validation failures.
- Non-interactive shells may miss PATH entries used by locally installed CLIs.
- For dev runners that must bind `0.0.0.0`, some services require an explicit auth-mode environment variable or they refuse to start in a trusted-local mode.
- Dockerfile build-arg names and wrapper scripts often drift; verify both before adding build helpers.
- A service that works in a shell may still fail under systemd if the environment is incomplete.
- 1Password lookup failures can mean either auth problems or missing item/field names; if the lookup reaches Ansible and reports the vault item is missing, fix the item naming/schema first.
- If an app expects a database username and password to stay in sync, store both in the same 1Password item instead of splitting them across items.
- If the database password is URL-encoded and ends up in Alembic/ConfigParser config, `%` may be treated as interpolation and crash startup; escape `%` before assigning the URL to Alembic config or otherwise bypass interpolation safely.
- When a backend starts but the UI still shows a disconnected banner, inspect runtime logs for gateway/auth rejection separately from deploy success; the app can be “up” while the integration is unauthorized.
- For long-running homelab deploys, run them in a detached tmux session and tee output to a log file so the result survives pane/session churn.
- 1Password lookups used inside `argument_specs` validation will fail early if the referenced item name is wrong; verify the exact vault item name/UUID before treating a validation failure as a role bug.
- When the repo uses a top-level `Justfile`, prefer invoking the `just` recipe from the repo root instead of bypassing it with raw `ansible-playbook` commands; that preserves environment loading and project-local wrappers.
- For long-running apply steps, run them inside a detached `tmux` session and log output to a file so the exact failure can be inspected after the session exits.
- For Claude Code-driven deploys, use tmux for the interactive session but keep the plan visible in chat first; do not start implementation until the user approves the plan.
- For new rootless Podman services in homelab-infra, create the full Ansible bundle together: `inventory/group_vars/<service>.yml`, `playbooks/<service>.yml`, `roles/<service>/defaults`, `handlers`, `meta/argument_specs.yml`, `tasks`, and any env templates. If the target user already exists, wire `rootless_user` with `rootless_user_manage: false` so the role only populates `rootless_user_facts`.
- When using the shared `podman_quadlet` role in rootless mode, ensure generated directories/files have explicit owner/group set to the target user if the role does not already do so, otherwise systemd unit generation can succeed while the runtime cannot access the quadlet assets.
- A LAN firewall opening is not enough if the service still binds to `127.0.0.1`; confirm the app host binding before treating UFW changes as the final fix.

## Practical verification checklist
- Role validation passes in an isolated inventory/playbook.
- 1Password-backed variables resolve successfully during validation, or failures clearly identify the incorrect vault item name/UUID.
- Quadlet/container units are generated in the expected systemd path.
- The service is enabled and starts successfully.
- A restart/reboot does not break the service.
- Runtime logs show the correct bind address, auth mode, and dependency resolution.
- Detached `tmux` logs capture the final exit status for long-running deploys.

## When to use with tmux/Claude Code
If the deployment is being executed through an interactive Claude Code session:
- Use tmux for long-running work.
- Keep the plan visible in the conversation first.
- Do not start implementation until the user approves the plan.
- Use the tmux pane to monitor progress and capture output when needed.

## Output style
When summarizing the plan or validation results, lead with:
- what will change
- how it will be verified
- what could block live apply
- whether a reboot-persistence check is included
