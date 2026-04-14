---
name: gemini-cli-git-review-cron
description: Create a recurring cron job that uses Gemini CLI to review multiple git repos, make selective commits, and push only when branch/upstream safety checks pass.
---

# Gemini CLI Git Review Cron

Use this when the user wants an unattended daily/nightly repo review-and-backup workflow driven by Gemini CLI.

## When to use

- Multiple local repos need periodic review/commit/push
- The commit selection should be AI-assisted, not just `git add -A`
- Safety matters: secrets, logs, caches, and broken upstream mappings must be excluded

## Core approach

1. Inspect each target repo first.
   - Verify the directory exists and is a git repo.
   - Record:
     - current branch
     - upstream branch (if any)
     - `git status --short --branch`
     - remotes
   - Check remote reachability with a non-interactive SSH call if using git@ remotes.

2. Determine push safety before any automation.
   - Safe:
     - local branch tracks an upstream, or
     - the same branch exists on `origin` and can be pushed with `git push -u origin <branch>`
   - Unsafe:
     - no upstream and remote branch names/history do not match
     - example: local `main` vs remote `master` with diverged history
   - In unsafe mode, allow review but skip auto-commit/push.

3. Use a dedicated script for the cron job.
   - Put the logic in a stable script path, e.g. `~/.hermes/scripts/gemini_repo_review.py`.
   - Have cron run the script, not a giant inline prompt.
   - Let the script print JSON for easy status reporting.

4. Ask Gemini CLI only for the review decision.
   - Gemini should return JSON only, with a schema like:
     - `action`: `noop` or `commit`
     - `include`: list of changed paths to stage
     - `exclude`: list of changed paths to avoid
     - `commit_message`: conventional commit message
     - `reason`
     - `warnings`
   - The script should validate Gemini output before acting.

5. Keep prompt context small.
   - Do not dump huge repo contents into Gemini.
   - Include only:
     - changed paths
     - `git status`
     - diff stats
     - truncated unstaged/staged diff excerpts
     - limited previews for untracked text files only
   - Large prompts can make Gemini CLI/node OOM.

6. Stage selectively and commit safely.
   - Start from an unstaged state.
   - `git reset --quiet`
   - `git add -A -- <approved paths>` for Gemini-approved files only
   - If cached diff is empty after staging, treat as noop.
   - Commit with Gemini’s message.

7. Push based on push mode.
   - tracking branch: `git push`
   - matching remote branch but no upstream: `git push -u origin <branch>`
   - unsafe: skip

## Practical filtering rules

Prompt Gemini to favor:
- configuration
- docs
- scripts
- skills
- notes / PKB content

Prompt Gemini to exclude:
- `.env` and credential files
- secrets/tokens discovered in diffs
- caches
- transient logs
- cron output
- bulky generated artifacts
- local-only noise like recent-files state

## Important implementation details

### Parse untracked files separately
Use `git status --porcelain=v1` and identify `??` entries explicitly.
Only build file previews for untracked files, not every changed path.
This keeps prompts much smaller.

### Validate Gemini output strictly
If Gemini requests a commit but provides no include list or no commit message, reject it.
Also discard any included/excluded path not present in the current changed-path set.

### Prefer `--approval-mode plan`
Use Gemini CLI in read-only planning mode for the review step.
Let the local script perform actual git writes after validation.

Example:
`gemini -p "...prompt..." --output-format text --approval-mode plan --include-directories <repo>`

## Cron job pattern

Create a cron job that runs the script exactly once, then summarizes the resulting JSON.
The cron prompt should also say:
- report errors clearly
- mention intentional safety skips
- do not inspect `.env` or credential files

## Pitfalls discovered

### 1. Gemini CLI can OOM on large prompts
A repo with large diffs/untracked files caused Gemini CLI (node) to crash with heap out-of-memory.
Fix: reduce diff excerpt sizes and preview only untracked files.

### 2. PKB repo auto-push can be unsafe even if the remote exists
A repo may have a reachable remote but still be unsafe for unattended push because the local branch has no upstream and the remote only advertises another branch name.
Example seen: local `main`, remote `master`, diverged histories.
Treat this as unsafe and skip push.

### 3. Gemini may correctly identify secrets in diffs
If Gemini flags a credential-bearing file, keep that file out of the staged set even when other changes in the repo are committed.

## Verification checklist

Before finalizing:
- run a dry run of the script
- confirm Gemini CLI exists and responds
- confirm each repo’s remote/upstream state
- confirm the cron schedule/timezone
- make sure the script path is stable and executable by the cron environment

## Output expectations

A good run should report, per repo:
- clean / noop / dry_run_commit / committed_and_pushed / skipped_unsafe_push / error
- branch
- push mode
- commit hash when applicable
- Gemini decision summary
