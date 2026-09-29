# AGENTS.md

Operating brief for AI agents and humans working in this repo. Read this before
touching anything. It encodes decisions that are not obvious from the code and
that have already been gotten wrong once.

---

## 1. What this is

**Andes Padel** — booking platform for a padel club in Guayaquil, Ecuador.

Three surfaces, one repo:

| Surface | Stack | Where |
|---|---|---|
| API + admin panel | Django 5.2 + DRF + SimpleJWT + Celery | `apps/`, `padel/` |
| Mobile app | Flutter 3.47 / Dart 3.13 | `mobile/` |
| Marketing site | Static HTML | `landing/` |

Postgres + Redis behind nginx. Compose-driven. Currency USD, timezone
`America/Guayaquil`, default language Spanish.

---

## 2. Non-negotiables

These are the rules that bite. Breaking them is a bug, not a style choice.

1. **Never commit secrets or build artifacts.** `.gitignore` covers Firebase
   config, keystores, `*.ipa`/`*.apk`, service accounts, `runsecrets/`. If you
   find one tracked, untrack it (`git rm --cached`) — do not delete the local
   copy, and say so in the commit message.
2. **Never show raw exceptions in the UI.** `e.toString()` / `DioException`
   dumps must not reach a screen. Route through
   `mobile/lib/core/friendly_error.dart` → `friendlyErrorMessage(err, l10n)`.
3. **Every user-facing string goes through i18n.** Flutter: `l10n.key`, and the
   key must exist in **all four** ARBs. Django: `gettext` / `gettext_lazy`.
   A key present in `en`/`es` but missing from `ca`/`pt` silently falls back to
   Spanish in the generated files — that is a bug users see.
4. **Never use `_` as a throwaway variable name in any module that calls
   gettext.** `_` is gettext. `_, created = ...` shadows it and every earlier
   `_("...")` in that function raises `UnboundLocalError`. Use `_player`,
   `_obj`, or similar.
5. **No Claude/AI attribution in commits or PRs.** No `Co-Authored-By`, no
   "Generated with", no session links. Commit as the configured git identity.
6. **Do not commit directly to `main` without being asked.** Branch first.
7. **Python side: `ruff check .` and `flake8 apps padel` must pass.**
   Flutter side: `flutter analyze` must report **No issues found!**

---

## 3. Architecture

### Django (`apps/` + `padel/`)

```
padel/settings/
  base.py       # INSTALLED_APPS, DRF/JWT/Celery/i18n. TIME_ZONE=America/Guayaquil
  dev.py        # DEBUG, CELERY_TASK_ALWAYS_EAGER
  prod.py       # HSTS/SSL + validate_production_secrets()
  local_sqlite.py  # overlay for docker-less tests
  _checks.py    # fail-fast secret validation
```

Apps fall into two kinds — keep the boundary clean:

- **HTTP apps** (have views/urls/serializers): `users`, `courts`, `bookings`,
  `payments`, `notifications`, `events`, `gdpr`, `reports`, `adminpanel`.
- **Library apps** (models + services only, no HTTP): `policies`, `pricing`,
  `scheduling`, `security`, `verification`, `common`.

Layering rule: **business logic belongs in `services.py`, not in views or
serializers.** Serializers validate and reshape; they should not write to the
DB or call Celery. Models should not fan out notifications.

Known violations (do not add more; fix when you touch the file):
- `apps/events/models.py` — `OpenMatch.notify_category` and `NewsPost.publish`
  fire Celery tasks from model methods.
- `apps/users/` has no `services.py`; auth flows live in serializers/views.
- `apps/adminpanel/` was a 1046-line monolith; it is now the `views/` package
  plus `mixins.py` for role scoping. Keep per-view modules focused.

### API surface

Mounted at `/api/` (**no version segment** — the SRS says `/api/v1/`, the code
does not). See `padel/urls.py`:

- `/api/auth/` — users + gdpr (login, register, verify, reset, devices, skill-levels)
- `/api/` — courts, bookings, payments, notifications, reports, events,
  tournaments, open-matches, news, club, banners
- `/api/webhooks/stripe/`
- `/adminpanel/` — server-rendered staff dashboard
- `/api/schema|docs|redoc/` — drf-spectacular

### Flutter (`mobile/lib/`)

```
core/      api_client, storage, friendly_error, form_validation, locale_controller,
           push_notification_service, theme, l10n, models/, widgets/
features/  auth/  booking/  bookings/  events/  home/  notifications/  profile/
shell/     app_shell.dart
```

`features/booking/` (the wizard + payment flow) and `features/bookings/` (the
list screen) are different folders. Confusing on purpose of history — do not
merge casually.

---

## 3b. Admin panel RBAC

Role hierarchy, low to high:

```
cliente < recepcionista < gerente < dueno < superadmin
```

Constants live in `apps/adminpanel/admin_base.py`:

| Constant | Roles |
|---|---|
| `STAFF_ROLES` | recepcionista, gerente, dueno, superadmin |
| `MANAGER_ROLES` | gerente, dueno, superadmin |
| `FINANCIAL_ROLES` | dueno, superadmin |

Gate whole views with `StaffRequiredMixin` / `ManagerRequiredMixin` /
`FinanceRequiredMixin`. When one view mixes routine and privileged `post()`
actions, call `require_roles(request, ROLES)` at the top of the handler — it
raises `PermissionDenied`. Do not swallow an authorization failure as
`messages.error` + redirect: that is a soft failure an attacker can script
around, and it does not show up as a 4xx in logs.

Action-level matrix (what each role may actually do):

| Action | recepcionista | gerente | dueno / superadmin |
|---|---|---|---|
| Calendar, courts, banners, events | yes | yes | yes |
| Create/cancel booking, block slot | yes | yes | yes |
| Confirm / reject bank transfer | **yes** | yes | yes |
| Record cash | yes | yes | yes |
| Refund | no | no | **yes** |
| Change a user's status (suspend/activate) | no | **yes** | yes |
| Change a user's role | no | no | **yes** |
| Club settings (bank details, policies) | no | no | **yes** |
| Audit log | no | no | **yes** |
| Reports — booking counts | no | **yes** | yes |
| Reports — revenue, per-court income, top customers | no | **restricted** | **yes** |
| Reports — CSV export (customer emails) | no | no | **yes** |

Design notes, so the next change does not undo them:

- **Transfer confirm/reject is front-desk work.** Receptionists verify the
  receipt at the counter and need to act; routing it through a manager just
  queues up people standing at the desk. It is reversible and non-financial.
- **Refund is not.** Refund moves money and is `FINANCIAL_ROLES` only.
- **Role changes refuse privilege escalation with 403**, not a flash message:
  a `dueno` cannot mint a `superadmin`, and nobody can assign a role above
  their own (`role_level`).
- **The last `superadmin` cannot be demoted.** Doing so would lock every
  privileged surface with no way back in.
- **Revenue is owner-only.** `ReportsAdminView` does not even compute the
  aggregates unless the role is in `FINANCIAL_ROLES`, so a template slip
  cannot leak them. Managers see booking counts and "Restringido".
- Django admin (`/admin/`) has its own gate: `RoleGatedAdmin` in
  `apps/adminpanel/admin_base.py`. It is coarser than the panel and should be
  tightened independently.

Payment service safety bounds (`apps/payments/services.py`) back the RBAC up,
because a handler can be reached from more than one view:

- `confirm_transfer` is **idempotent** and atomic — a double-click does not
  send two notifications or re-run the booking transition.
- `reject_transfer` refuses a payment that is no longer pending.
- `refund` refuses a non-positive amount, an amount above what was captured,
  and a second refund of the same payment. Amounts are coerced through
  `Decimal(str(...))` because `payment.amount` can arrive as a bare string.
- `_record_cash_payment` is wrapped in `transaction.atomic()`, so a failed
  `booking.transition_to("confirmed")` leaves no orphan `Payment` row.

---

## 4. Environments and ports

Three Docker Compose projects. **There is no port 8000.** Old docs that say
`localhost:8000` are stale.

| Env | Project | Ports | Compose | Make targets |
|---|---|---|---|---|
| dev | `andespadel` | 28000–28003 | `docker-compose.yml` + `docker-compose.dev.yml` | `up-dev`, `test-dev`, `fltest-dev`, `seeddemo-dev` |
| test | `andespadel-test` | 29000–29003 | + `docker-compose.test.yml` | `up-test`, `test-test`, `seeddemo-test` |
| prod | `andespadel-prod` | 34000–34003 | + `docker-compose.prod.yml` | `up-prod`, `down-prod` |

Port map within each env: `N000` db, `N001` redis, `N002` backend/API,
`N003` nginx.

- **API_DEV is `http://127.0.0.1:28002/api`** — this is also the default in
  `mobile/lib/core/api_client.dart`. Release builds must override with
  `--dart-define=API_BASE_URL=https://andespadel.yachaq.io/api`.
- `docker-compose.yml` must never be run alone; always pair with an env overlay
  and a `-p` project name.
- `compose.prod.yml` / `compose.server.yml` at the repo root are **legacy and
  unused** by the Makefile. Do not extend them.

---

## 5. Commands

```bash
make up-dev          # start dev stack
make test-dev        # pytest apps -q  (needs stack up)
make lint            # ruff check . && flake8 && bandit -r apps   (inside container)
make fltest-dev      # flutter test against the dev API
make flcheck         # flutter analyze
make flrun           # flutter run
make ship-ios        # TestFlight build + upload (needs ASC_USER/ASC_PASSWORD)
make seeddemo-dev    # demo data, password Andes12345!  — dev/test only, NEVER prod
```

Python lint on the host (faster than the container):

```bash
python3 -m ruff check .
python3 -m flake8 apps padel
```

Flutter, always with the full path and these flags:

```bash
cd mobile
/usr/local/bin/flutter analyze --no-version-check --suppress-analytics
/usr/local/bin/flutter test  --no-version-check --suppress-analytics \
  --dart-define=API_BASE_URL=http://127.0.0.1:28002/api
```

**Never use `~/development/flutter`** — the project's Flutter is
`/usr/local/bin/flutter` (3.47.1).

---

## 6. i18n rules

Four locales everywhere: **es, en, ca, pt**. Spanish is the default and the
fallback; device locale is deliberately ignored.

### Flutter

- ARBs live in `mobile/lib/core/l10n/app_{es,en,ca,pt}.arb`.
- `mobile/l10n.yaml` sets `template-arb-file: app_es.arb`.
- **Adding a key means adding it to all four ARBs in the same change.** Because
  the template is `app_es.arb`, a key missing from `ca`/`pt` compiles fine and
  shows **Spanish** to those users. This has already shipped once — the entire
  payment flow was Spanish for Catalan/Portuguese users.
- After editing ARBs run `flutter gen-l10n` and commit the regenerated
  `app_localizations*.dart`.
- Language endonyms in the profile picker (`Español`, `English`, `Português`,
  `Català`) are intentional and are **not** a translation miss.

### Django

- Catalogs in `locale/{es,en,ca,pt}/LC_MESSAGES/django.{po,mo}`.
- Wrap user-visible strings: `gettext as _` in views,
  `gettext_lazy as _` in models.
- Source strings are Spanish. After adding one:
  `python3 -m django makemessages -l es -l en -l ca -l pt`, translate the empty
  `msgstr`, then `msgfmt -o <po> <mo>`. Commit both `.po` and `.mo`.
- **msgid must match the source byte-for-byte**, accents included. A catalog
  entry of `Credenciales invalidas` does not match code that calls
  `_("Credenciales inválidas")`.
- **`gettext()` on a variable is not extractable.** `makemessages` only sees
  string *literals* passed to a recognized name (`gettext`, `gettext_lazy`,
  `gettext_noop`, `pgettext`, `_`). A table of literals localized later via
  `gettext(template[0])` is invisible to it: the msgids go obsolete (`#~`) and
  the strings ship untranslated in every language. Wrap the literals at
  definition time with `gettext_noop(...)` and call `gettext(...)` at render
  time. Spell out `gettext_noop` rather than aliasing it to `_` — `_` is
  gettext, and rebinding it is the shadowing trap above. See
  `apps/notifications/services.py` `MESSAGE_TEMPLATES`, which had exactly this
  bug: notification titles and bodies were English for every locale.
- Dict **keys** in such tables are event identifiers, not user-facing. Do not
  wrap them — a `gettext_noop("booking_confirmed")` key pollutes the catalog.
- Adminpanel templates are currently Spanish-only. Do not claim 4-language
  admin coverage in docs.

---

## 7. Testing

- Django tests: colocated per app (`apps/<app>/tests.py`, `tests_api.py`,
  `tests_auth.py`, `tests_security.py`). 215 tests. Need Postgres —
  `make up-dev && make test-dev`.
- Flutter tests: `mobile/test/`. **Hermetic** — `test/helpers/fake_api.dart`
  stubs `ApiClient`, so `flutter test` needs no Docker and no network. Failure
  injection is available (`FakeApi.offline = true`, bad password → real 401).
- Playwright E2E: `tests/e2e/` with its own `pytest.ini` — 111 admin + 28 auth
  tests. Separate from the Django suite.
- `AuthState.error(l10n)` takes `l10n` and maps through `friendlyErrorMessage`,
  so it is non-null exactly when `hasError` is. Do **not** use it as a success
  signal — assert `authenticated`, written tokens, or a call-log entry instead.
- Never assert `error, isNull` as proof that something worked.

---

## 8. Gotchas already hit

| Trap | Reality |
|---|---|
| `localhost:8000` | Does not exist. Use 28002 (dev) / 29002 (test) / prod URL. |
| `make seed-test` | Not a target. It is `seeddemo-test`. |
| `_ , created = Model.objects.get_or_create(...)` | Shadows gettext. Always. |
| `gettext(some_variable)` | Not extractable. Wrap the literal in `gettext_noop` where it is defined or `makemessages` marks it obsolete and it ships untranslated. |
| Adding an ARB key to `en`+`es` only | Ships Spanish UI to ca/pt users. |
| `firebase_options.dart` | Gitignored. Push is **optional**: without it the app still builds and runs, with push disabled. Run `flutterfire configure` to enable FCM. |
| `Manual_Usuario_AndesPadel.docx`, `images/Archive.zip` | Were tracked despite `*.docx`/`*.zip` in `.gitignore`. Ignore rules do not untrack. |
| `disenio ` (trailing space) | Accidental design-asset dump, also has `loos/` (typo for "logos"). Not code. |
| `apps/common/timefmt.py` | Was untracked while imported in 5 places. Commit files before pushing work that depends on them. |
| SRS (`docs/srs/`) | Requirements baseline, partially superseded. It says `/api/v1/`, 10-char passwords, partner-matching is v2 — none of which match the code. Treat as historical contract, not ground truth. |
| Password policy | SRS says 10+ with complexity; code is `min_length: 8`, no complexity validator. |

---

## 9. Docs map

Trust levels as of 2026-09-29:

- **Current:** `README.md`, `docs/DEPLOYMENTS.md`, `docs/BUILD_AND_DEPLOY.md`,
  `docs/SECURITY.md`, `TESTING_GUIDE.md`, `mobile/README.md`, `store/README.md`,
  this file.
- **Historical:** `docs/DEPLOYMENT_PLAN.md`, `docs/plans/`, `docs/srs/`.

Two facts still need operator confirmation and are marked `UNVERIFIED` in the
docs rather than guessed: the server IP (`140.82.15.48` vs `140.82.155.48`), and
whether a `resend` route should exist (there is currently none).

When you change a port, a make target, a URL, or add an API route, update
`docs/DEPLOYMENTS.md` and this file in the same commit.

---

## 10. Known debt (do not pretend it is not there)

Ordered by cost of ignoring it. Paid down on 2026-09-29; what remains:

1. **Dart lint rules parked at `ignore`.** `always_use_package_imports` (116
   hits), `require_trailing_commas` (79) and `unawaited_futures` (6) are
   enabled but severity-overridden in `mobile/analysis_options.yaml`. Sweep
   `lib/` and `mobile/test/widget_test.dart`, then flip them to `info`.
2. **`ruff format` is not enforced** — a large set of files would reformat.
   Either adopt it in one commit or stop checking it.
3. **`apps/.bandit` is load-bearing.** bandit does not read `pyproject.toml`;
   it only discovers a `.bandit` INI inside the scanned trees. Keep exactly one
   under `apps/`+`padel/` or bandit errors with "Multiple .bandit files found".
   B105/B106/B107 (password-shaped-string heuristics) are globally skipped
   because they fire on every test fixture; a real secret scanner is the right
   tool for credential leaks.
4. **Django admin RBAC is coarser than the panel.** `RoleGatedAdmin` is
   all-or-nothing per role in a way the custom panel is not. Split it the same
   way if staff are ever pointed at `/admin/`.
5. **Firebase API keys are still in git history** (`AIza...` for Android and
   iOS, from commit `d26820e`). Untracking did not erase them. **Decision
   (2026-09-29): do not rotate** — accepted as-is. Note this is a deliberate
   acceptance, not an expiry: Google API keys do not self-expire the way a
   time-boxed GitHub PAT does, so the exposure is open-ended until revoked.
   Do not re-raise as a new finding; it is a known, owned risk.
6. **Server IP is unverified** (`140.82.15.48` vs `140.82.155.48`).
7. **SRS (`docs/srs/`) still drifts** from the code (`/api/v1/`, password
   policy, partner-matching). Historical contract — do not treat as ground truth.
8. **`timezone.datetime` / `timezone.timedelta`** are gone from `apps/`, but
   they worked only because Django re-exports those stdlib names. Use
   `from datetime import datetime, timedelta`.

## 11. Commit style

Conventional prefixes, lowercase, imperative: `feat:`, `fix:`, `chore:`,
`docs:`, `test:`. Body explains *why*, not a count of files touched.

Do:
```
fix: shadowing gettext in open-match join

`_, created = get_or_create(...)` rebound `_`, so the error responses
above it raised UnboundLocalError instead of returning 409.
```

Do not:
```
fix: 15 critical production bugs found by AI audit (comprehensive)
feat: fix iOS build
```

Message counts ("N bugs fixed", "N tests added") and the word "comprehensive"
in a subject line are noise. Say what changed and why it matters.
