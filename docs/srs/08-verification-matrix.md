# 08 — Verification Matrix

> For every v1 requirement, defines the **test case ID (TC-xxxx)**, **verification method**, and **acceptance criteria**. Methods: T=Automated test (unit/integration), S=Static/scan (lint, security scan, coverage), M=Manual/operational test, D=Demo/inspection (acceptance). TC IDs match the Traceability Matrix (`07`).

---

## 8.1 Methods Reference

| Method | Tool / Approach |
|--------|-----------------|
| **T** (unit) | Django `TestCase` / pytest on services, models, serializers |
| **T** (integration) | DRF `APITestCase`, DB transactions, Celery `task_always_eager` |
| **T** (e2e Flutter) | Flutter widget + integration tests |
| **T** (load) | Load test (e.g., locust) per NFR-0011/0012 |
| **S** | flake8/ruff, bandit, `dart analyze`, coverage gate, secret scan |
| **M** | Manual test script / production smoke test |
| **D** | Stakeholder demo, sign-off |

---

## M01 — Authentication & Identity

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0001 | TC-0001 | T (unit+int) | Registration creates inactive user; consent required; duplicate email rejected with localized error; verification code issued; code expires 15 min |
| F-0002 | TC-0002 | T (int) | Login issues access (15 min) + refresh (7 days); refresh rotates; reuse detection revokes family; logout invalidates refresh; lockout after 5 failures (30 min) |
| F-0003 | TC-0003 | T (int) | Correct code → `active`; 5 wrong attempts → code invalid; resend rate-limited |
| F-0004 | TC-0004 | T (int) | Reset link single-use, 30-min expiry; identical response for unknown email (no enumeration); all sessions revoked |
| F-0005 | TC-0005 | T (int) | Current password required; wrong → error; success revokes other tokens |
| F-0006 | TC-0006 | T + M | Profile fields update; language preference honored immediately; history read-only |
| F-0007 | TC-0007 | T (int) | RBAC matrix: every role × endpoint action passes expected allow/deny; server-side enforced |
| F-0008 | TC-0008 | T (int) | Suspend blocks login; blocked after 5 failures; deleted = anonymized |
| F-0009 | TC-0009 | T (int) | Device list accurate; revoke kills that session only |
| F-0010 [v2] | — | — | — |

## M02 — Court Management

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0011 | TC-0011 | T + M | CRUD works; archived court excluded from new bookings; history preserved |
| F-0012 | TC-0012 | T | Type/lighting values persisted; pricing multipliers applied from type |
| F-0013 | TC-0013 | T | Only `available` courts appear publicly; status changes block booking |
| F-0014 | TC-0014 | T | Per-weekday schedule drives slot generation; holiday override respected |
| F-0015 | TC-0015 | T | Recurring window blocks slots on every affected day |

## M03 — Scheduling & Availability

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0016 | TC-0016 | T | Slots generated at 30-min granularity; valid durations 60/90/120; no past slots |
| F-0017 | TC-0017 | T + load | Correct free slots excluding booked/held/blocked/maintenance/past; p95 < 300 ms |
| F-0018 | TC-0018 | T | Block overrides holds; reason recorded in audit |
| F-0019 | TC-0019 | T | Hold 10 min; auto-release on failure; anti-hoarding limit enforced |
| F-0020 | TC-0020 | T (concurrency) | 50 parallel booking attempts on same slot → exactly 1 success; no double-booking in DB |

## M04 — Booking Engine

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0021 | TC-0021 | T (int) | Creates pending_payment with holds; price breakdown shown; slots consecutive & same court |
| F-0022 | TC-0022 | T | Only legal transitions; illegal transition rejected; every transition logged |
| F-0023 | TC-0023 | T | Paginated lists correct; client sees only own bookings; admin sees all (role-gated) |
| F-0024 | TC-0024 | T | Reschedule allowed ≥24h & slots free; price diff charged/refunded; audited |
| F-0025 | TC-0025 | T | Cancel applies policy; refund/penalty computed correctly |
| F-0026 | TC-0026 | T | No-show suggestion 30 min after start; confirm closes booking + penalty |
| F-0027 | TC-0027 | T + M | Slot-taken error localized and re-selectable; no partial state |
| F-0028 | TC-0028 | T + M | PDF invoice with correct items/total/invoice number; tax 0% (RIMPE) |

## M05 — Pricing Engine

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0029 | TC-0029 | T | Formula correct for all combinations; changes audited |
| F-0030 | TC-0030 | T | Server-computed breakdown; client-supplied price ignored (security test) |
| F-0031 | TC-0031 | T | Zone boundaries respected (valle/pico) |
| F-0032 | TC-0032 | T | Weekday/weekend/holiday multipliers applied; holiday calendar honored |
| F-0033/34 [v2] | — | — | — |

## M06 — Payments & Billing

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0035 | TC-0035 | T + D | Card via Stripe (test mode); transfer marked pending; cash recorded; no card data in our DB (scan) |
| F-0036 | TC-0036 | T | Lifecycle transitions correct; failures handled idempotently |
| F-0037 | TC-0037 | T | Authorize at booking; capture at start; penalty capture on no-show |
| F-0038 | TC-0038 | T | Full/partial refund to original instrument; audited |
| F-0039 | TC-0039 | T + M | Receipt history complete; downloadable |
| F-0040 | TC-0040 | T | Reconciliation matches Stripe payouts; discrepancies flagged |

## M07 — Cancellation & Penalties

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0041 | TC-0041 | T | Config values honored; defaults 24h/50%/100%/10min |
| F-0042 | TC-0042 | T | Penalty computed from server time at cancel instant |
| F-0043 | TC-0043 | T | Suggestion timing correct; confirm charges penalty; user notified |
| F-0044 | TC-0044 | T | Cutoffs computed in UTC; client TZ never influences outcome |

## M08 — Notifications

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0045 | TC-0045 | T | Each trigger fires on correct event |
| F-0046 | TC-0046 | T + M | Push (FCM test), email (test SMTP), in-app records created |
| F-0047 | TC-0047 | T | Preferences respected; marketing opt-out honored; transactional always sent |
| F-0048 | TC-0048 | T | Async dispatch; retry/backoff; idempotent (no duplicates) |
| F-0049 [v2] | — | — | — |

## M09 — Web Admin Panel

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0050 | TC-0050 | M + D | Dashboard shows correct KPIs; role-filtered |
| F-0051 | TC-0051 | M | Calendar create/block/edit/cancel works; role checks apply |
| F-0052 | TC-0052 | T + M | Search/suspend/role assign; role assign restricted to dueño/superadmin |
| F-0053 | TC-0053 | T + M | Transfer confirm, cash record, refund, failure list |
| F-0054 | TC-0054 | M | Audit viewer read-only; filter works |
| F-0055 | TC-0055 | T | Settings changes persisted + audited; restricted roles |
| F-0056 | TC-0056 | T | Recepcionista cannot view financial reports (verified denial) |
| F-0057 | TC-0057 | M | Language switch takes effect immediately; persists |

## M10 — Reports & Analytics

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0058 | TC-0058 | T + M | Correct revenue aggregation; CSV/PDF export; role-gated |
| F-0059 | TC-0059 | T | Occupancy % correct from confirmed bookings |
| F-0060 | TC-0060 | T | Top customers by bookings/spend; GDPR-safe aggregation |
| F-0061 | TC-0061 | T | Cancellation & no-show rates + penalty revenue correct |
| F-0062 | TC-0062 | T + M | Chart data endpoints correct; date filters work |

## M11 — Eventos & Torneos

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0097 | TC-0097 | T | Draft not public; published visible in feed; i18n fields saved |
| F-0098 | TC-0098 | T | Tournament states transition correctly; deadline enforces registration close |
| F-0099 | TC-0099 | T | Registration created; capacity enforced; payment link if priced; waitlist not required v1 |
| F-0100 | TC-0100 | T | News published; feed sorted; pinned honored |
| F-0101 | TC-0101 | T | Broadcast to subscribers (in-app + opt-in push); reminder before registered event |
| F-0102 | TC-0102 | T (widget) | Feed list/detail/register CTA renders; filters work; localized |
| F-0103 | TC-0103 | T + M | Admin CRUD; capacity view; publish/unpublish; cancel notifies + refunds |

## M12 [v2] — not verified in v1.

## M13 — Security & Audit

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0067 | TC-0067 | T + S | Audit written on all listed actions; append-only (no update/delete API); fields correct |
| F-0068 | TC-0068 | T | Fuzz/length/type/range tests; XSS/SQLi/IDOR security tests pass; no raw SQL (scan) |
| F-0069 | TC-0069 | T | Throttles enforced per spec; 429 responses localized |
| F-0070 | TC-0070 | S + T | TLS ≥1.2, HSTS, secure headers present; Fernet-encrypted fields decrypt correctly |
| F-0071 | TC-0071 | T | Consent recorded; export returns full JSON; erase anonymizes per §6.4; legal records retained |
| F-0072 | TC-0072 | T | Rotation + reuse detection; revocation on password change; blacklist works |

## M14 — API Gateway

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0073 | TC-0073 | T + S | `/api/v1/` namespace consistent; version pinned |
| F-0074 | TC-0074 | S + D | Swagger UI lists all endpoints with schemas |
| F-0075 | TC-0075 | T | Error envelope shape for all error paths; localized messages |
| F-0076 | TC-0076 | T | Pagination correct; page_size cap enforced |
| F-0077 | TC-0077 | M | Health endpoint reports DB/Redis reachability |
| F-0078 [v2] | — | — | — |

## M15 — Flutter Mobile App

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0079 | TC-0079 | T (widget) | Shell renders all tabs; onboarding CTA for guests; runtime localization |
| F-0080 | TC-0080 | T (widget+int) | All auth flows complete; tokens in secure storage (Keychain/Keystore); no token logs |
| F-0081 | TC-0081 | T (widget) | Court list/detail renders correct data; loading/error states |
| F-0082 | TC-0082 | T (widget) | Wizard steps complete; draft restored on restart; validations localized |
| F-0083 | TC-0083 | T (widget+int) | Payment sheet works (test mode); failure recovery re-validates hold |
| F-0084 | TC-0084 | T (widget) | Lists/detail correct; cancel/reschedule act per policy; invoice link |
| F-0085 | TC-0085 | T (widget) | Profile/settings update; language switch live; GDPR actions present |
| F-0086 | TC-0086 | T + M | FCM token registered; deep links open correct screen |
| F-0087 | TC-0087 | T (widget) | Events tab renders feed/detail/register; filters; localized |
| F-0088 | TC-0088 | T (widget) | Cached data shown offline w/ banner; no crash on any API failure |
| F-0089 | TC-0089 | S + M | Secure storage used; HTTPS pinning; static scan shows no hardcoded secrets |

## M16 — Internationalization

| Req | TC | Method | Acceptance Criteria |
|-----|-----|--------|---------------------|
| F-0092 | TC-0092 | T | Locale resolution order correct; default `es` |
| F-0093 | TC-0093 | S + T | All user-facing strings via gettext (lint); catalogs present for es/en/pt/ca; DRF errors localized |
| F-0094 | TC-0094 | T | Number/date/currency formats localized per locale; USD cents correct |
| F-0095 | TC-0095 | T (widget) | ARB files complete; runtime switch without restart |
| F-0096 | TC-0096 | S | No hardcoded strings (lint); translation completeness ≥ 98% (check script) |

---

## 8.2 NFR Verification

| NFR | Method | Acceptance Criteria |
|-----|--------|---------------------|
| NFR-0001..0010 | T + S | See criteria per NFR in `04`; automated security suite in CI |
| NFR-0011/0012 | T (load) | p95 latencies and throughput targets met |
| NFR-0013 | T | Request non-blocking; queue retry/recovery verified |
| NFR-0014 | S | Query plans for top endpoints reviewed in CI |
| NFR-0015 | T | Cache hit ratio ≥ 80% for static reads |
| NFR-0016 | M | Uptime monitored; 99.5% target during venue hours |
| NFR-0017/0018 | T + M | Concurrency stress; restore drill (RPO ≤ 24h, RTO ≤ 4h) |
| NFR-0019 | T (widget) | Graceful degradation tests pass |
| NFR-0020 | M | Booking ≤ 4 taps; wizard ≤ 5 steps (walkthrough) |
| NFR-0021 | S | i18n lint + completeness check pass |
| NFR-0022 | S + M | axe scan clean; manual contrast/target review |
| NFR-0023 | S | CI gates pass (lint, coverage ≥ 80%/60%) |
| NFR-0024 | S | `grep os.environ` = 0 findings |
| NFR-0025 | S | Both platforms build in CI |
| NFR-0026 | S | Version policy documented; deprecation process in place |
| NFR-0027 | M + D | Compliance checklist + pen-test report accepted |
| NFR-0028 | S | No card-data fields in schema/scan (PCI SAQ-A) |
| NFR-0029 | S | Coverage reports meet thresholds per module |
| NFR-0030 | S | Settings-module parity across dev/staging/prod; CI on staging-like config |

---

## 8.3 Test Execution & Sign-off

- All T/S gates run in CI on every merge; coverage thresholds enforced (NFR-0029).
- M and D items executed against staging before release; results recorded in the test log.
- Release blocks on: all v1 TCs passing, security suite clean, RBAC matrix passing, no open blocker defects.
