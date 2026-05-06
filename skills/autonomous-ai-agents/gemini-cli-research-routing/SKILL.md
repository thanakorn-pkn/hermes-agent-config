---
name: gemini-cli-research-routing
description: Use Gemini CLI for repository analysis, research synthesis, and exploratory reasoning. Prefer an interactive session when it is actually productive, but fall back to headless prompt mode when the interactive UI stalls or yields no usable output.
metadata:
  hermes:
    tags: [gemini, cli, research, agents, interactive-session]
    category: autonomous-ai-agents
---

# Gemini CLI research routing

Use this skill when the user explicitly asks for Gemini CLI, or when Gemini is the best fit for a research/synthesis task and you need a reliable way to run it from Hermes.

## When to use

- Repository analysis
- Research synthesis
- Comparing docs and extracting architecture / workflow summaries
- Long-form reasoning where Gemini can help, especially when the user asked for it directly

## Core routing rule

For live session inventory, `gemini --list-sessions` is useful and returns per-project session history.
For quick one-shot probes, prefer `gemini -p` over interactive mode when the UI stalls or no usable text appears.

Prefer an interactive Gemini session *only if* the session is likely to stay responsive and you need follow-up interaction.

Use headless `-p/--prompt` mode when:
- You want deterministic output
- The interactive UI appears but does not produce usable text
- The session sits at the prompt without returning a result after a short polling window
- You only need one-shot analysis or synthesis

## Reliable launch pattern

1. Start Gemini in the target repo or workspace.
2. If the PATH is suspicious in non-interactive shells, invoke it through `bash -ic` so shell setup is loaded.
3. Use interactive mode first when requested.
4. If the interactive session stalls, fall back to `gemini -p` with the same prompt.

Example interactive launch:

```bash
bash -ic 'cd /path/to/repo && gemini --skip-trust'
```

Then submit the prompt through the session.

Example deterministic fallback:

```bash
bash -ic 'cd /path/to/repo && gemini -p "your prompt here"'
```

## Practical workflow

1. Read the relevant repo/docs first if needed.
2. Prefer the official Gemini CLI changelog docs (`https://geminicli.com/docs/changelogs/`) for release/news summaries; use GitHub releases as a fallback or cross-check.
3. Start Gemini with the smallest useful prompt.
4. Poll once or twice for a response.
5. If the interactive session is still idle or only shows the UI shell, switch to `-p`.
6. Ground the final answer with direct file reads or repo output.

## Extraction tips

- The changelog docs page groups announcements by version, and each announcement section is often easiest to extract by locating the `h2` heading and reading the following list block.
- If browser text snapshots are noisy or truncated, use console/DOM inspection to target the specific release heading and sibling content.
- If search engines block or return captcha pages, skip them and go straight to the official docs or GitHub releases page.

## Pitfalls

- Interactive Gemini can appear to start successfully but never return useful content in some Hermes terminal flows.
- Do not waste time waiting indefinitely on a stalled prompt UI.
- Do not assume interactive is always better; for many repository summaries, `-p` is the safer path.
- Use `bash -ic` if the current shell cannot see the Gemini binary or its PATH additions.

## Verification

After Gemini returns, confirm the answer against the source files or repo output before acting on it.

If the result will be persisted in a PKB, make sure the write follows the vault's note conventions and links the source repo explicitly.
