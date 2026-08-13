# 03 — Functional Requirements (ISO/IEC/IEEE 29148 §5.4)

> Every functional requirement is listed by module. Each entry defines: **ID, name, description, actors, trigger, preconditions, postconditions, i18n status, ISO mapping.** Requirements marked **[v2]** are future scope, documented for completeness but excluded from the first release.

---

## M01 — Authentication & Identity

### F-0001 · User Registration
- **Description:** A guest creates a client account providing email (unique), full name, phone (optional), and password. A mandatory GDPR consent checkbox must be accepted. Email verification is sent (6-digit code).
- **Actors:** Guest. **Trigger:** Guest submits registration form.
- **Pre:** Email not already registered; consent accepted; password passes validators (NFR-0002).
- **Post:** User created with status `inactive`; verification code issued (expiry 15 min); user may log in only after verification (F-0003).
- **i18n:** All labels, errors, and the verification email are localized. **ISO:** 25010 (Functional suitability, Security), 27001 A.9.

### F-0002 · Login / Logout
- **Description:** Client logs in with email + password. Server issues JWT **access token (15 min)** and **refresh token (7 days, rotation, device-bound, revoked on reuse)**. Logout invalidates the refresh token.
- **Actors:** Any user. **Trigger:** Login form / logout action.
- **Pre:** Account active and email verified. **Post:** Tokens issued / refresh invalidated.
- **i18n:** N/A (system messages localized). **ISO:** 27001 A.9.2/A.9.4, OWASP API #2/#4.

### F-0003 · Email Verification
- **Description:** A 6-digit code sent by email verifies the address; max 5 attempts then code expires and a new one can be requested (rate-limited).
- **Actors:** Client. **Trigger:** Registration / resend request.
- **Pre:** Code valid and unexpired. **Post:** User status → `active`; email flagged verified.
- **i18n:** Email template and errors localized. **ISO:** 25010 Security, 27001 A.9.

### F-0004 · Password Reset
- **Description:** "Forgot password" sends a one-time reset link (expiry 30 min, single use). User sets a new password complying with validators.
- **Actors:** Guest/Client. **Trigger:** Reset request.
- **Pre:** Email exists (no account enumeration: identical response whether or not the email exists). **Post:** Password replaced; all refresh tokens revoked.
- **i18n:** Email and form localized. **ISO:** 27001 A.9.4, OWASP API #2.

### F-0005 · Change Password
- **Description:** Authenticated user changes password providing the current password; on success, all other sessions/refresh tokens are revoked.
- **Actors:** Client. **Trigger:** Profile action.
- **Post:** New password active; other devices logged out. **ISO:** 27001 A.9.4.

### F-0006 · Profile Management
- **Description:** User edits full name, phone, avatar image, and language preference (`language_code`). Booking history is read-only (F-0023).
- **Actors:** Client. **Post:** Profile updated; language preference immediately applied (M16).
- **i18n:** Preference stored and honored. **ISO:** 25010 Usability.

### F-0007 · Roles & Permissions (RBAC)
- **Description:** Five roles with a strict permission matrix enforced at every endpoint/action: `cliente`, `recepcionista`, `gerente`, `dueño`, `superadmin`. Permissions checked server-side, never by UI hiding alone.
- **Actors:** All. **ISO:** 27001 A.9.1/A.9.2, OWASP API #5.

### F-0008 · Account State Management
- **Description:** States `active | suspended | blocked | deleted`. Blocked after 5 consecutive failed logins (30-min lockout, configurable). Admin may suspend accounts (F-0052). Deleted = GDPR erasure (DT-0018).
- **Actors:** System, Admin. **ISO:** 27001 A.9, GDPR Art.17.

### F-0009 · Session & Device Management
- **Description:** User lists active devices/sessions; can revoke any session remotely.
- **Actors:** Client. **ISO:** 27001 A.9.

### F-0010 · Social Login **[v2]**
- **Description:** Google / Apple Sign-In linking to the same user model. **ISO:** 27001 A.9.4.

---

## M02 — Court Management

### F-0011 · Court CRUD
- **Description:** Admin creates, reads, updates, archives courts: name, number, venue/sede, court type, images, and status. Archiving disables new bookings but preserves history.
- **Actors:** Gerente, Dueño, Superadmin. **ISO:** 25010 Functional suitability.

### F-0012 · Court Types
- **Description:** Court classified `techada | abierta`; flag `has_lighting` (nocturnal). Both feed pricing multipliers (F-0029) and availability display.
- **Actors:** Admin. **ISO:** 25010 Functional suitability.

### F-0013 · Court Status
- **Description:** Status `available | maintenance | blocked | in_use`. Only `available` courts appear in public availability.
- **ISO:** 25010 Reliability.

### F-0014 · Operating Schedule
- **Description:** Per-court opening/closing times per weekday, plus holiday overrides. Schedule feeds slot generation (F-0013→F-0015).
- **Actors:** Admin. **ISO:** 25010 Functional suitability.

### F-0015 · Recurring Maintenance Windows
- **Description:** Auto-recurring blocked windows (e.g., daily cleaning 12:00–12:30) that exclude slots (F-0013) and cannot be booked.
- **Actors:** Admin. **ISO:** 25010 Reliability.

---

## M03 — Scheduling & Availability

### F-0016 · Slot Generation
- **Description:** Slots of 30-minute granularity generated from operating schedule and duration rule; valid durations 60/90/120 min (configurable). Slots only exist for future times.
- **ISO:** 25010 Functional suitability.

### F-0017 · Real-time Availability
- **Description:** Endpoint returns free slots for a court/date: excludes booked, held (F-0019), blocked, maintenance, past, and archive. Response localized (dates/times).
- **Actors:** All. **i18n:** Times in venue TZ, localized format. **ISO:** 25010 Performance, Usability.

### F-0018 · Manual Slot Blocking
- **Description:** Admin blocks arbitrary date/time ranges with a reason (visible in audit). Blocks take effect immediately and cancel any affected holds.
- **Actors:** Recepcionista, Gerente, Dueño. **ISO:** 27001 A.12 audit.

### F-0019 · Booking Hold (Soft-reserve)
- **Description:** On checkout, chosen slots are held for 10 minutes while payment is pending; a failed/abandoned payment auto-releases the hold. A user cannot hold more slots than their pending bookings allow (anti-hoarding).
- **ISO:** 25010 Reliability; concurrency safety.

### F-0020 · Conflict Prevention (Race-free)
- **Description:** Booking creation runs in a DB transaction using `select_for_update()` on slot rows; unique constraints on (court, slot, date); double-booking is impossible at DB level.
- **ISO:** 25010 Reliability, 27001 A.12.

---

## M04 — Booking Engine

### F-0021 · Booking Creation
- **Description:** Client selects court + date + consecutive slots (valid duration). System shows a price breakdown (F-0030), then creates `pending_payment` with holds (F-0019), then payment (M06) finalizes to `confirmed`.
- **Actors:** Cliente. **Trigger:** Checkout. **Pre:** Authenticated, slots free, duration valid. **Post:** Booking `pending_payment`; holds active; invoice draft.
- **i18n:** Price breakdown localized (currency, number, units). **ISO:** 25010 Usability.

### F-0022 · Booking State Machine
- **Description:** Legal transitions enforced:
  `pending_payment → confirmed → completed`
  `pending_payment → cancelled` (system/timeout)
  `confirmed → cancelled` (policy F-0041/F-0042)
  `confirmed → no_show` (F-0043)
  No other transition is permitted; every transition is recorded (F-0067).
- **ISO:** 25010 Functional correctness, 27001 A.12.

### F-0023 · Booking History
- **Description:** Paginated lists: `upcoming`, `past`, `cancelled` with full detail (court, slots, price, payment state, invoice). Read-only for clients.
- **Actors:** Cliente, Admin (all users' bookings). **ISO:** 25010 Usability.

### F-0024 · Modify / Reschedule Booking
- **Description:** Reschedule time or court if ≥24h before start and target slots are free; price difference is charged or refunded (M06). History retains the change (audit).
- **Actors:** Cliente, Admin. **ISO:** 25010 Functional suitability.

### F-0025 · Cancel Booking (user)
- **Description:** Client cancels applying the policy (F-0041/F-0042). Refund/penalty calculated and executed automatically where possible.
- **Actors:** Cliente. **ISO:** 25010 Functional suitability.

### F-0026 · No-show Workflow
- **Description:** Admin marks no-show (auto-suggested 30 min after start); triggers penalty (F-0043), notification (M08), and closes the booking.
- **Actors:** Recepcionista, Gerente. **ISO:** 25010 Functional suitability.

### F-0027 · Concurrent-User Handling
- **Description:** If a slot was taken during checkout, the user receives a graceful localized error ("Slot just taken, choose another") and can re-select; no partial writes.
- **ISO:** 25010 Reliability, Usability.

### F-0028 · Invoice Generation
- **Description:** PDF receipt auto-generated on `completed` with items, taxes, payments, invoice number (sequential, per venue).
- **ISO:** 9001 records, 25010 Usability.

---

## M05 — Pricing Engine

### F-0029 · Tariff Model
- **Description:** Price = base tariff (per court type per hour) × time-zone multiplier × day multiplier × court multiplier (techada +15%, lighting +10%, defaults configurable). All multipliers configurable; every price change audited.
- **ISO:** 25010 Functional correctness, 27001 A.12.

### F-0030 · Price Preview API
- **Description:** Client receives a full line-item breakdown (base, surcharges, taxes, total) before committing to pay. Server computes prices — the client never sends prices.
- **ISO:** 25010 Usability, Security (server-authoritative pricing).

### F-0031 · Time-of-Day Zones
- **Description:** `valle | pico` zones with configurable hour ranges per weekday/weekend.
- **ISO:** 25010 Functional suitability.

### F-0032 · Day Multipliers
- **Description:** Weekday vs weekend vs holiday multipliers; holiday calendar configurable by admin.
- **ISO:** 25010 Functional suitability.

### F-0033 · Promotions **[v2]** — %/absolute discounts with validity windows.
### F-0034 · Coupons **[v2]** — one-time/global codes with usage limits.

---

## M06 — Payments & Billing

### F-0035 · Payment Methods
- **Description:** (a) Card via **Stripe** (incl. Apple/Google Pay); (b) bank transfer → status `pending_transfer`, admin-confirmed (F-0053); (c) cash at venue → recorded by receptionist. Card data never touches our servers (Stripe Elements) (C11).
- **ISO:** PCI-DSS scope minimization, 27001 A.10.

### F-0036 · Payment Lifecycle
- **Description:** States `authorized → captured → paid | refunded | failed | voided`. Server verifies webhook (signature-verified) and reconciles.
- **ISO:** 25010 Reliability.

### F-0037 · Deposit Capture
- **Description:** Card authorized at booking; captured on booking start (completion); no-show penalty charged separately (F-0043). Failed capture triggers notification and admin task.
- **ISO:** 25010 Reliability.

### F-0038 · Refunds
- **Description:** Full/partial refunds per policy (F-0041/F-0042), triggered automatically by cancellation or manually by gerente/dueño. Refund issued to original payment instrument.
- **ISO:** 25010 Functional correctness.

### F-0039 · Receipts & Payment History
- **Description:** Every payment recorded with method, status, timestamps, and linked invoice; client can download receipts.
- **ISO:** 25010 Usability, 9001 records.

### F-0040 · Reconciliation Report **[admin]**
- **Description:** Stripe payouts vs recorded payments reconciled; discrepancies flagged for the owner.
- **ISO:** 9001 records.

---

## M07 — Cancellation & Penalties

### F-0041 · Cancellation Policy Configuration
- **Description:** Configurable: free-cancel window (default ≥24h), penalty % inside window (default 50%), no-show penalty (default 100%), hold duration (F-0019).
- **ISO:** 25010 Configurability.

### F-0042 · Penalty Calculation
- **Description:** Server computes penalty on booking total at the moment of cancellation using server time (client clocks are never trusted).
- **ISO:** 25010 Correctness.

### F-0043 · No-show Detection & Charging
- **Description:** 30 min after start, admin gets an action prompt; confirmation marks `no_show`, charges penalty via captured card, and notifies the user (M08).
- **ISO:** 25010 Reliability.

### F-0044 · Timezone Authority
- **Description:** All cutoff computations use UTC server time; the user's local timezone is display-only (A-trust rule). See NFR-0005.
- **ISO:** 25010 Correctness.

---

## M08 — Notifications

### F-0045 · Event Triggers
- **Description:** Events: booking confirmed, reminder (24h and 2h before), cancellation (user & admin), no-show penalty, payment success/failure, transfer confirmed, booking modified.
- **ISO:** 25010 Functional suitability.

### F-0046 · Channels
- **Description:** Push (FCM/APNS), email (transactional templates), in-app notification center. Each event maps to a configurable channel set.
- **ISO:** 25010 Usability.

### F-0047 · Preference Management
- **Description:** Per-event, per-channel opt-in/opt-out for clients; admins receive operational notifications by role.
- **ISO:** GDPR Art.7 consent for marketing only; transactional messages not opt-outable.
- **i18n:** All templates localized in user's language.

### F-0048 · Delivery Queue
- **Description:** Celery async dispatch with retries and exponential backoff; idempotency keys prevent duplicate sends.
- **ISO:** 25010 Reliability.

### F-0049 · Local Reminders **[v2]** — offline scheduled local push (requires offline mode).

---

## M09 — Web Admin Panel

### F-0050 · Dashboard
- **Description:** Today's bookings, occupancy %, revenue today, upcoming bookings, alerts (pending transfers, pending no-shows, conflicts).
- **Actors:** All admin roles (content filtered by role). **ISO:** 25010 Usability.

### F-0051 · Calendar View
- **Description:** Court × time grid; click a free slot to create a booking; drag to block (F-0018); edit/cancel bookings inline. All actions role-checked.
- **Actors:** Recepcionista, Gerente, Dueño. **ISO:** 25010 Usability.

### F-0052 · User Management
- **Description:** Search, view, suspend/unsuspend, assign roles, reset passwords, view per-user bookings. Role assignment limited to dueño/superadmin.
- **ISO:** 27001 A.9.

### F-0053 · Payment Management
- **Description:** Confirm bank transfers, record cash payments, issue refunds, view payment failures.
- **ISO:** 25010 Functional suitability.

### F-0054 · Audit Viewer
- **Description:** Read-only view of the audit log (F-0067) filtered by entity/actor/date; non-modifiable.
- **ISO:** 27001 A.12.4.

### F-0055 · Settings Management
- **Description:** Operating schedule, tariffs, multipliers, holiday calendar, cancellation policy, notification templates, hold duration. Only dueño/superadmin modify; all changes audited.
- **ISO:** 25010 Configurability, 27001 A.12.

### F-0056 · Role-Based Access in Admin
- **Description:** Recepcionista cannot see revenue/financial reports; gerente cannot manage roles; enforced server-side.
- **ISO:** 27001 A.9.

### F-0057 · Language Switch
- **Description:** Per-user language override in admin chrome; honors Django's locale middleware order (user → session → cookie → Accept-Language → default).
- **i18n:** Full admin translations via Django `locale/` catalogs.
- **ISO:** 25010 Usability.

---

## M10 — Reports & Analytics

### F-0058 · Revenue Report
- **Description:** Revenue by day/week/month, by court, by payment method; filters + CSV/PDF export. Restricted to gerente/dueño.
- **ISO:** 25010 Usability.

### F-0059 · Occupancy Report
- **Description:** Utilization % per court/slot/period from confirmed bookings.
- **ISO:** 25010 Usability.

### F-0060 · Frequent Customers
- **Description:** Top clients by bookings and spend; exportable.
- **ISO:** GDPR-compliant aggregation (no extra personal data).

### F-0061 · Cancellation & No-show Report
- **Description:** Rates and penalty revenue per period.
- **ISO:** 25010 Usability.

### F-0062 · Time-series Charts
- **Description:** Dashboard widgets with date-range filters; chart data endpoints backed by aggregate queries.
- **ISO:** 25010 Performance.

---

## M11 — Eventos & Torneos (Events & Tournaments)

> Added to v1 per the **Andes Pádel proposal** (Módulo de Eventos: publication of events, tournaments, and news/activities).

### F-0097 · Event Publication
- **Description:** Admin creates and publishes events (e.g., exhibition matches, clinics, social days): title, description, date/time range, venue/court link, cover image, category, and visibility. Unpublished events are visible only to admin (draft state).
- **Actors:** Recepcionista (create/update), Gerente/Dueño (publish/unpublish).
- **Trigger:** Admin submits event form. **Post:** Event `draft → published`; appears in app feed (F-0102); optional notification broadcast (F-0101).
- **i18n:** Event fields localized (title/description translatable per locale).
- **ISO:** 25010 Functional suitability.

### F-0098 · Tournament Publication
- **Description:** Admin creates tournaments: name, modality (2/4 players), category, start date, registration deadline, number of pairs/capacity, price per pair (optional), rules (rich text), prizes. Status: `draft | open | closed | in_progress | finished`.
- **Actors:** Gerente, Dueño. **Trigger:** Admin form. **Post:** Tournament visible in app; registration opened/closed per deadline.
- **i18n:** Localized. **ISO:** 25010 Functional suitability.

### F-0099 · Tournament Registration (Player)
- **Description:** Client registers to an open tournament providing pair partner info (or requests partner matching **[v2]**); creates registration record with payment link (if priced) — reuses M04/M06 engines.
- **Actors:** Cliente. **Post:** Registration `pending_payment → confirmed`; capacity check enforced; waitlist if full **[v2]**.
- **ISO:** 25010 Functional correctness.

### F-0100 · News & Announcements
- **Description:** Admin publishes news/announcements (novedades y actividades de las canchas): title, body, image, pinned flag, publish date. Sorted feed in app.
- **Actors:** Recepcionista, Gerente, Dueño. **ISO:** 25010 Functional suitability.

### F-0101 · Event Notifications
- **Description:** On publish of event/tournament/news, subscribers receive in-app + (opt-in) push/email broadcast per F-0047 preference. Reminder before an event the user registered for.
- **ISO:** GDPR Art.7 (marketing opt-in), 25010 Usability.

### F-0102 · Events Feed (Mobile)
- **Description:** App "Events" area: upcoming events, tournaments (open registration), news; detail views with register CTA; filters by category; localized.
- **i18n:** Localized. **ISO:** 25010 Usability.

### F-0103 · Event Administration
- **Description:** Admin dashboard section: list/search events & tournaments, capacity management, view registrations, publish/unpublish, cancel an event (notification to registrants + refund where applicable).
- **ISO:** 25010 Usability, 27001 A.9 RBAC.

---

## M12 — Loyalty & Gamification **[v2 Module]**

- **F-0063 · Points Accrual:** points per booking / per USD.
- **F-0064 · Rewards Catalog:** free slot, discounts, badge tiers.
- **F-0065 · Player Groups:** group creation, invites, split bookings.
- **F-0066 · Partner Matching:** open-pool to find a 4th player.

> Documented for completeness. **Excluded from v1.**

---

## M13 — Security & Audit

### F-0067 · Audit Log
- **Description:** Immutable append-only log recording actor, action, entity, before/after (for sensitive fields), timestamp, IP. Written on: authentication events, all booking transitions, payments, refunds, price changes, role changes, user suspensions, settings changes. Read-only API for gerente/dueño.
- **ISO:** 27001 A.12.4, OWASP API #9.

### F-0068 · Input Validation
- **Description:** Serializer-level validation on all inputs: type, length, range, format; strict max lengths; no raw SQL; parameterized ORM queries. (OWASP API #3.)
- **ISO:** 27001 A.14.

### F-0069 · Rate Limiting
- **Description:** Per-IP/per-user throttles: auth endpoints (e.g., 5/min), booking/payment (e.g., 20/min), generic API (e.g., 100/min). Configurable; 429 responses localized.
- **ISO:** 27001 A.12, OWASP API #4.

### F-0070 · Transport & Data Security
- **Description:** TLS 1.2+ only; HSTS in prod; secure/HttpOnly/SameSite cookies; `SECURE_*` suite (NFR-0005); sensitive fields encrypted at rest with Fernet where required (DT-0016); secrets never logged.
- **ISO:** 27001 A.8/A.10/A.13.

### F-0071 · Privacy / GDPR
- **Description:** Consent records with timestamp/version; `export-my-data` (JSON, 30 days); right-to-be-forgotten → anonymized cascade erase (DT-0018); minimal data collection; data-retention schedule (DT-0017).
- **ISO:** GDPR Art.5/7/15/17.

### F-0072 · Token Security
- **Description:** JWT access 15 min; refresh rotation + reuse detection (revoke family); revocation on password change/reset; device-bound tokens; blacklist storage in Redis.
- **ISO:** 27001 A.9, OWASP API #2.

---

## M14 — API Gateway

### F-0073 · Versioned REST API
- **Description:** Base path `/api/v1/`; resource namespaces: `auth`, `me`, `courts`, `availability`, `bookings`, `payments`, `notifications`, `reports`, `admin` (role-gated). Version pinned in URL; future breaking changes bump to v2.
- **ISO:** 25010 Compatibility.

### F-0074 · API Documentation
- **Description:** Auto-generated OpenAPI/Swagger UI (drf-spectacular); every endpoint documented with request/response schemas and auth requirements.
- **ISO:** 25010 Maintainability.

### F-0075 · Unified Error Envelope
- **Description:** All errors `{ "error": { "code", "message", "field_errors"?, "detail"? } }`; codes stable; messages localized via `Accept-Language`.
- **i18n:** Message localization. **ISO:** 25010 Usability.

### F-0076 · Pagination
- **Description:** List endpoints support `page`/`page_size` (default 20, max 100) or cursor for high-volume lists; consistent metadata shape.
- **ISO:** 25010 Performance.

### F-0077 · Health & Readiness
- **Description:** `/api/v1/health/` returns DB/Redis reachability; used by deployment checks.
- **ISO:** 25010 Reliability.

### F-0078 · Webhooks **[v2]** — Stripe signature-verified webhook endpoint (documented; v1 polls Stripe API instead).

---

## M15 — Flutter Mobile App

### F-0079 · Onboarding & Navigation
- **Description:** App shell with bottom navigation: Home (courts), Bookings, Events, Notifications, Profile. Onboarding screen for guests (register/login CTA). Localized at runtime.
- **i18n:** ARB-based, locale switch in settings. **ISO:** 25010 Usability.

### F-0080 · Auth Screens
- **Description:** Login, register (consent checkbox), verify code, password reset, change password. Tokens in secure storage (C12).
- **ISO:** 27001 A.9.

### F-0081 · Court List & Detail
- **Description:** List courts with type/lighting/images; detail with schedule and availability picker.
- **i18n:** Localized labels. **ISO:** 25010 Usability.

### F-0082 · Booking Wizard
- **Description:** Step flow (4 steps): date → time (30-min slots, duration selector) → summary/price → payment → confirmation. Court is selected on the Court Detail screen before entering the wizard. Step state restored on app restart (draft saved).
- **ISO:** 25010 Usability.

### F-0083 · Payment Screens
- **Description:** Stripe card (Elements), transfer instructions, cash option note; payment status results; failure recovery with hold re-validation.
- **ISO:** PCI scope minimized.

### F-0084 · My Bookings
- **Description:** Upcoming/past/cancelled lists; detail view; cancel/reschedule actions (per policy); invoice download link.
- **ISO:** 25010 Usability.

### F-0085 · Profile & Settings
- **Description:** Profile edit (F-0006), language selector, notification preferences, device management, export-my-data, delete-my-account (GDPR).
- **i18n:** Runtime language switch (no restart). **ISO:** GDPR, 25010 Usability.

### F-0086 · Push & Deep Links
- **Description:** FCM registration with token refresh; taps deep-link to the relevant booking, event, or notification detail screen.
- **ISO:** 25010 Usability.

### F-0087 · Events Feed (Mobile)
- **Description:** App "Events" tab: list upcoming events, tournaments with open registration, news; detail views with register CTA; filters by category; localized. See F-0102.
- **i18n:** Localized. **ISO:** 25010 Usability.

### F-0088 · Cache & Resilience
- **Description:** Court list and own bookings cached; offline banner; queued actions sync **[sync v2]**; graceful error states (localized) for all API failures.
- **ISO:** 25010 Reliability.

### F-0089 · Platform Security
- **Description:** Secure storage (Keychain/Keystore), HTTPS pinning, no logging of tokens/payments, biometric unlock **[v2]**.
- **ISO:** 27001 A.8/A.10.

---

## M16 — Internationalization (Cross-cutting Module)

### F-0092 · Locale Set & Resolution
- **Description:** Locales v1: `es` (default), `en`, `pt`, `ca`. Resolution order (web/admin): user preference → session → cookie → `Accept-Language` → default. App: stored device preference → device locale → default.
- **ISO:** 25010 Usability/Compatibility, 9001 documented process.

### F-0093 · Backend i18n
- **Description:** All user-facing strings via `gettext_lazy()`/`pgettext`; message catalogs in `locale/<lang>/LC_MESSAGES/django.po`; `LocaleMiddleware` active; DRF validation/error messages localized.
- **ISO:** 25010 Usability.

### F-0094 · Number, Date, Currency Localization
- **Description:** `USE_L10N=True`, localized formats (`USE_THOUSAND_SEPARATOR`, `NUMBER_GROUPING`), currency formatting per locale, dates/times in venue TZ with localized patterns.
- **ISO:** 25010 Usability.

### F-0095 · Flutter i18n
- **Description:** `flutter_localizations` + ARB files mirroring the locale set; `Intl` for date/number/currency; app-level locale controller with runtime switching.
- **ISO:** 25010 Usability.

### F-0096 · i18n Governance
- **Description:** No hardcoded user-facing strings allowed (lint enforced); extraction pipeline (`makemessages`); translation review process (ISO 9001); glossary of domain terms per language.
- **ISO:** 9001, 25010 Maintainability.

---

## M17 — Class Booking **[v2 Module]**

- **F-0104 · Instructor Directory:** profile, rating, availability.
- **F-0105 · Class Creation:** session types (privada/grupo), capacity, price.
- **F-0106 · Class Booking & Cancellation:** reuses M04/M06/M07 engines.

> Documented for completeness. **Excluded from v1.**

---

## Cross-cutting Rules (apply to all modules)

| Rule | Detail |
|------|--------|
| **Timezone** | All times UTC in DB; venue TZ configured per venue; client TZ display-only. |
| **Concurrency** | Booking operations transactional with `select_for_update`; unique constraints; retry-safe. |
| **Server authority** | Prices, availability, and policy cutoffs always computed server-side. |
| **Error handling** | Unified envelope (F-0075); localized messages; idempotency where applicable. |
| **Testing** | Every requirement has a test case (TC-xxxx) in `08`; no code without tests (C10). |
