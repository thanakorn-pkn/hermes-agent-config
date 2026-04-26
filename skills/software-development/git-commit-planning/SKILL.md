---
name: git-commit-planning
description: Plan reviewable git commit groups for any repo by inspecting repo conventions and the working tree, then produce an ordered, intent-grouped commit plan.
---

# Git Commit Planning

Use when the user asks for a commit plan, or when you need to turn a messy working tree into a small number of reviewable commits.

## Goal

Produce a commit plan that:
- groups changes by intent, not by file order
- keeps documentation, application code, configuration, tests, and unrelated cleanup in separate commits
- follows the repo's existing commit conventions
- preserves rename/move/delete relationships within a single commit

## Required discovery

1. **Convention discovery** — read whichever of these the repo has, in order, stop when you have enough context:
   - `CONTRIBUTING.md`
   - `AGENTS.md` / `CLAUDE.md`
   - `.gitmessage` / `commitlint.config.*` / `.czrc`
   - Top-level `README.md` (often documents commit style)
   - Recent history: `git log --oneline -30` to infer style if no docs spell it out

2. **Working tree inspection**:
   ```bash
   git status --short
   git diff --stat
   git diff --name-only
   git diff --cached --name-only   # already-staged
   ```

3. **Identify rename/move/delete patterns** that must stay together (use `git status` rename detection; check for symbol moves across files that need to land in one commit).

## Grouping heuristics

Prefer separate commits for:
- documentation (`*.md`, `docs/`)
- application/library code changes
- configuration (`*.yaml`, `*.toml`, `*.json`, `Dockerfile`, etc.)
- tests and test fixtures
- build/CI changes (`.github/workflows/`, `Makefile`, build configs)
- generated files (lockfiles when isolated, snapshots, fixtures)
- unrelated cleanup, formatting, or rename passes

Merge files into the same commit when they share one intent:
- a function rename + every call-site update
- a new feature + the test that exercises it
- a config schema bump + the migration that needs it
- a file move + the imports that reference its new location
- a doc rename + the cross-references that point to it

## Commit message style

Default to **Conventional Commits** unless repo history says otherwise:

```
<type>(<scope>): <imperative subject>

[optional body]
[optional footer]
```

Common types:
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `chore` — tooling, build, deps
- `refactor` — no behavior change
- `test` — tests only
- `style` — formatting, no logic change
- `perf` — performance
- `ci` — CI/CD config

If the repo uses a different convention (e.g. `[area] description`, plain imperative, or repo-specific types from `AGENTS.md`), match that instead.

## Output format

Return:
- ordered commit plan (commit 1, 2, 3, …)
- subject line per commit
- file list per commit
- one-line rationale per commit
- alternatives flagged when a split/merge call is genuinely debatable

## Verification

Before finalizing, confirm:
- the plan covers every changed/staged/untracked file the user wants committed
- delete/rename/move relationships are respected within their commits
- the plan reads as a coherent story when reviewed via `git log` afterward
- no commit mixes unrelated intents
