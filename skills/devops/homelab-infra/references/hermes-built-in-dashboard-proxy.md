# Hermes built-in dashboard proxy pattern

Use this when exposing the Hermes *built-in* dashboard through `homelab-infra`.

## Known-good chain

- Hermes dashboard process binds to `127.0.0.1:9119` on the host.
- A Kubernetes `hermes` deployment can proxy that localhost port on a LAN-only listener, e.g. `9118`.
- The `hermes` Service should select the proxy pod.
- The `hermes` Ingress should route `hermes.bp-house.com` to that Service.

End-to-end chain:

```text
hermes.bp-house.com -> Traefik -> hermes Service :9118 -> localhost:9119 -> Hermes built-in dashboard
```

## Correct live identity

The built-in dashboard is the Hermes Agent UI, not Mission Control.

Good signs:
- page title: `Hermes Agent - Dashboard`
- nav items such as `SESSIONS`, `ANALYTICS`, `MODELS`, `LOGS`, `CRON`, `SKILLS`
- `curl -k -I https://hermes.bp-house.com` may return `405` because the dashboard accepts `GET` but not `HEAD`

Wrong signs:
- title `Mission Control`
- UI elements that mention tasks, board freshness, or Mission Control-specific navigation
- direct backend `192.168.1.161:3000` if it serves the Mission Control app

## Verification recipe

```bash
kubectl -n hermes get ingress hermes -o yaml
kubectl -n hermes get svc,endpoints -o wide
curl -k -I https://hermes.bp-house.com
curl -k -s https://hermes.bp-house.com | grep -Eo '<title>[^<]+' | head -1
```

Then open the page in a browser and confirm the live title and nav match the Hermes dashboard, not Mission Control.
