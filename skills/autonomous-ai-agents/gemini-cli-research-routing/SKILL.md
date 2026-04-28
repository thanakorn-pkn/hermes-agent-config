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
2. Start Gemini with the smallest useful prompt.
3. Poll once or twice for a response.
4. If the interactive session is still idle or only shows the UI shell, switch to `-p`.
5. Ground the final answer with direct file reads or repo evidence.

## Pitfalls

- Interactive Gemini can appear to start successfully but never return useful content in some Hermes terminal flows.
- Do not waste time waiting indefinitely on a stalled prompt UI.
- Do not assume interactive is always better; for many repository summaries, `-p` is the safer path.
- Use `bash -ic` if the current shell cannot see the Gemini binary or its PATH additions.

## Verification

After Gemini returns, confirm the answer against the source files or repo output before acting on it.

If the result will be persisted in a PKB, make sure the write follows the vault's note conventions and links the source repo explicitly.
