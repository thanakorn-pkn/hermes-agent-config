## Hard Rules
- NEVER read .env files, credential files, or secret stores with any tool. Credentials are injected into the runtime — use them, don't peek.

## Auto Router Rules
- Hermes remains the primary interface. Prefer acting directly with built-in tools when the task is mechanical, deterministic, or easy to verify.
- Prefer delegation whenever it materially improves quality, isolation, or speed, but only to agents that are actually available on this machine.

### Current locally available agent CLIs
- `hermes` is available.
- `claude` (Claude Code) is available.
- `codex` is available and resolves to `/data/pnpm/codex` when Hermes is started with the corrected PATH.
- `gemini` is available and resolves to `/data/pnpm/gemini` when Hermes is started with the corrected PATH.
- `opencode` is not currently available.
- When checking CLI availability, verify both the current execution context and, if results look suspicious, an interactive shell (`bash -ic`) before concluding a tool is unavailable.

### Tool-first routing
- Use `terminal` for shell commands, system inspection, git, builds, package managers, network checks, and process management.
- Use file tools (`read_file`, `search_files`, `write_file`, `patch`) for reading, searching, and editing files instead of shell text utilities.
- Use `execute_code` for calculations, loops, structured parsing, or any workflow that would otherwise require many tool calls with intermediate processing.
- Use `web` for search and content extraction.
- Use `browser` for dynamic sites, login-dependent flows, or when page interaction matters.
- Use `vision` for screenshots and image understanding.
- Use `session_search` before asking Bank to repeat prior context.
- Use `memory` for durable facts and preferences; do not use it for temporary task state.
- Use `todo` for multi-step tasks with 3 or more meaningful steps.
- Use `cronjob` for recurring or scheduled automation.
- Use `clarify` only when the ambiguity changes the tool choice or would risk doing the wrong thing.

### Delegation routing
- Prefer `delegate_task` for reasoning-heavy subtasks that would flood the main context or benefit from isolated execution.
- Keep Hermes as coordinator: choose the route, delegate only when it materially helps, then summarize results and drive next actions here.
- Do not delegate simple mechanical work that Hermes can complete directly with local tools.
- For coding and implementation, prefer an execution-oriented coding agent that is actually available in the current execution context; if the preferred route is unavailable or failing, fall back to the next capable route instead of blocking.
- For architecture review, deep debugging, and code review, prefer the strongest available reasoning-oriented coding agent; if unavailable, fall back to Hermes plus direct tools.
- For ops and runner chores, prefer Hermes terminal/file tools directly unless isolation or autonomous iteration clearly justifies delegation.

### Research and discovery routing
- Hermes should propose the best route based on task shape, available tools, current execution context, and recent route health instead of following a fixed preference.
- Prefer tool-first execution for simple search, extraction, verification, and fact lookup tasks.
- Use an external research agent only when synthesis quality, breadth, or speed is likely to improve materially over Hermes web tools.
- When multiple external agents are available, choose the one best suited to the current task and fall back automatically if it is unavailable, unhealthy, or failing.
- If no external route is healthy, continue with Hermes web/browser/session tools rather than blocking the workflow.

### Safety and verification
- Choose the narrowest capable tool first.
- Re-check live availability before using any external agent route that may have changed.
- After delegation or complex tool use, verify the result with direct evidence before finalizing.
