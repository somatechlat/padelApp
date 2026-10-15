# Deploying: production vs local

Last audited 2026-10-15 against the **running** production box
(`root@140.82.15.48`) and the local dev stack. Every claim below was checked
with a command, not remembered; the commands are in §7.

Read this before touching the server. The differences between the laptop and
production are exactly the ones that take a site down.

---

## 1. The five rules

1. **Project name decides everything.** `andespadel` (dev),
   `andespadel-test`, `andespadel-localprod`, `andespadel-prod`. Always pass
   `-p` and both compose files, or you are talking to the wrong stack.
2. **Each environment has its own settings module, secrets directory, and
   database name.** They are paired; mixing one from another fails closed on
   purpose (see §3).
3. **Production code is baked into an image; local code is bind-mounted.**
   A file you edit on the laptop is live in dev instantly and **does not
   exist** in production until you commit, push, and rebuild (§5).
4. **On the server, only `/opt/padelapp` and the `andespadel-prod-*`
   containers are yours.** Ports 33900–33914 belong to Loyallia; the host
   vhosts `loyallia`, `loyallia-agent-port` and `soma-agent-zero` and every
   other container are off limits.
5. **Ask before deploying to production.** `make up-prod` and any
   `docker compose -p andespadel-prod … up` write to a live service.

---

## 2. Topology

### Local (dev)

```
browser ── http://127.0.0.1:28003
              └─ andespadel-nginx        container nginx, listen 80, conf
                     │                   docker/nginx/nginx.conf (bind mount)
                     ├─ /            → landing/ (static files, bind mount)
                     ├─ /static/ /media/ → named volumes
                     └─ /api/ /adminpanel/ /admin/ /webhooks/ /django-admin/
                            └─ http://backend:8000 → andespadel-backend
                                     source bind-mounted, runserver,
                                     settings padel.settings.dev
```

One layer. No TLS. Django never enforces an SSL redirect, so the container's
hard-coded `X-Forwarded-Proto https` is inert locally.

### Production

```
browser ── https://app.andespadelclub.com
   │        host nginx (Ubuntu 1.24, on the server itself)
   │        vhost /etc/nginx/sites-enabled/padelapp
   │          • TLS terminated here, Let's Encrypt cert
   │            /etc/letsencrypt/live/app.andespadelclub.com/
   │          • HSTS 2y, X-Frame-Options DENY, nosniff, Referrer-Policy
   │          • client_max_body_size 20M
   │          • proxy_set_header X-Forwarded-Proto $scheme  (real scheme)
   │          • proxy_pass http://127.0.0.1:34003
   └─ andespadel-prod-nginx   container nginx, listen 80 → host 34003
          conf bind-mounted from /opt/padelapp/docker/nginx/nginx.conf
          • sends X-Forwarded-Proto https unconditionally — it only ever
            sits behind the TLS terminator, and Django's SECURE_SSL_REDIRECT
            + Secure cookies depend on that header being https
          ├─ /            → landing/
          ├─ /static/ /media/ → named volumes
          └─ /api/ /adminpanel/ /admin/ /webhooks/ /django-admin/
                 └─ http://backend:8000 → andespadel-prod-backend
                        image andespadel-backend:prod (code BAKED in),
                        migrate + gunicorn (3 workers),
                        settings padel.settings.prod
```

Two layers. The container nginx must never be pointed straight at the
internet in prod, and the host vhost must never be deleted to "simplify" it.

`localprod` sits between: one layer, but the container itself terminates TLS
with a self-signed certificate (`docker/nginx/nginx.localprod.conf`,
certificates in `docker/runsecrets/tls`, `X-Forwarded-Proto $scheme`).

---

## 3. Differences, one table

| | dev | test | localprod | **production** |
|---|---|---|---|---|
| Compose project | `andespadel` | `andespadel-test` | `andespadel-localprod` | `andespadel-prod` |
| Host ports | 28000–28003 | 29000–29003 | 35000–35003 | 34000–34003 (server) |
| Settings module | `padel.settings.dev` | `padel.settings.dev` | `padel.settings.prod_local` | `padel.settings.prod` |
| Code delivery | bind mount `.:/app`, runserver | bind mount | **baked image** | **baked image** `andespadel-backend:prod` |
| Secrets | `docker/runsecrets/`, yours, `make secrets-init` | same dir | same dir (+ `tls/`) | `/opt/padelapp/docker/runsecrets/`, root, provisioned once |
| Secret file modes | dir `0700`, files `0644` | same | same | same — the app reads as uid 1000 and compose keeps the host mode |
| Database | `padel` | `padel` (test db `test_padel`) | `padel_localprod` | **`padel_prod`** |
| TLS | none | none | self-signed, in-container | Let's Encrypt, **host vhost** |
| nginx layers | 1 | 1 | 1 (TLS inside) | **2** (host vhost → container) |
| Email | file/console | file/console | files (`artifacts/outbox`) | real SMTP `mail.andespadelclub.com:465` |
| Push (FCM) | off unless configured | off | **off** (`PUSH_DISABLED`) | real (firebase secret) |
| Stripe | empty files = payments off | same | **test keys required**, live keys refused | operator's test keys |
| Celery | eager | eager | real worker + beat | real worker + beat |
| Data seeding | `seeddemo-dev`, `mirror-prod` | `seeddemo-test` | `seeddemo-localprod` | **never** — no prod seed target exists, on purpose |
| Verification | `make test-dev`, `make journey-dev` | `make test-test` | `make test-localprod`, `make journey-localprod` | curl + container health + logs (§6) |
| HSTS | n/a | n/a | **off** (a laptop hostname must not preload) | on, via the host vhost |

### Settings modules fail closed for exactly this reason

`padel.settings.prod` will not import without the production secret set and a
valid `prod-domain`; `prod_local` refuses live Stripe keys. That is what
stops a laptop from quietly becoming a production, and what stops production
from booting with a laptop's configuration.

---

## 4. nginx: what is shared and what is not

- **`docker/nginx/nginx.conf`** is one file, used by dev, test **and**
  production's container. It listens on 80, serves the landing page,
  static/media, and proxies the app paths. It sends
  `X-Forwarded-Proto https` unconditionally, which is only true because in
  production something else always terminates TLS in front of it.
- **`docker/nginx/nginx.localprod.conf`** is the localprod-only variant: it
  terminates TLS itself and derives the scheme from `$scheme`.
- **The host vhost is production-only and is not in this repository.**
  It lives at `/etc/nginx/sites-enabled/padelapp` on the server (audited
  2026-10-15). Changing it means editing a file on the server and running
  `nginx -s reload` — **never** `systemctl restart nginx`, because the same
  host serves Loyallia and soma.
- **Backend address resolution.** The container nginx resolves the name
  `backend` once, at startup, and keeps that IP for the life of the
  container. Recreating the backend (i.e. every deploy) leaves it pointing
  at a dead address → `502` until the nginx container is restarted. Commit
  `9fd7597` fixes this by re-resolving per request through Docker's DNS
  (10s cache) and is **not deployed as of this audit** — until it is, the
  runbook in §5 includes the restart step.

---

## 5. Production runbook

Everything runs from the laptop, over ssh, pinned to the compose project.
The server's checkout is at `/opt/padelapp` and tracks `main`.

```bash
# 0. What is running now (read-only)
ssh root@140.82.15.48 'cd /opt/padelapp && git log --oneline -1; docker ps --format "{{.Names}}  {{.Status}}" | grep padel'

# 1. Get the code. ff-only: a dirty or diverged checkout must be inspected,
#    never force-reset.
ssh root@140.82.15.48 'cd /opt/padelapp && git fetch origin && git merge --ff-only origin/main'

# 2. Fail fast before touching anything: the config resolves every secret
#    file, so a missing one aborts here instead of at boot.
ssh root@140.82.15.48 'cd /opt/padelapp && docker compose -p andespadel-prod \
  -f docker-compose.yml -f docker-compose.prod.yml config --quiet'

# 3. If docker/nginx/nginx.conf changed: test, then reload (graceful).
ssh root@140.82.15.48 'docker exec andespadel-prod-nginx nginx -t \
  && docker exec andespadel-prod-nginx nginx -s reload'

# 4. Rebuild + recreate the app processes. db/redis/nginx only when their
#    own config changed (compose skips unchanged services).
ssh root@140.82.15.48 'cd /opt/padelapp && docker compose -p andespadel-prod \
  -f docker-compose.yml -f docker-compose.prod.yml up -d --build backend worker beat'

# 5. Verify (§6). Until 9fd7597 is deployed, also:
#    docker compose -p andespadel-prod … restart nginx   ← stale IP after step 4
```

**Rollback:** the previous image tag still exists locally on the server; a
`git reset --hard <last-good>` in `/opt/padelapp` plus the same `up -d
--build` restores it. Secret files live outside git and survive any rollback.

**Never:** `git push` directly to the server's working copy from the laptop,
edit files under `/opt/padelapp` by hand (it tracks `main`; local edits show
up as drift and the next pull conflicts), or run seed/demo commands against
production.

---

## 6. Production verification checklist

```bash
# containers: every one healthy, no restart loops
docker ps --format '{{.Names}}  {{.Status}}' | grep padel
docker inspect andespadel-prod-backend --format '{{.RestartCount}}'   # must be 0

# no credential in any container's environment (secrets are files)
docker inspect andespadel-prod-backend \
  --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -Ei 'SECRET|STRIPE|PASSWORD|SMTP' | grep -v _FILE   # must print nothing

# the public surface
for p in /api/courts/ /api/club/ /api/auth/skill-levels/ /privacy /; do
  echo -n "$p -> "; curl -s -o /dev/null -w '%{http_code}\n' "https://app.andespadelclub.com$p"
done          # expect 200s; /adminpanel/ answers 302 (redirect to login)

# logs quiet, worker registered
docker logs andespadel-prod-backend 2>&1 | grep -Ei 'traceback|error' | tail -5
docker logs andespadel-prod-worker --tail 3

# data still the real thing
curl -s https://app.andespadelclub.com/api/club/            # daily_open/close
curl -s https://app.andespadelclub.com/api/courts/          # 4 courts
```

`python manage.py journey_check` runs the full customer journey but
**writes** to whatever database it points at. In production that creates
real rows; run it there only with the operator's go-ahead.

---

## 7. How these facts were verified (2026-10-15)

| Claim | Command |
|---|---|
| Host vhost contents | `cat /etc/nginx/sites-enabled/padelapp` |
| Container nginx running config | `docker exec andespadel-prod-nginx cat /etc/nginx/nginx.conf` |
| No drift between disk, running config and git | `md5sum` of both + `git status --porcelain docker/nginx/` (clean at `ebe5cfc`) |
| Port map | `docker port andespadel-prod-nginx` → `34003:80`; backend `34002:8000` |
| Code baked, not mounted | `docker inspect andespadel-prod-backend --format '{{.Config.Cmd}}'` |
| Privileges | `docker inspect … {{.Config.User}}` = `root`, but `docker/entrypoint.prod.sh` execs `gosu appuser` before anything from the app runs |
| Secrets are files, not env | `docker inspect … {{.Config.Env}}` + `ls -la /run/secrets` inside the container |
| Host nginx | `nginx -v` → 1.24 (Ubuntu); `systemctl is-active nginx` |

---

## 8. Known state at this audit

- Server checkout: `ebe5cfc`. Repository `main`: `9fd7597`. The delta is
  **not deployed**: nginx per-request resolution, the firebase mount target,
  the SQLite-path removal and the real-stack settings tests.
- `/opt/padelapp/docker/backend/` still exists on the server and is **dead**
  (nothing references it since the mounted-secrets cutover). Delete it once
  the pending changes are deployed and verified.
- Production's database password is unchanged from before the cutover and
  now lives only in `/opt/padelapp/docker/runsecrets/db-password`.
- `make mirror-verify` now works end to end (the production image carries
  `content_counts`).
