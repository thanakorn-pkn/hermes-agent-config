# homelab-infra workflow notes

## Observed conventions

- The repo should be operated through `just` entrypoints rather than ad hoc direct Ansible calls.
- The `just` wrapper is expected to load 1Password-backed credentials from the repo `.env` during execution.
- `.env` and credential files must not be inspected directly.
- Firewall/UFW changes are part of the same homelab-infra scope.
- Kubernetes work in this repo is GitOps-managed, so prefer declarative repo changes.

## Practical reminder

If a task fails because a secret-backed lookup is unavailable, the first thing to check is whether the command was run through the repo’s expected `just` path.

## Why this matters

This keeps the skill compact at the class level while preserving session-specific repo conventions here instead of fragmenting the library into many narrow helper skills.
