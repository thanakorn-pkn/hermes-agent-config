# Project monitoring cron jobs

Use this pattern for recurring monitors that report project progress.

## Key rules

- Before removing or replacing an existing tracker, list cron jobs and confirm the job ID/name you intend to change.
- Default project-status monitors to **quiet mode**: do not send output when there is no meaningful change.
- Only notify on:
  - a noteworthy progress update
  - a blocker or regression
  - a state change that requires user attention
  - final completion/stability confirmation
- If the project is already complete and stable, report completion once and then stop unless a regression appears.
- Phrase prompts narrowly so the agent knows silence is acceptable and desired when nothing changed.

## Good prompt wording

- "Stay silent unless there is a noteworthy update or a blocker that needs user action."
- "If nothing materially changed since the last check, do not send output."
- "Report completion once and then stop unless a regression appears."

## Operational tip

For long-running project monitors, prefer a quiet progress monitor over a noisy tracker. This avoids repeated pings after the important work is already done.
