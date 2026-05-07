# Mission Control triage notes

Session-derived quick checks for Mission Control UI issues before escalating to a Kanban task.

## Live verification pattern

When a user reports that a page is "not loading properly":

1. Check the service is listening on the expected port.
2. Verify the route with `curl` and a browser snapshot.
3. Distinguish between:
   - route/page failure
   - partial page render
   - missing sub-metrics or backend data

## Example from this session

- `http://192.168.1.161:3000/` returned the Mission Control dashboard.
- `http://192.168.1.161:3000/subscription` returned `200 OK` and rendered the Subscription page.
- The page showed partial data issues such as:
  - `Claude CLI not found: claude`
  - `Codex CLI not found: codex`
  - `Gemini status available`

## Useful commands

- `ss -ltnp | grep ':3000\|:8000\|:5433'`
- `podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'`
- `curl -I http://HOST:PORT/path`
- browser snapshot / console check for client-side rendering issues

## Triage outcome rule

If the route loads but a subsection is incomplete, log the issue as a *partial-data / integration* problem instead of a full page outage.