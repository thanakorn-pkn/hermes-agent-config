---
name: mission-control-model-usage-dashboard
description: Build a Mission Control model usage dashboard backed by CLI probes for Claude, Codex, and Gemini, with FastAPI endpoints, Next.js UI, and validation steps.
---

# Mission Control model usage dashboard

Use this skill when adding or updating a Mission Control dashboard that reports usage/status for Claude Code, Codex, and Gemini CLI.

## When to use

- The user wants a unified usage/status view for model providers in Mission Control.
- You need to normalize inconsistent CLI outputs into a dashboard-friendly snapshot.
- You are wiring a backend FastAPI route to a Next.js page and sidebar navigation.
- You need to verify the feature with backend compile checks and frontend lint/build.

## Recommended approach

### 1) Probe the CLIs with the least expensive status path

Prefer native usage/status commands over any heavy API or web scrape.

- **Claude Code:** use `/usage` in an interactive session.
- **Codex CLI:** use `/status` in an interactive session.
- **Gemini CLI:** use `/model` in an interactive session.

Practical notes:
- Some CLI tools behave differently in non-interactive shells.
- If a command is missing in a plain shell, retry with a login shell wrapper such as `bash -ic`.
- For interactive probing, a PTY wrapper such as `tmux` is often more reliable than raw subprocess capture.
- Capture enough output to derive a compact summary, current model/account, and any visible usage or quota hint.

### 2) Normalize the results into a stable schema

Create a small backend schema layer that can represent:

- `generated_at`
- per-source snapshot objects
- status (`healthy`, `degraded`, `error`, etc.)
- human-readable summary text
- a list of metrics or quota fields when available

Keep the schema tolerant of partial data because CLI outputs vary across accounts, versions, and providers.

### 3) Put probe logic in a dedicated service, not the router

Recommended backend structure:

- `schemas/model_usage.py` for snapshot/metric models
- `services/model_usage.py` for probe and normalization logic
- `routers/hermes.py` or the relevant router for the HTTP endpoint

This keeps the route thin and makes the probe logic testable and reusable.

### 4) Expose a dedicated API route

Add a route like:

- `GET /api/hermes/usage`

The response should be a single dashboard payload, not three separate ad hoc outputs.

### 5) Build a dashboard page in the existing Hermes area

Recommended frontend behavior:

- Add a page under the Hermes section, for example `/hermes/usage`
- Use the project’s existing data-fetching pattern (for example React Query)
- Render one card per provider with:
  - source name
  - health/status badge
  - short summary
  - any visible metric chips or progress indicators
- Keep the layout consistent with the rest of Mission Control
- Add a sidebar link and, if appropriate, a homepage CTA

### 6) Tighten TypeScript types on adjacent Hermes pages if needed

If a page starts failing lint/build because of `any`-style data handling or malformed destructuring, fix the nearby Hermes pages at the same time instead of only the new page. This avoids partial build failures and keeps the UI consistent.

## Validation checklist

Run the following after implementation:

- Backend syntax/compile check:
  - `py_compile` or the project’s equivalent
- Frontend lint:
  - the repo’s standard lint command
- Frontend production build:
  - the repo’s standard build command
- Smoke test the backend dashboard service directly if possible

If the frontend build fails because of environment PATH issues, retry in a login shell wrapper.

## Common pitfalls

- Parsing CLI usage output too aggressively; preserve raw summary text when exact numbers are unavailable.
- Assuming the same command works in both interactive and non-interactive shells.
- Putting probe logic directly in the router, which makes the code harder to maintain.
- Forgetting to add navigation into the existing Hermes sidebar/homepage.
- Missing formatting/type errors in neighboring pages after adding a new route.

## Good outcome

A good implementation gives Mission Control a stable, at-a-glance view of Claude, Codex, and Gemini usage/status, with a clean API and a frontend page that passes lint and build checks.