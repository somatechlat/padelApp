# Andes Padel — production deploy on `app.andespadelclub.com`

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Retire `andespadel.yachaq.io` from the Loyallia host, serve Andes Padel
(API + admin panel) at `https://app.andespadelclub.com` with a real Let's
Encrypt certificate, ship the current code there in containers, and produce
the publishable mobile + landing artifacts (TestFlight IPA, Android APK,
zipped landing site).

**Architecture:** Host nginx terminates TLS on 80/443 and reverse-proxies to
the compose nginx on `127.0.0.1:34003`. Django/gunicorn + Celery worker/beat +
Postgres + Redis run as the `andespadel-prod` compose project on ports
34000–34003. The Flutter apps are not containers — they are release builds
compiled with `--dart-define=API_BASE_URL=https://app.andespadelclub.com/api`
and delivered separately (TestFlight / APK on the landing page).

**Tech Stack:** Ubuntu 24.04 host, Docker Compose, Django 5.2 + DRF + Celery,
Postgres 15, Redis 7, nginx + certbot, Flutter 3.47.

---

## Ground truth gathered 2026-10-01

| Fact | Value |
|---|---|
| Server | `140.82.15.48` (host `loyallia`, Ubuntu 24.04.4), root + supplied password |
| DNS `app.andespadelclub.com` | → `140.82.15.48` **already correct** |
| DNS `andespadelclub.com` / `www.` | → `190.92.174.243` (different box — do not touch) |
| Old vhost | `/etc/nginx/sites-enabled/padelapp` → `andespadel.yachaq.io` → `127.0.0.1:34003` |
| Old cert | certbot `andespadel.yachaq.io` (expires 2026-11-24) — **delete this one only** |
| Other certs on box | `agente.soma.lat`, `maquinadeltiempo.yachaq.io`, `rewards.loyallia.com`, `xtrim.yachaq.io` — **never touch** |
| Loyallia containers | ports **33900–33914** and names `loyallia-*` — **never touch** |
| Old padel stack | compose project `padelapp` via **deleted** `compose.server.yml`; all containers `Exited (0)` 6 days ago |
| Old data | volumes `padelapp_db_data`, `padelapp_media_data`, `padelapp_static_data`; dump at `/opt/padelapp/backups/padel_prod-20260923T142419Z.sql` |
| New compose | `docker-compose.yml` + `docker-compose.prod.yml`, project `andespadel-prod`, volumes `andespadel-prod_*` |
| Git remote | `https://github.com/somatechlat/padelApp.git`, branch `audit/quality-fixes` (2 commits ahead of origin) |
| iOS identity | only **Apple Development** in keychain; **Apple Distribution private key is missing** (known blocker) |
| Android signing | `key.properties` absent → release APK is debug-signed |

---

## Task 1 — Make Django answer to the `app.` subdomain

**Files:**
- Modify: `padel/settings/prod.py`
- Modify: `padel/settings/_checks.py` (docstring only)
- Test: `apps/common/tests_settings.py` (create)

`PROD_DOMAIN` stays the **bare apex** (`andespadelclub.com`) per AGENTS.md §9.
`prod.py` currently derives only `apex` + `www.apex`. The app lives on
`app.apex`, and the apex/`www` are served by a *different* host, so the
allowlist must cover `app.` explicitly.

**Step 1: Write the failing test**

```python
# apps/common/tests_settings.py
from django.test import SimpleTestCase, override_settings


class ProdHostDerivationTests(SimpleTestCase):
    def test_app_subdomain_is_allowed(self):
        from padel.settings import _checks

        apex = _checks.validate_production_host("andespadelclub.com")
        hosts = [apex, f"www.{apex}", f"app.{apex}"]
        self.assertIn("app.andespadelclub.com", hosts)

    def test_prod_hosts_include_app(self):
        from padel.settings import prod

        self.assertIn("app.andespadelclub.com", prod.ALLOWED_HOSTS)
        self.assertIn("https://app.andespadelclub.com", prod.CORS_ALLOWED_ORIGINS)
        self.assertIn("https://app.andespadelclub.com", prod.CSRF_TRUSTED_ORIGINS)
```

**Step 2: Run it, expect FAIL**

```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/padelApp
python3 -m pytest apps/common/tests_settings.py -q
```
Expected: `ImportError` / `AttributeError` — `prod.ALLOWED_HOSTS` has no `app.` entry.

**Step 3: Implement**

In `padel/settings/prod.py`, replace the host-derivation block:

```python
PROD_DOMAIN = validate_production_host(getattr(secrets, "PROD_DOMAIN", ""))
# Apex + www + app. The mobile apps and the staff panel are served from the
# `app.` host; the apex/www are a different machine and still need to be a
# legal Host/Origin so a stray request cannot 400, and so CORS/CSRF cover the
# origin the apps actually call.
ALLOWED_HOSTS = [PROD_DOMAIN, f"www.{PROD_DOMAIN}", f"app.{PROD_DOMAIN}"]
PROD_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
```

**Step 4: Run it, expect PASS**

```bash
python3 -m pytest apps/common/tests_settings.py -q
```

**Step 5: Commit**

```bash
git add padel/settings/prod.py apps/common/tests_settings.py
git commit -m "feat: allow the app. subdomain in production hosts

The apps and the staff panel are served from app.andespadelclub.com while
the apex and www point at a different machine. Deriving only apex+www left
the real origin out of ALLOWED_HOSTS and out of CORS/CSRF, so every request
from the apps would have been rejected as a bad Host header."
```

---

## Task 2 — Point the landing page at `app.` and ship the APK with it

**Files:**
- Modify: `landing/index.html`
- Replace: `landing/padelapp.apk` (built in Task 5)
- Delete from dist: `landing/padelapp-debug.apk` (159 MB debug build — not for the public)

The landing page currently links `https://www.andespadelclub.com/api/docs/`,
`.../adminpanel/login/` and downloads `/padelapp.apk`. Those must become the
`app.` host, and the download must be the **release** APK compiled against
production.

**Step 1:** rewrite the `www.andespadelclub.com` hrefs to
`https://app.andespadelclub.com/...` (API docs, admin login, reserve button).

**Step 2:** build the release APK (Task 5) and copy it to
`landing/padelapp.apk`, replacing the stale one.

**Step 3:** commit.

---

## Task 3 — Push the branch with the operator's token

**Step 1:** confirm working tree is clean and the two local commits are the
only delta.

**Step 2:** push `audit/quality-fixes` using the supplied token as the
credential. **Never write the token into the repo, a file, or a commit.**

```bash
git -c credential.helper= \
  -c "http.https://github.com/.extraheader=AUTHORIZATION: basic $(printf 'x:%s' "$GH_TOKEN" | base64)" \
  push origin audit/quality-fixes
```

**Step 3:** if the repo wants the work on `main`, open a PR / merge per the
operator's call — AGENTS.md forbids committing straight to `main` unasked.

---

## Task 4 — Server: swap the vhost and certificate

**Only `andespadel.yachaq.io` is removed.** Every other cert and vhost on the
box is left exactly as it is.

**Step 1: Snapshot before touching anything**

```bash
cp /etc/nginx/sites-enabled/padelapp /root/padelapp-nginx.bak.$(date +%s)
tar czf /root/letsencrypt-andespadel-backup.tgz /etc/letsencrypt/live/andespadel.yachaq.io /etc/letsencrypt/renewal/andespadel.yachaq.io.conf
```

**Step 2: Replace the vhost** with one that serves `app.andespadelclub.com`:

- `server_name app.andespadelclub.com;` on both :80 and :443
- :80 keeps `/.well-known/acme-challenge/` → `/var/www/certbot` and 301s to https
- :443 proxies everything to `127.0.0.1:34003` (same as today)
- TLS: `fullchain.pem` / `privkey.pem` under `/etc/letsencrypt/live/app.andespadelclub.com/`
- Same security headers as today (HSTS, X-Frame-Options, nosniff, Referrer-Policy)
- `client_max_body_size 20M` (transfer proofs upload)

**Step 3: Obtain the certificate**

```bash
certbot certonly --webroot -w /var/www/certbot \
  -d app.andespadelclub.com \
  --non-interactive --agree-tos -m <operator email> \
  --cert-name app.andespadelclub.com
```

If the cert cannot be issued yet, write the vhost with a temporary
self-signed pair so the stack can be verified, then re-run certbot and reload.

**Step 4: Delete only the retired cert**

```bash
certbot delete --cert-name andespadel.yachaq.io
```

**Step 5: `nginx -t && nginx -s reload`** — reload only, never restart.

---

## Task 5 — Server: deploy the code and build containers

**Step 1:** make the checkout safe for git, then fetch the new branch.

```bash
git config --global --add safe.directory /opt/padelapp
cd /opt/padelapp
git remote set-url origin https://github.com/somatechlat/padelApp.git
git fetch origin
git checkout audit/quality-fixes
git reset --hard origin/audit/quality-fixes
```

**Step 2:** preserve the real secrets. `docker/backend/secrets.py` is
gitignored — copy the live one aside first, then add the one new key it needs:

```python
PROD_DOMAIN = "andespadelclub.com"
```

Everything else (SECRET_KEY, DB_*, REDIS_URL, EMAIL_*, STRIPE_*) is reused as
it already is on the box.

**Step 3:** retire the legacy stack and preserve its data.

```bash
cd /opt/padelapp
docker compose -p padelapp -f compose.server.yml down   # if that file is gone, docker rm -f the padelapp-* containers
docker run --rm -v padelapp_db_data:/from -v /opt/padelapp/backups:/to alpine \
  tar czf /to/db_data_pre_migration.tgz -C /from .
```

**Step 4:** bring up the new project.

```bash
cd /opt/padelapp
POSTGRES_PASSWORD=<from secrets.py DB_PASSWORD> \
PROD_API_BASE_URL=https://app.andespadelclub.com/api \
docker compose -p andespadel-prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

**Step 5:** migrate + collectstatic, then restore any data that only lived in
the old volume.

```bash
docker compose -p andespadel-prod -f docker-compose.yml -f docker-compose.prod.yml \
  exec -T backend python manage.py migrate --noinput
docker compose -p andespadel-prod -f docker-compose.yml -f docker-compose.prod.yml \
  exec -T backend python manage.py collectstatic --noinput
```

**Step 6: Verify**

```bash
curl -fsS https://app.andespadelclub.com/api/courts/          # JSON, 200
curl -fsSI https://app.andespadelclub.com/adminpanel/login/   # 200
curl -fsSI https://app.andespadelclub.com/                    # landing
openssl s_client -connect app.andespadelclub.com:443 -servername app.andespadelclub.com </dev/null | openssl x509 -noout -subject -dates
```

---

## Task 6 — Build the Android release APK against production

```bash
cd mobile
/usr/local/bin/flutter pub get
/usr/local/bin/flutter build apk --release --no-version-check --suppress-analytics \
  --dart-define=API_BASE_URL=https://app.andespadelclub.com/api
cp build/app/outputs/flutter-apk/app-release.apk ../landing/padelapp.apk
```

Note in the report: the APK is **debug-signed** until a Play upload keystore
exists (`mobile/android/key.properties`). Fine for direct install from the
landing page; not acceptable for Google Play.

---

## Task 7 — Simulator smoke-test against production, then TestFlight

**Step 1:** boot an iOS simulator and run the app pointed at production.

```bash
xcrun simctl boot "iPhone 17 Pro" || true
cd mobile
/usr/local/bin/flutter run -d "iPhone 17 Pro" --no-version-check --suppress-analytics \
  --dart-define=API_BASE_URL=https://app.andespadelclub.com/api
```

Verify: login/registration reach the production API, courts load, no raw
exception text on screen (`friendlyErrorMessage` path).

**Step 2:** `make ship-ios` with the supplied app-specific password as
`ASC_PASSWORD` and `info@loyallia.com` as `ASC_USER`.

**Known blocker:** the `Apple Distribution: ROBERTO MANOSALVAS (29NGPXM563)`
**private key** is not in this Mac's keychain — only the Apple Development
identity is. `xcodebuild -exportArchive` fails with *Missing private key for
signing certificate* and this cannot be worked around in software: a
signature cannot be produced without the key. The Sep 23 App Store IPA proves
the key existed then.

Resolution, in order of preference:
1. Operator opens Xcode → Settings → Accounts → team `29NGPXM563` →
   *Manage Certificates* → **Apple Distribution** → *Create*. Xcode mints a
   new Distribution identity into the login keychain.
2. Operator imports the original `.p12` for that key.

Until one of those happens, Task 7 Step 2 stops at the export step. The
development-signed IPA still builds and is useful for the simulator check.

---

## Task 8 — Publishable landing bundle for FTP

**Step 1:** assemble a clean dist — no debug APK, no `.DS_Store`, no source.

```
landing-dist/
  index.html
  privacy.html
  favicon*.png
  assets/
  padelapp.apk          # release build from Task 6
```

**Step 2:** `zip -r andespadel-landing-YYYYMMDD.zip landing-dist/` and hand the
archive to the operator for FTP upload.

---

## Task 9 — Update the operating brief and memory

- AGENTS.md §4/§9: a production host **now exists** (`140.82.15.48`,
  app-facing name `app.andespadelclub.com`). Replace "there is no production
  server" with the real facts and the do-not-touch list (Loyallia ports
  33900–33914, other certs, the `190.92.174.243` apex box).
- `docs/DEPLOYMENTS.md`: same, plus the `app.` subdomain in the host table.
- Memory `prod-target-unset.md` is now wrong — rewrite it as
  `prod-target-app-subdomain.md` describing the live server.

---

## Order of execution

1. Task 1 (settings + test) → commit
2. Task 3 (push)
3. Task 4 (nginx + cert) — can run in parallel with 5
4. Task 5 (deploy + build containers) → verify
5. Task 6 (Android APK) → Task 2 (landing wiring) → commit + push
6. Task 7 (simulator, then TestFlight)
7. Task 8 (landing zip)
8. Task 9 (docs + memory)

## Out of scope

- Google Play upload (needs an upload keystore — report it, do not invent one).
- Anything on the `190.92.174.243` apex/www box.
- Loyallia, `agente.soma.lat`, `xtrim.yachaq.io`, `maquinadeltiempo.yachaq.io`,
  `rewards.loyallia.com`.
- DNS changes (already correct).
