# Hermes dashboard routing lesson

Use this when exposing the Hermes dashboard or any similar internal admin surface through homelab-infra.

## What happened in this session

- `hermes.bp-house.com` initially resolved correctly in Pi-hole.
- The hostname was incorrectly aliased to the Traefik dashboard.
- `curl -k -I https://hermes.bp-house.com` returned `405` once the route existed, which indicated the hostname hit a live dashboard route rather than a dead DNS entry.
- The real dashboard backend was on `192.168.1.161:3000`.
- The durable fix was to create a real Hermes app ingress and service, not to keep aliasing the hostname to Traefik.

## Diagnostic pattern

1. Check DNS resolution first.
2. Check the HTTPS response code.
   - `404` often means the hostname is not routed.
   - `405` or `200` usually means the hostname hits a live service.
3. Search the repo for the hostname and for nearby ingress/host rules.
4. If the hostname only appears in DNS and a proxy admin route, suspect a stale alias.
5. Find the actual backend and expose it declaratively through Flux/Kubernetes.

## Preferred fix shape

- Keep `traefik.bp-house.com` for the Traefik dashboard.
- Expose the Hermes dashboard on `hermes.bp-house.com` only when it points at the Hermes service/backend.
- Use the repo’s GitOps/Kubernetes manifests rather than ad hoc live edits.
- If Traefik still claims `hermes.bp-house.com`, remove the stale alias from the Traefik dashboard route before assuming the Hermes ingress is broken.
- After the repo change, push the commit and force Flux reconciliation so the live cluster matches Git.
## Verification commands

```bash
getent hosts hermes.bp-house.com
curl -k -I https://hermes.bp-house.com
kubectl get ingress -A
kubectl -n traefik-system get ingressroute traefik-dashboard -o jsonpath='{.spec.routes[0].match}'
```

If `flux` is not available locally, force reconciliation with `kubectl annotate` on the relevant Flux objects instead of blocking on the missing CLI.
## Repo hygiene

When a git repo change is completed and the user has not asked for an uncommitted diff, commit the change and leave the working tree clean before finishing.
