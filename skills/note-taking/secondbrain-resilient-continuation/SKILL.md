---
name: secondbrain-resilient-continuation
description: Update active Obsidian project notes for interruption-resilient continuation, including compact resume plans, low-cost continuation prompts, and vault-local Python execution via uv.
metadata:
  hermes:
    tags: [pkm, obsidian, projects, cron, resilience]
    category: knowledge
---

# Secondbrain Resilient Continuation

Use this skill when working in a PARA-style Obsidian vault on an active project that should keep moving even if the session is interrupted by usage limits, context limits, or timeouts.

It covers three reusable patterns:
1. adding a compact resume plan to the project note,
2. scheduling a self-contained continuation job,
3. running vault-local Python scripts reliably with `uv run python`.

---

## Trigger conditions

Use this skill when the task involves any of the following:
- an active project note that should be safe to resume later
- a request to continue work after usage or context limits
- a recurring cron/job that should pick up from project notes
- running Python scripts from inside the vault/project folder

---

## Workflow

### 1) Make the project note self-resumable

Update the active project note with a short section such as:
- current status
- what has been completed
- what the next safe step is
- what to do if the session is interrupted
- any low-cost fallback action if limits are tight

Keep the resume plan compact and specific. The goal is for a future run to continue from the note alone without re-deriving decisions.

### 2) Encode a usage-limit strategy

If the task may be interrupted by limits, add guidance like:
- prefer the lightest model or cheapest action that can still make progress
- batch related edits to avoid extra restarts
- if limits are tight, switch to note updates, planning, or other low-cost work
- make the next-step instruction explicit in the note

Do not invent a live numeric quota if the session does not expose one. Instead, instruct the next run to retrieve whatever usage-limit information is visible at that time.

### 3) Schedule or update a continuation job

Create or update a recurring job that:
- reads the project note first
- resumes from the next safe unfinished step
- stays self-contained because cron runs do not inherit chat context
- uses low-cost defaults unless a heavier action is justified

If a continuation job already exists, update it rather than creating a duplicate.

### 4) Run local project Python with uv

When executing scripts inside the vault/project folder, prefer:

```bash
uv run python path/to/script.py ...
```

Do this instead of plain `python` when the environment may not have `python` on PATH.

---

## Pitfalls

- Do not rely on a chat session as the only source of state.
- Do not create a continuation prompt that depends on prior conversation context.
- Do not assume `python` is available; use `uv run python` for vault-local scripts.
- Do not overcomplicate the resume plan; it should be a compact handoff, not a full design doc.

---

## Verification

Before finishing, verify that:
- the project note contains a compact resume plan
- the note names the next safe step
- the continuation job references the project note and is self-contained
- any local Python script actually runs with `uv run python`
- the resulting files or cron job are updated in the vault/tooling as intended
