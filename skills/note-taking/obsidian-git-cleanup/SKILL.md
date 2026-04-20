---
name: obsidian-git-cleanup
description: Clean up Obsidian vault git noise from Syncthing conflict artifacts and noisy tracked plugin/session files, then commit meaningful changes in reviewable groups.
---

# Obsidian Git Cleanup

Use this when an Obsidian vault shows lots of noisy git changes from `.obsidian/`, Syncthing conflict files, workspace churn, or plugin history/state files.

## When to use
- `git status` shows many `.obsidian/*` changes unrelated to real note content
- Syncthing created `*.sync-conflict-*` files
- duplicate config files like `app(1).json`, `appearance(1).json`, `types(1).json` appear
- tracked plugin files like `recent-files-obsidian/data.json` or `emoji-shortcodes/data.json` keep changing every session
- user wants the vault fixed and committed cleanly

## Goals
1. Remove conflict junk safely
2. Keep intentional note/project edits
3. Stop tracking obviously noisy plugin history files
4. Produce small reviewable commits

## Workflow

### 1. Inspect the repo state
Run from the vault root.

```bash
git status --short --untracked-files=all
git diff --name-status -M
git log --oneline -n 8
find .obsidian \( -name '*sync-conflict*' -o -name '*(1).json' \) -type f | sort
```

Also inspect `.gitignore` and confirm what is already ignored.

### 2. Separate noise from real changes
Typical noise:
- `.obsidian/workspace*.json`
- Syncthing `*.sync-conflict-*`
- duplicate files like `app(1).json`, `appearance(1).json`, `types(1).json`
- plugin history/state files such as:
  - `.obsidian/plugins/recent-files-obsidian/data.json`
  - `.obsidian/plugins/emoji-shortcodes/data.json`

Potentially meaningful config changes:
- `.obsidian/core-plugins.json`
- `.obsidian/types.json`
- plugin `data.json` files that reflect real setup changes
- vault templates under `50_templates/`
- actual note/project markdown files

### 3. Update `.gitignore` for known noisy plugin files
If these are being tracked and churn constantly, ignore them explicitly even if other plugin `data.json` files remain allowed.

Add lines like:

```gitignore
.obsidian/plugins/recent-files-obsidian/data.json
.obsidian/plugins/emoji-shortcodes/data.json
```

Keep other plugin `data.json` files tracked if they contain real configuration.

### 4. Stop tracking noisy files without deleting local copies
Use `git rm --cached`.

```bash
git rm --cached .obsidian/plugins/recent-files-obsidian/data.json
git rm --cached .obsidian/plugins/emoji-shortcodes/data.json
```

This removes them from git history going forward while preserving the user's local files.

### 5. Delete ignored conflict artifacts from disk
Once confirmed as junk:

```bash
find .obsidian \( -name '*sync-conflict*' -o -name '*(1).json' \) -type f -print -delete
```

These are usually safe to remove because they are duplicate/editor-state conflict artifacts, not source-of-truth vault content.

### 6. Review diffs before committing
Inspect grouped diffs separately:
- `.obsidian` config changes
- template changes
- daily note/journal changes
- project-note changes
- folder reorganizations / renames

Useful commands:

```bash
git diff -- .obsidian
git diff -- '50_templates/Daily Note.md'
git diff -- '00_inbox/Journal/Daily Notes/...'
git diff -- '10_projects/...'
```

### 7. Commit in small logical groups
Recommended grouping pattern:
- `pkm(obsidian): ignore noisy plugin history files`
- `pkm(obsidian): update planner settings and daily note template`
- `capture(journal): ...`
- `project(<scope>): ...`

Stage each group explicitly and commit immediately after review.

Example:

```bash
git add .gitignore
git add -u -- .obsidian/plugins/recent-files-obsidian/data.json .obsidian/plugins/emoji-shortcodes/data.json
git commit -m 'pkm(obsidian): ignore noisy plugin history files'
```

Then repeat for template changes, journal changes, and project changes.

## Verification
After the cleanup and commits:

```bash
git status --short --untracked-files=all
git log --oneline -n 8
```

Success criteria:
- no lingering sync-conflict or `(1).json` junk in `.obsidian`
- noisy plugin history files are no longer tracked
- intentional note and project changes remain committed
- working tree is clean

## Pitfalls
- Do not blindly ignore all `.obsidian/plugins/*/data.json` files; some are real config
- Prefer `git rm --cached` over deleting tracked noisy files from disk
- Review rename/move diffs carefully so real project reorganizations are preserved
- Secret-scan git hooks may print warnings on Unicode/Thai paths; if the commit succeeds, verify with `git log` and `git status`
- Use `git add -A -- <paths>` when staging renames plus deletions in a specific project area
