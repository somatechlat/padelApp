# 04 — Non-Functional Requirements (ISO/IEC 25010 + ISO 27001)

> NFRs are grouped by ISO/IEC 25010 quality characteristics. ISO 27001 controls are mapped explicitly. Each NFR has an ID, description, target/metric, and verification pointer (see `08-verification-matrix.md`).

---

## 4.1 Security (ISO 25010 Security · ISO 27001)

### NFR-0001 · Authentication Integrity
- **Requirement:** All protected endpoints require a valid access token; every request is authenticated and authorized before any business logic runs.
- **Metric:** 0% protected endpoints accessible without valid token (automated scan).
- **ISO:** 27001 A.9.2; OWASP API #1/#5.

### NFR-0002 · Password Policy
- **Requirement:** Passwords ≥10 chars, must contain upper, lower, digit, and symbol; rejected if in the common-password list or too similar to profile attributes. Hashed with **Argon2** (Django default); legacy MD5/SHA never used.
- **Metric:** Validator tests pass; hash field is `argon2$...`.
- **ISO:** 27001 A.9.4; OWASP API #2.

### NFR-0003 · Brute-force Protection
- **Requirement:** Lockout after 5 failed logins for 30 min; exponential backoff on resend/verification endpoints; rate limits (F-0069).
- **Metric:** 5-failure lockout verified by test; 429 responses correct.
- **ISO:** 27001 A.9.4; OWASP API #4.

### NFR-0004 · Data Encryption at Rest
- **Requirement:** Fields requiring protection (e.g., refresh-token family seeds, payment provider metadata) encrypted with Fernet via `django.core.signing`/`cryptography`. DB-level encryption handled by deployment (volume encryption).
- **Metric:** Encryption helper tests; no plaintext sensitive fields in DB dumps.
- **ISO:** 27001 A.8/A.10.

### NFR-0005 · Data Encryption in Transit
- **Requirement:** TLS 1.2+ only; HSTS; all cookies `Secure + HttpOnly + SameSite`; CSP/`X-Content-Type-Options`/`X-Frame-Options`/referrer policy set.
- **Metric:** Prod deployment scan shows no TLS <1.2; security headers present.
- **ISO:** 27001 A.13.1; OWASP API #3.

### NFR-0006 · Least Privilege (RBAC enforcement)
- **Requirement:** Role checks are server-side on every endpoint; 100% coverage by tests; admin UI never relies on hiding for enforcement.
- **Metric:** RBAC test matrix per role × endpoint passes.
- **ISO:** 27001 A.9.1/A.9.2.

### NFR-0007 · Auditability
- **Requirement:** Immutable audit log for sensitive actions (F-0067); logs non-repudiable (append-only, checksum or write-once storage).
- **Metric:** Every required action produces an audit record (tested).
- **ISO:** 27001 A.12.4; OWASP API #9.

### NFR-0008 · Secrets Management
- **Requirement:** Zero secrets in code, repos, logs, or settings-except-`secrets.py` (git-ignored, 0600). No environment variables read for secrets (C2/C3). Boot-time validation fails fast on missing/blank secrets.
- **Metric:** Secret scan of repository = 0 findings; boot test with missing secret fails.
- **ISO:** 27001 A.8.10/A.8.12.

### NFR-0009 · Input Validation & Injection Prevention
- **Requirement:** All inputs validated (F-0068); ORM parameterization throughout; no `raw()`/`extra()` SQL; max input sizes enforced; strict media type checks.
- **Metric:** OWASP API #3 checklist passes; security tests for XSS/SQLi/IDOR.
- **ISO:** 27001 A.14.2; OWASP API #3.

### NFR-0010 · Session & Token Security
- **Requirement:** Access 15 min, refresh 7 days, rotation + reuse detection, revocation on password change. Token storage on device = platform secure storage.
- **Metric:** Rotation/reuse tests pass; no token in Flutter logs.
- **ISO:** 27001 A.9.

---

## 4.2 Performance & Scalability (ISO 25010 Performance efficiency)

### NFR-0011 · API Latency
- **Requirement:** p95 response time ≤ 300 ms for read endpoints (availability, courts, bookings) and ≤ 600 ms for write endpoints (booking create) under normal load, excluding network.
- **Metric:** Load test report.
- **ISO:** 25010 Time behavior.

### NFR-0012 · Throughput
- **Requirement:** Sustain 50 concurrent users / 300 req/min without degradation (baseline for a single venue).
- **Metric:** Load test report.
- **ISO:** 25010 Capacity.

### NFR-0013 · Asynchronous Processing
- **Requirement:** Notifications and report exports never block HTTP requests (Celery); queues monitored with retry/backoff and dead-letter handling.
- **Metric:** Integration test: request returns before task completes; failure recovers.
- **ISO:** 25010 Time behavior/Reliability.

### NFR-0014 · Indexing & Query Performance
- **Requirement:** All list queries used by UI are index-backed; availability queries hit covered indexes; slow-query log threshold set.
- **Metric:** Query plan review in CI for the top 10 endpoints.
- **ISO:** 25010 Time behavior.

### NFR-0015 · Cache Strategy
- **Requirement:** Read-mostly data (courts, schedules, tariff config) cached with short TTL and invalidated on change; availability computed fresh with bounded queries.
- **Metric:** Cache hit ratio > 80% for static reads.
- **ISO:** 25010 Time behavior.

---

## 4.3 Reliability & Availability (ISO 25010 Reliability)

### NFR-0016 · Availability
- **Requirement:** 99.5% monthly availability during 08:00–23:00 venue hours; planned maintenance outside venue hours.
- **Metric:** Uptime report.
- **ISO:** 25010 Availability.

### NFR-0017 · Data Integrity & Concurrency
- **Requirement:** No lost updates or double-booking possible; transactions + row locks + unique constraints (F-0020); DB backups daily + WAL archiving.
- **Metric:** Concurrent-booking stress test → exactly one succeeds per slot.
- **ISO:** 25010 Recoverability; 9001 records.

### NFR-0018 · Failure Recovery
- **Requirement:** Payment/webhook failures retried idempotently; booking state never ambiguous after crash (journaled transitions); restore from backup RPO ≤ 24h, RTO ≤ 4h.
- **Metric:** Chaos tests (killed worker mid-transaction) leave consistent state.
- **ISO:** 25010 Recoverability.

### NFR-0019 · Graceful Degradation (Mobile)
- **Requirement:** Flutter app shows localized offline/error states and cached data; no crash on any API failure (tested via widget tests).
- **Metric:** Widget test suite for error states.
- **ISO:** 25010 Fault tolerance.

---

## 4.4 Usability & Accessibility (ISO 25010 Usability)

### NFR-0020 · Task Efficiency
- **Requirement:** Booking a court from home screen ≤ 4 taps after selection; booking wizard = 4 steps.
- **Metric:** Usability walkthrough script.
- **ISO:** 25010 Operability.

### NFR-0021 · Localization Quality (i18n/L10n)
- **Requirement:** 100% user-facing strings externalized; locales `es/en/pt/ca`; no string truncation in any locale; date/number/currency per locale.
- **Metric:** Lint + catalog completeness check (≥ 98% translated strings).
- **ISO:** 25010 Usability/Compatibility.

### NFR-0022 · Accessibility
- **Requirement:** WCAG 2.1 AA on web admin; Flutter semantics labels; minimum contrast; touch targets ≥ 44px.
- **Metric:** Automated axe scan + manual review.
- **ISO:** 25010 Usability.

---

## 4.5 Maintainability & Portability (ISO 25010)

### NFR-0023 · Code Quality
- **Requirement:** Linters (flake8/ruff, dart analyze) with zero errors in CI; type hints; coverage ≥ 80% for backend, ≥ 60% for Flutter core logic; no dead code.
- **Metric:** CI gates.
- **ISO:** 25010 Maintainability; 9001.

### NFR-0024 · Modularity & Settings-Only Config
- **Requirement:** All configuration in the Django settings package (`base/dev/prod/secrets`); feature flags in settings; no environment variables for configuration (C2).
- **Metric:** `grep` for `os.environ` in codebase = 0.
- **ISO:** 25010 Modularity.

### NFR-0025 · Portability
- **Requirement:** Flutter single codebase for iOS/Android; backend runs on any Linux host (Docker); PostgreSQL-only; no platform-specific code paths outside `platform/` in Flutter.
- **Metric:** Build both platforms in CI.
- **ISO:** 25010 Portability.

---

## 4.6 Compatibility & Compliance (ISO 25010 Compatibility · ISO 9001 · GDPR)

### NFR-0026 · API Compatibility
- **Requirement:** Versioned API; additive changes only within v1; breaking changes require v2 + deprecation notice.
- **ISO:** 25010 Compatibility.

### NFR-0027 · Compliance
- **Requirement:** GDPR: consent recorded, export available, erase works (DT-0018); audit trail (ISO 9001 records); documented requirements process (ISO 29148); no use of prohibited algorithms.
- **Metric:** Compliance checklist + pen-test report.
- **ISO:** 27001/9001/GDPR.

### NFR-0028 · Payment Security Compliance
- **Requirement:** PCI-DSS SAQ-A scope: card data handled by Stripe Elements only; no card data in our DB, logs, or analytics.
- **Metric:** Code scan: no `card/cvv/pan` persistence fields.
- **ISO:** PCI-DSS SAQ-A.

---

## 4.7 Testability

### NFR-0029 · Test Coverage
- **Requirement:** Every F-xxxx has ≥1 test case in `08`; backend coverage ≥ 80%; critical modules (M04, M06, M07) ≥ 90%; Flutter widget tests for all screens.
- **Metric:** Coverage report in CI.
- **ISO:** 25010 Testability; 9001.

### NFR-0030 · Environment Parity
- **Requirement:** Dev/staging/prod use the same settings modules with different `secrets.py`; CI runs the full suite on staging-like config.
- **ISO:** 9001.
