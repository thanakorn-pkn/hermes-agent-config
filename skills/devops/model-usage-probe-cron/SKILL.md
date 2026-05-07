---
name: model-usage-probe-cron
description: Low-token probing of Claude Code, Codex, and Gemini CLI usage/status plus optional cron scheduling. Use when the user wants a lightweight automation to check model usage limits or plan status without spending many tokens.
---

# Model usage probe cron

Use this skill when the user wants a low-/no-token way to check current CLI model usage or status for Claude, Codex, and Gemini, especially when the result should run on a schedule.

## Goal

Produce a small shell probe that:
- calls each CLI with the least expensive status/usage path available
- tolerates TTY/login-shell quirks
- emits a compact summary and/or JSON line
- can be run from cron with a stable environment
- logs locally unless the user asks for notifications

## Recommended workflow

1. **Check installed CLIs and auth state**
   - Verify `claude`, `codex`, and `gemini` are available in the live shell.
   - Do not inspect secrets or credential files.
   - If PATH differs between interactive and non-interactive shells, verify with both `command -v` and a `bash -ic` wrapper.

2. **Probe each tool with the native usage/status path**
   - **Claude Code:** open an interactive session, then run `/usage`.
     - This is the most reliable source for the current session and weekly limit display.
     - Typical output includes session usage, current 5h/session window, weekly limit, and reset times.
   - **Codex:** open an interactive session, then run `/status`.
     - Typical output includes the account, model, permissions mode, and visible 5h/weekly limit bars with reset timing.
     - The session itself may also point to an up-to-date web usage page.
   - **Gemini CLI:** open an interactive session, then run `/model`.
     - Gemini often shows a quota indicator in the TUI (for example, a percent used line) and the active plan/account context.
     - It may *not* show an exact reset time or hard cap in the CLI, so record whatever quota text is visible.

3. **Expect TTY and PATH quirks**
   - Some CLIs behave differently in non-interactive shells.
   - If a binary disappears in cron or `script`, resolve the absolute path first or wrap the command in `bash -ic` when needed.
   - For cron, set a minimal `PATH` and `HOME` explicitly.
   - For interactive probing, tmux is often the most reliable wrapper because it lets you confirm the prompt and capture the resulting screen.

4. **Implement a compact parser**
   - Strip box-drawing, ANSI noise, and repeated whitespace.
   - Match the strongest status line first.
   - Emit a concise human-readable summary plus a JSON object on one line for downstream parsing.

5. **Write a small shell script**
   - Put the script in a stable location such as `~/bin/model-usage-probe.sh`.
   - Make it executable and syntax-check it with `bash -n`.
   - Run it twice if needed; the first run may be empty if the CLI initializes lazily.

6. **Schedule with cron**
   - Prefer a 15-minute interval for lightweight monitoring if the user asks for frequent checks.
   - Add `PATH` and `HOME` inline in the crontab entry.
   - Redirect output to a local log file unless the user wants notifications.

## Example cron entry

```cron
*/15 * * * * PATH=/usr/bin:/bin:/usr/local/bin:/data/pnpm:/home/tphat/.local/bin HOME=/home/tphat /home/tphat/bin/model-usage-probe.sh >/dev/null 2>&1
```

## Example data to capture

- Claude: subscription usage confirmation or usage status text
- Codex: current model name, reasoning level, permissions/mode, and any visible usage hint
- Gemini: signed-in plan, workspace sandbox status, and quota text if shown

## Pitfalls

- `codex` and `gemini` may work in an interactive shell but fail in cron/non-interactive execution because of PATH or terminal expectations.
- Box-drawing characters can break naive parsers; normalize them before matching.
- Do not overinvest in perfect quota parsing if the CLI does not expose a numeric limit.
- Avoid heavyweight wrappers that spend extra tokens; use the direct status command and log the result.

## Verification

- Confirm the script exits successfully.
- Confirm the log contains a recent JSON summary.
- Confirm cron is installed with `crontab -l`.
- If the user wants live notification, add that as a separate step after the probe is stable.
