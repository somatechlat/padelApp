# Store publication blockers — design and change record

| Attribute | Value |
|-----------|-------|
| Project | Andes Padel — padel club booking platform |
| Document | Release-readiness remediation plan |
| Document ID | PADEL-PLN-004 |
| Version | 1.0 |
| Status | Approved for implementation |
| Date | 2026-10-03 |
| Standards | ISO 9001:2015 §7.5 (control of documented information) |
| Author | Product Engineering |
| Classification | Internal — Confidential |

---

## 1. Purpose

Bring the release pipeline into a state where an uploaded binary actually works
and where the store listings are submittable. This document is the change
record for that work, in the format established by `docs/srs/00-document-control.md`.

## 2. Verified baseline (2026-10-03)

Measured, not assumed:

| Fact | Evidence |
|------|----------|
| Production server **exists** | `app.andespadelclub.com` → `140.82.15.48`, Let's Encrypt `CN=app.andespadelclub.com`, valid 2026-10-01 → 2026-12-30 |
| Prod stack is running | `/opt/padelapp`, compose project `andespadel-prod`, up 2 days, `/etc/nginx/sites-enabled/padelapp` |
| API answers | `GET https://app.andespadelclub.com/api/courts/` → 200 |
| Privacy policy is live | `GET https://app.andespadelclub.com/privacy` → 200 |
| `www.andespadelclub.com/privacy` | **404** — different machine, `190.92.174.243`. Not provisioned to this operator |
| Store screenshots | `store/*/images/screenshots/` both **empty** |
| Built IPA | 2026-09-23, `CFBundleVersion` 6, `CFBundleDisplayName` "Padel App" |
| Built AAB | 2026-09-29, release-signed |
| Android AVD | `Medium_Phone_API_36` |
| iOS simulators | iOS 26.3 runtime only; iPhone 17 Pro Max available |

`AGENTS.md` §9 and §10.6, `README.md`, `mobile/README.md`, `TESTING_GUIDE.md`,
`docs/DEPLOYMENTS.md`, `docs/SECURITY.md` and `docs/DEPLOYMENT_PLAN.md` all
assert that no production server is provisioned. **That is false.** Those
documents are corrected under item 6.

## 3. Scope boundary

This server hosts several unrelated applications. Work is confined to:

- `/opt/padelapp` (the Andes Padel deploy)
- the `padelapp` host nginx vhost
- the `andespadel-prod-*` compose project

The `loyallia` and `soma-agent-zero` vhosts, and the `loyallia-*` containers
(`loyallia-web`, `loyallia-api`, `loyallia-postgres-replica`, `loyallia-pgbouncer`,
`loyallia-whatsapp-bridge`, `loyallia-grafana`, `loyallia-flower`,
`loyallia-celery-*`, `loyallia-redis-sentinel`, `soma-agent-zero`) are **out of
scope and must not be modified, restarted, or redeployed.**

## 4. Defects to correct

### D1 — Release builds ship a loopback API URL (critical)

`mobile/lib/core/api_client.dart:28` defaults `API_BASE_URL` to
`http://127.0.0.1:28002/api`. `mobile/tool/release_ipa.sh:34` builds without
`--dart-define`, and `store/README.md` documents the Play build the same way.
On a device `127.0.0.1` is the phone itself, so the shipped app cannot reach any
API. The comment in the source says release builds must pass the define; a
comment is not an enforcement.

**Correction.** Resolve the base URL through a single helper that throws in
release mode when the value is absent or loopback. Pass the define from the
release script and from the Makefile, with the production host as the default
in the release path.

### D2 — Android release signing fails open (critical)

`mobile/android/app/build.gradle:65` selects
`keystorePropertiesFile.exists() ? signingConfigs.release : signingConfigs.debug`.
With `key.properties` absent the build still succeeds and still produces a
signed AAB — signed by the debug key, which cannot be used for a Play update.
A CI box or fresh clone therefore ships a debug-signed artifact that looks
release-shaped.

**Correction.** Throw at configuration time when a release build has no
`key.properties`. Debug builds keep the debug key.

### D3 — `aps-environment` is hardcoded to `development` (critical)

`mobile/ios/Runner/Runner.entitlements:6` pins
`<string>development</string>`, and the same entitlements file is referenced by
the Debug, Profile **and** Release configurations. The distribution provisioning
profile grants `aps-environment = production`. No `APS_ENVIRONMENT` build
setting exists anywhere.

**Correction.** Use `$(APS_ENVIRONMENT)` in the entitlements file and define it
per configuration in `project.pbxproj`: `development` for Debug, `production`
for Profile and Release.

### D4 — Store metadata points at a 404 (blocker)

Eight files under `store/` reference `https://www.andespadelclub.com/...`,
which does not serve them. Both stores require a reachable privacy policy URL.

**Correction.** Repoint to `https://app.andespadelclub.com/...`, verified 200.

### D5 — Play short description exceeds the limit (blocker)

`store/google-play/listing/en-US/short-description.txt` is 89 characters and
`es-419` is 90. The Play Console limit is 80; the field will not save.

**Correction.** Shorten both to ≤ 80 characters without losing the value prop.

### D6 — Privacy policy is orphaned (minor)

`landing/index.html` contains no link to the policy.

**Correction.** Add one to the footer.

## 5. Deferred to later change requests

- Screenshot capture and the authenticated capture harness.
- Play upload tooling (none exists in this repo).
- Display-name alignment: listing says "Andes Padel", `Info.plist` says
  "Andes Padel Club", the built IPA says "Padel App".
- `andespadel-prod-backend` reports `unhealthy` (health check returns HTTP 400)
  while the API itself answers 200. Health-check definition is wrong, not the app.
- Publicly served build artifacts in `/opt/padelapp/landing/`:
  `padelapp-debug.apk` (56.9 MB), `padelapp-unsigned.ipa` (38.8 MB),
  `index.html.bak.20260917174315`.
- `landing/index.html` claims Quito; production is New Jersey.
- `mobile/tool/smoke_test.dart:11` uses `http://backend:8000/api`; no port 8000
  exists in any supported environment.
- Apple "App access" / demo credentials in `store/apple-app-store/review-notes.txt`.
- Play "Target audience and content" declaration.
- `docs/srs/` drift (`/api/v1/`, password policy, partner matching).

## 6. Verification

| Check | Command |
|-------|---------|
| Static analysis | `cd mobile && flutter analyze` → No issues found |
| Flutter tests | `cd mobile && flutter test` (hermetic, no Docker) |
| Python lint | `python3 -m ruff check . && python3 -m flake8 apps padel` |
| Fail-closed behaviour | release-mode base-URL guard raises; Android release config throws without `key.properties` |
| Live URLs | `curl -o /dev/null -w '%{http_code}'` against `/privacy`, `/`, `/api/courts/` |
| Metadata limits | character counts asserted ≤ 80 for Play short descriptions |

## 7. Change log

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-10-03 | Engineering | Initial issue. D1–D6 recorded from verified baseline. |
