---
name: lightweight-git-review-cron
description: Create a recurring Hermes cron job that reviews multiple git repos with a lightweight model, commits selectively, and pushes only when branch/upstream safety checks pass.
---

# Lightweight Git Review Cron

Use this when the user wants an unattended daily/nightly repo review-and-backup workflow powered by Hermes with a small model such as `gpt-5.4-mini`.

## Principles

- Prefer Hermes-native automation over external CLI model wrappers.
- Keep the model context small: changed paths, branch/upstream state, status, diff stats, and minimal excerpts only.
- Never inspect `.env` files or credential-bearing files.
- Commit/push only when the repo is clearly safe for unattended automation.
- If a repo looks unsafe, skip it rather than forcing a risky commit.
- Overnight delivery should be quiet: use local delivery / no external notifications unless explicitly requested.

## Safety checks

Before any commit or push:

1. Confirm the path exists and is a git worktree.
2. Record current branch, upstream, remotes, and `git status --short --branch`.
3. Treat the repo as **unsafe** if any of the following apply:
   - detached HEAD
   - no upstream and no matching remote branch
   - remote branch/history mismatch
   - suspicious or sensitive paths are present
4. If unsafe, do not commit or push; report the skip reason only.

## Sensitive-path rules

Never read or preview files that match or resemble:

- `.env`
- `.env.*`
- credential / credentials files
- token / secret / auth material
- private key material

If sensitive paths appear in `git status`, exclude them from the review and skip auto-commit if their contents would need inspection.

## Commit/push behavior

When safe:

- stage only the approved non-sensitive files
- commit with a short conventional commit message
- push only if the branch/upstream state is safe

Recommended push policy:

- tracking branch -> `git push`
- matching branch on origin but no upstream -> `git push -u origin <branch>`
- anything else -> skip push

## Prompt shape for cron jobs

A good cron prompt should:

- name the exact repos to review
- state that the model must be lightweight (`gpt-5.4-mini` or similar)
- require quiet local delivery overnight
- require skipping unsafe repos
- require never inspecting `.env` or credential files
- require direct evidence in the final summary for any commit/push

## Output expectations

Per repo, report one of:

- `clean`
- `noop`
- `committed_and_pushed`
- `skipped_unsafe_push`
- `error`

Include:

- branch
- push mode
- commit hash when relevant
- brief reason / warnings
