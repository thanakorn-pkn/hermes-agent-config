---
name: approval-gated-repo-update-cron
description: Create a safe cron workflow for repository updates that sends a read-only daily review and waits for explicit chat approval before applying any git changes.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [cron, git, approval, automation, hermes, telegram]
---

# Approval-Gated Repo Update Cron

Use this when the user wants a recurring "check for updates" automation, but also wants manual approval before any repo-changing action like pull, merge, rebase, commit, or push.

## Why this pattern exists

Hermes cron jobs run autonomously in a fresh session and **cannot pause for interactive approval**. If the user says:
- "summarize updates every morning, then update after I approve"
- "send me an approval card first"
- "don't auto-apply changes"

then the correct implementation is a **two-phase workflow**:

1. **Cron job:** read-only review only
2. **Later chat turn after user approval:** perform the actual update

Do **not** try to build a single cron run that waits for a reply.

## Recommended workflow

### Phase 1: Scheduled read-only review

Create a cron job that:
1. `cd`s into the target repo
2. Records baseline repo state
3. Runs `git fetch` only
4. Computes ahead/behind vs upstream
5. Summarizes new upstream commits
6. Reports whether the working tree is clean/dirty
7. Emits an approval card with an exact reply phrase

### Phase 2: Interactive approval execution

When the user later replies with the approval phrase in chat, perform the write actions live:
- preserve local work first
- update safely
- verify the repo/app
- commit any Hermes-made follow-up changes with a conventional commit

## Mandatory safety rules

- **Cron phase must be read-only**
- In the cron prompt explicitly forbid:
  - modifying files
  - switching branches
  - pulling/rebasing/merging
  - stashing unless the user explicitly asked for it
  - committing or pushing
  - installing packages unless requested
- Always report dirty state, including modified/untracked files
- If the repo is already ahead of upstream or contains local work, call that out clearly in the approval card

## Suggested cron prompt structure

Use a self-contained prompt similar to this, filling in repo path / branch / timezone details:

```text
You are running a daily read-only update review for the repo at <repo_path>.

Goal: summarize upstream updates and generate an approval card. Do NOT modify files, switch branches, stash, pull, merge, rebase, commit, or push.

Required workflow:
1. cd into the repo
2. Collect baseline state:
   - git rev-parse --short HEAD
   - git branch --show-current
   - git status --short --branch
3. Fetch upstream without changing local files:
   - git fetch origin <branch> --prune
4. Compute ahead/behind counts between local HEAD and origin/<branch>
5. If upstream is ahead, summarize up to 10 commits from HEAD..origin/<branch> using short SHA, subject, author, and relative date. Call out likely breaking/config/migration/tooling changes.
6. If no upstream commits are ahead, say so clearly.
7. Always report whether the working tree is clean or dirty, including modified/untracked files.
8. End with heading: ## Approval card
9. In the approval card include:
   - Status: waiting for <user>
   - short "If approved, I will" list
   - exact reply phrase
   - warning that no update will be applied until the user approves in chat
```

## Good output contract

The approval card should contain:
- current branch
- current local commit
- ahead/behind counts
- dirty/clean state
- concise upstream summary
- exact reply phrase, e.g. `approve hermes self-update`

## When the user approves later

On the follow-up interactive turn:
1. re-check repo state (it may have changed since the morning review)
2. preserve local work before any risky git action
3. update using the safest repo-appropriate strategy
4. run verification/tests relevant to the repo
5. commit only Hermes-made follow-up changes, using a conventional commit
6. report exactly what changed

### Safer preservation pattern before rebase/pull

If the repo has local commits or the user specifically wants to preserve local work, create a backup branch pointing at the pre-update HEAD before rebasing or similar history-changing actions.

Recommended pattern:

```bash
cd <repo>
backup="backup/<user-or-purpose>-$(date +%Y%m%d-%H%M%S)"
git branch "$backup" HEAD
```

Then perform the update (for example, `git rebase origin/main`). This gives the user an easy rollback anchor and makes the preservation step explicit in the final report.

### Conflict-resolution lesson

If the approved update uses `git rebase` and hits conflicts, do not abort immediately if the intent is to preserve local work on top of upstream. Instead:

1. inspect `git status --short --branch` to confirm the rebase state
2. read the conflicted files and identify whether both sides contain valuable changes
3. resolve conflicts by keeping upstream fixes plus the local behavior/tests that still matter
4. search for leftover conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) before continuing
5. `git add` the resolved files and run `git rebase --continue`
6. run targeted verification for the touched area after the rebase completes

This is especially important for self-updates where upstream may have added adjacent tests or refactors since the last local patch. The goal is usually to preserve the local fix while adopting upstream improvements, not to choose one side blindly.

### Verification lesson

Do not assume the full repository test suite will be green after an approved self-update, especially for large upstream repos or environment-sensitive setups. Prefer this verification order:

1. run targeted tests covering the local change or the risky path you touched
2. optionally run the broader suite if feasible
3. if the broader suite is red, distinguish clearly between:
   - failures caused by your local change
   - pre-existing upstream failures
   - environment/dependency/config-related failures (for example missing optional packages or provider credentials)

If the full suite is noisy, still report the targeted verification result clearly instead of treating the entire update as failed by default.

## Pitfall learned

If the user asks for "approval card then auto-update after approval," do **not** model it as approval happening inside the cron job. Approval must happen in a later normal conversation turn, because cron runs cannot wait for chat interaction.
