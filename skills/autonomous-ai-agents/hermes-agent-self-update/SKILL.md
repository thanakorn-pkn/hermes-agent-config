---
name: hermes-agent-self-update
description: "Review Hermes updates before applying them: check current vs upstream version, summarize changes by feature/fix/obsolete-config/security, require a clean ~/.hermes config repo before approval, then run hermes update with prompt handling that prefers defaults and otherwise answers yes."
version: 1.4.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, self-update, git, security, approval, review]
    related_skills: [hermes-agent, github-pr-workflow]
---

# Hermes Agent Self Update

Use this when Bank asks to review and optionally apply an update to the local Hermes installation.

This skill is intentionally **approval-gated**:
1. inspect current vs latest upstream state
2. summarize the update
3. perform a security-focused review
4. ask for approval
5. only then execute `hermes update`

## Goals

- Check the **current Hermes version** and the **latest available upstream version**
- Compare the current checkout against the update target
- Summarize changes split into:
  - **new features**
  - **fix issues**
  - **obsolete / removed / config-impacting changes**
  - **security concerns**
- Require the separate `~/.hermes` config repo to be clean before asking for update approval
- Ask Bank for approval only after that prerequisite is satisfied
- If Bank approves, run `hermes update` and bypass interactive prompts by:
  - accepting the **default** answer when the prompt is default-yes (`[Y/n]`)
  - answering **`y`** when a prompt is not clearly default-yes

## Important safety rules

- Do **not** run `hermes update` before approval.
- Do **not** claim a security scan was clean unless you actually ran one.
- Always report dirty working tree state and local branch divergence.
- If `git status --short --branch` shows the repo is **ahead** of `origin/main` or **diverged**, explicitly warn that Hermes' built-in updater may hard-reset to `origin/main` when fast-forward is impossible.
- If the working tree is dirty, note that `hermes update` may auto-stash and offer to restore local changes afterward.
- Do **not** confuse the Hermes source checkout `~/.hermes/hermes-agent` with the separate Hermes config repo at `~/.hermes`.
- A clean `~/.hermes` repo is a hard prerequisite before asking for approval to self-update. If it is dirty, stop and tell Bank to let the separate config-commit cron handle it first.
- Never read `.env` or other credential files.

## Repo assumptions

Default Hermes source checkout:
- `~/.hermes/hermes-agent`

Main update target branch:
- `origin/main`

Separate Hermes config repo:
- `~/.hermes`

## Steps

### 1. Establish current local state

Run these checks first:

```bash
hermes --version
git -C ~/.hermes/hermes-agent status --short --branch
git -C ~/.hermes/hermes-agent rev-parse --short HEAD
git -C ~/.hermes/hermes-agent describe --tags --always HEAD
git -C ~/.hermes status --short --branch
git -C ~/.hermes diff --name-only
```

Also capture:
- current branch
- whether the tree is clean/dirty
- whether local is ahead/behind/diverged
- whether the separate Hermes config repo at `~/.hermes` is currently clean or dirty

If `~/.hermes` is dirty at this stage, stop the self-update workflow before approval and report that the config repo must be cleaned/committed first.

If `hermes --version` shows a release version but `git describe` shows additional commits, report both.

### 2. Determine the latest upstream candidate

Fetch upstream without modifying local files:

```bash
git -C ~/.hermes/hermes-agent fetch origin --prune
git -C ~/.hermes/hermes-agent rev-parse --short origin/main
git -C ~/.hermes/hermes-agent describe --tags --always origin/main
git -C ~/.hermes/hermes-agent rev-list --count HEAD..origin/main
git -C ~/.hermes/hermes-agent show origin/main:hermes_cli/__init__.py | sed -n '1,20p'
```

Interpretation rules:
- Treat `hermes --version` as the **current installed Hermes version**.
- Treat the remote `hermes_cli/__init__.py` plus `origin/main` commit as the **latest available upstream candidate**.
- If the version string is unchanged but `HEAD..origin/main` is non-zero, say clearly:
  - "same advertised version string, but local checkout is behind upstream by N commit(s)."

### 3. Compare changes between current and latest

Use the commit range `HEAD..origin/main`.

Minimum review commands:

```bash
git -C ~/.hermes/hermes-agent log --no-merges --format='%h%x09%s%x09%an%x09%ar' HEAD..origin/main
git -C ~/.hermes/hermes-agent diff --stat HEAD..origin/main
git -C ~/.hermes/hermes-agent diff --name-only HEAD..origin/main
```

Then categorize the changes into these buckets:

#### New features
Look for:
- commit subjects starting with `feat:`
- user-visible new commands, tools, platforms, or integrations
- new workflows, UI capabilities, or delivery features

#### Fix issues
Look for:
- `fix:` commits
- bugfixes affecting gateway stability, tool behavior, slash commands, TUI/CLI, auth, or message delivery
- perf changes that clearly fix reliability or resource issues

#### Obsolete / removed / config-impacting changes
Look for:
- removed or renamed settings
- new required env vars or config fields
- migration prompts or compatibility notes
- changes that make old workflows obsolete or change defaults
- lockfile/build/runtime changes with operator impact

#### Security concerns
Always review this section explicitly, even if the answer is "none found in review."

Focus especially on changes touching:
- auth / OAuth / credential resolution
- approvals / dangerous command handling
- gateway message dispatch
- webhook / API server / browser / MCP integrations
- terminal / process execution
- file access / memory / session storage / prompt handling
- secret redaction or data exfiltration safeguards

### 4. Perform a security-focused review

First do a manual security triage from commit subjects and changed paths.

At minimum inspect:

```bash
git -C ~/.hermes/hermes-agent log --no-merges --format='%h%x09%s' HEAD..origin/main
git -C ~/.hermes/hermes-agent diff --name-only HEAD..origin/main
```

If any commit subjects or files suggest security-relevant changes, inspect targeted diffs before asking for approval.

Examples of high-priority review targets:
- files under `gateway/`, `tools/`, `agent/`, `hermes_cli/auth.py`, `hermes_cli/main.py`, API server, MCP, browser, terminal, approval, or credential logic
- commit subjects mentioning `security`, `auth`, `secret`, `token`, `credential`, `approval`, `redact`, `sandbox`, `permission`, `oauth`

Inspect the actual diffs for those files/commits.

#### Optional static scan
If a scanner is already installed, run a best-effort scan on a temporary archive of `origin/main`:

```bash
tmpdir=$(mktemp -d)
git -C ~/.hermes/hermes-agent archive origin/main | tar -x -C "$tmpdir"
semgrep scan --config auto "$tmpdir"
```

Rules:
- Only run `semgrep` if it is already available.
- Do not install new security tooling just for the review unless Bank explicitly asks.
- If no scanner is available, say the security review was **manual diff-based review only**.

### 5. Report the update summary before approval

Use this reporting structure:

- **Current Hermes**
  - version string
  - current HEAD
  - current branch
  - clean/dirty state
  - ahead/behind/diverged state
- **Latest upstream candidate**
  - remote version string
  - remote commit
  - number of commits behind
- **New features**
- **Fix issues**
- **Obsolete / config-impacting changes**
- **Security concerns**
- **Recommendation**

Keep the summary concise but concrete. Mention representative commits or changed areas, not just raw counts.

Before asking for approval, explicitly confirm whether `~/.hermes` is clean.
If it is dirty, do **not** ask for approval yet; stop and report that the config-commit cron (or an equivalent manual commit) must run first.

Always end phase 1 by asking for approval explicitly only when the prerequisite is satisfied. Use this exact phrase:

```text
Reply: approve hermes update
```

Do not update until Bank approves.

### 6. If Bank approves, re-check state immediately before updating

Before running the updater, re-run:

```bash
hermes --version
git -C ~/.hermes/hermes-agent status --short --branch
git -C ~/.hermes/hermes-agent rev-parse --short HEAD
git -C ~/.hermes/hermes-agent fetch origin --prune
git -C ~/.hermes/hermes-agent rev-list --count HEAD..origin/main
git -C ~/.hermes status --short --branch
git -C ~/.hermes diff --name-only
```

If there are now zero commits behind, report that no update is needed and stop.

If the repo is ahead/diverged, remind Bank that the built-in updater may hard-reset to `origin/main` when fast-forward is impossible, then proceed only if the approval still clearly applies.

If `~/.hermes` is dirty at this point, stop and report that the prerequisite is no longer satisfied. Do **not** run `hermes update` until the config repo is clean again.

### 7. Execute `hermes update` after approval

Preferred execution method: **PTY + process control**, not blind non-interactive stdin.

Reason:
- `hermes update` uses interactive prompts like `Restore local changes now? [Y/n]` and `Would you like to configure them now? [Y/n]`
- To honor Bank's preference, the agent should accept the **default** on default-yes prompts and otherwise answer **yes**

Preferred behavior during execution:
- For prompts ending with `[Y/n]` → send **Enter** (accept default yes)
- For prompts with no clear default or `[y/N]` → send **`y`**

When using Hermes terminal/process tools, prefer:
1. start `hermes update` in PTY mode
2. watch output for prompts
3. submit newline for default-yes prompts
4. submit `y` for any non-default-yes confirmation
5. wait for completion and capture the full result

Only use a blind `yes` pipe as a fallback if PTY/process control is unavailable.

### 8. Verify after update

After `hermes update` completes, verify with:

```bash
hermes --version
git -C ~/.hermes/hermes-agent status --short --branch
git -C ~/.hermes/hermes-agent rev-parse --short HEAD
git -C ~/.hermes/hermes-agent rev-list --count HEAD..origin/main
git -C ~/.hermes status --short --branch
```

Recommended extra checks when feasible:

```bash
hermes status
hermes gateway status
```

Verify and report:
- final Hermes version string
- final HEAD
- whether local is now up to date
- whether local changes were restored from stash
- whether config migration ran or was skipped
- any warnings/errors from the updater
- whether `~/.hermes` remained clean throughout the approved update flow


## Pitfalls

- `hermes update` updates against `origin/main`, not an arbitrary release tag.
- The remote `__version__` string may remain the same even when upstream has additional commits.
- If the local checkout is ahead/diverged, the updater may hard-reset to `origin/main` if fast-forward pull fails.
- Dirty working tree state can trigger auto-stash + restore prompts.
- Non-interactive execution may skip prompts differently from PTY execution; PTY is preferred when the user explicitly wants default answers honored.
- `~/.hermes` must be clean both before approval and immediately before execution; if it becomes dirty, stop and wait for the separate config-commit workflow to clean it up.

## Verification checklist

Before approval:
- current version captured
- latest candidate captured
- behind count captured
- changes categorized
- security review completed and labeled manual or scanned
- current `~/.hermes` clean/dirty state reported
- approval requested only if `~/.hermes` is clean

After approval:
- prerequisite re-checked
- updater executed only if `~/.hermes` was still clean
- prompts handled with default/yes behavior
- final version verified
- final git state verified
- results summarized clearly
