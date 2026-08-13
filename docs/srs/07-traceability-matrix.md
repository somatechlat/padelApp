# 07 — Traceability Matrix

> Maps every functional requirement to its module, ISO/IEC 25010 quality characteristics, ISO 27001 controls (where applicable), and test-case reference (see `08`). This matrix must be updated on any baseline change (§0.4).

Legend — 25010 characteristics: FS=Functional suitability, PE=Performance efficiency, CO=Compatibility, US=Usability, RE=Reliability, SE=Security, MA=Maintainability, PO=Portability.

---

## M01 — Authentication & Identity

| Req | Module | 25010 | 27001 / Other | Test |
|-----|--------|-------|---------------|------|
| F-0001 Registration | M01 | FS, SE | A.9 | TC-0001 |
| F-0002 Login/Logout | M01 | FS, SE | A.9.2, A.9.4 | TC-0002 |
| F-0003 Email verification | M01 | FS, SE | A.9 | TC-0003 |
| F-0004 Password reset | M01 | FS, SE | A.9.4 | TC-0004 |
| F-0005 Change password | M01 | FS, SE | A.9.4 | TC-0005 |
| F-0006 Profile mgmt | M01 | FS, US | — | TC-0006 |
| F-0007 RBAC | M01 | FS, SE | A.9.1, A.9.2 | TC-0007 |
| F-0008 Account state | M01 | FS, SE | A.9 | TC-0008 |
| F-0009 Devices/sessions | M01 | FS, SE | A.9 | TC-0009 |
| F-0010 Social login [v2] | M01 | — | — | — |

## M02 — Court Management

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0011 Court CRUD | M02 | FS | A.9 | TC-0011 |
| F-0012 Court types | M02 | FS | — | TC-0012 |
| F-0013 Court status | M02 | FS, RE | — | TC-0013 |
| F-0014 Operating schedule | M02 | FS | — | TC-0014 |
| F-0015 Maintenance windows | M02 | FS, RE | — | TC-0015 |

## M03 — Scheduling & Availability

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0016 Slot generation | M03 | FS | — | TC-0016 |
| F-0017 Real-time availability | M03 | FS, PE | — | TC-0017 |
| F-0018 Manual blocking | M03 | FS | A.12 | TC-0018 |
| F-0019 Booking hold | M03 | FS, RE | — | TC-0019 |
| F-0020 Conflict prevention | M03 | RE, SE | A.12 | TC-0020 |

## M04 — Booking Engine

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0021 Booking creation | M04 | FS | — | TC-0021 |
| F-0022 State machine | M04 | FS, RE | A.12 | TC-0022 |
| F-0023 Booking history | M04 | FS, US | — | TC-0023 |
| F-0024 Modify/reschedule | M04 | FS | — | TC-0024 |
| F-0025 Cancel (user) | M04 | FS | — | TC-0025 |
| F-0026 No-show workflow | M04 | FS | — | TC-0026 |
| F-0027 Concurrency UX | M04 | US, RE | — | TC-0027 |
| F-0028 Invoice generation | M04 | FS | A.12 | TC-0028 |

## M05 — Pricing Engine

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0029 Tariff model | M05 | FS | A.12 | TC-0029 |
| F-0030 Price preview | M05 | FS, US | SE (server authority) | TC-0030 |
| F-0031 Time-of-day zones | M05 | FS | — | TC-0031 |
| F-0032 Day multipliers | M05 | FS | — | TC-0032 |
| F-0033 Promotions [v2] | M05 | — | — | — |
| F-0034 Coupons [v2] | M05 | — | — | — |

## M06 — Payments & Billing

| Req | Module | 25010 | 27001 / Other | Test |
|-----|--------|-------|---------------|------|
| F-0035 Payment methods | M06 | FS, SE | PCI SAQ-A | TC-0035 |
| F-0036 Payment lifecycle | M06 | FS, RE | A.12 | TC-0036 |
| F-0037 Deposit capture | M06 | FS, RE | PCI | TC-0037 |
| F-0038 Refunds | M06 | FS | A.12 | TC-0038 |
| F-0039 Receipts & history | M06 | FS, US | 9001 | TC-0039 |
| F-0040 Reconciliation | M06 | FS | 9001 | TC-0040 |

## M07 — Cancellation & Penalties

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0041 Policy config | M07 | FS, MA | — | TC-0041 |
| F-0042 Penalty calc | M07 | FS | — | TC-0042 |
| F-0043 No-show detection | M07 | FS, RE | — | TC-0043 |
| F-0044 TZ authority | M07 | FS | — | TC-0044 |

## M08 — Notifications

| Req | Module | 25010 | 27001 / GDPR | Test |
|-----|--------|-------|--------------|------|
| F-0045 Event triggers | M08 | FS | — | TC-0045 |
| F-0046 Channels | M08 | FS, US | — | TC-0046 |
| F-0047 Preferences | M08 | FS, US | GDPR Art.7 | TC-0047 |
| F-0048 Delivery queue | M08 | RE, PE | — | TC-0048 |
| F-0049 Local reminders [v2] | M08 | — | — | — |

## M09 — Web Admin Panel

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0050 Dashboard | M09 | US | — | TC-0050 |
| F-0051 Calendar view | M09 | US, FS | — | TC-0051 |
| F-0052 User mgmt | M09 | FS | A.9 | TC-0052 |
| F-0053 Payment mgmt | M09 | FS | A.12 | TC-0053 |
| F-0054 Audit viewer | M09 | FS | A.12.4 | TC-0054 |
| F-0055 Settings mgmt | M09 | FS, MA | A.12 | TC-0055 |
| F-0056 RBAC in admin | M09 | SE | A.9 | TC-0056 |
| F-0057 Language switch | M09 | US | — | TC-0057 |

## M10 — Reports & Analytics

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0058 Revenue report | M10 | FS, US | A.9 (g,d) | TC-0058 |
| F-0059 Occupancy report | M10 | FS, US | — | TC-0059 |
| F-0060 Frequent customers | M10 | FS, US | GDPR | TC-0060 |
| F-0061 Cancellations report | M10 | FS | — | TC-0061 |
| F-0062 Time-series charts | M10 | FS, PE | — | TC-0062 |

## M11 — Eventos & Torneos

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0097 Event publication | M11 | FS | A.9, A.12 | TC-0097 |
| F-0098 Tournament publication | M11 | FS | A.9, A.12 | TC-0098 |
| F-0099 Tournament registration | M11 | FS | — | TC-0099 |
| F-0100 News & announcements | M11 | FS | — | TC-0100 |
| F-0101 Event notifications | M11 | US | GDPR Art.7 | TC-0101 |
| F-0102 Events feed (mobile) | M11 | FS, US | — | TC-0102 |
| F-0103 Event administration | M11 | FS, US | A.9 | TC-0103 |

## M12 — Loyalty [v2]

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0063..F-0066 | M12 | — | — | — (v2) |

## M13 — Security & Audit

| Req | Module | 25010 | 27001 / Other | Test |
|-----|--------|-------|---------------|------|
| F-0067 Audit log | M13 | SE, RE | A.12.4 | TC-0067 |
| F-0068 Input validation | M13 | SE | A.14.2 | TC-0068 |
| F-0069 Rate limiting | M13 | SE, RE | A.12 | TC-0069 |
| F-0070 Transport security | M13 | SE | A.8/A.10/A.13 | TC-0070 |
| F-0071 GDPR privacy | M13 | SE | GDPR Art.5/7/15/17 | TC-0071 |
| F-0072 Token security | M13 | SE | A.9 | TC-0072 |

## M14 — API Gateway

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0073 Versioned REST | M14 | CO, MA | — | TC-0073 |
| F-0074 API docs | M14 | MA | — | TC-0074 |
| F-0075 Error envelope | M14 | US, FS | — | TC-0075 |
| F-0076 Pagination | M14 | PE | — | TC-0076 |
| F-0077 Health check | M14 | RE | — | TC-0077 |
| F-0078 Webhooks [v2] | M14 | — | — | — |

## M15 — Flutter Mobile App

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0079 Onboarding/nav | M15 | US | — | TC-0079 |
| F-0080 Auth screens | M15 | US, SE | A.9 | TC-0080 |
| F-0081 Court list/detail | M15 | US | — | TC-0081 |
| F-0082 Booking wizard | M15 | US, FS | — | TC-0082 |
| F-0083 Payment screens | M15 | US, SE | PCI | TC-0083 |
| F-0084 My bookings | M15 | US, FS | — | TC-0084 |
| F-0085 Profile & settings | M15 | US | GDPR | TC-0085 |
| F-0086 Push & deep links | M15 | US | — | TC-0086 |
| F-0087 Events feed (mobile) | M15 | US, FS | — | TC-0087 |
| F-0088 Cache & resilience | M15 | RE | — | TC-0088 |
| F-0089 Platform security | M15 | SE | A.8/A.10 | TC-0089 |

## M16 — Internationalization

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0092 Locale resolution | M16 | US, CO | — | TC-0092 |
| F-0093 Backend i18n | M16 | US | — | TC-0093 |
| F-0094 Number/date/currency L10n | M16 | US | — | TC-0094 |
| F-0095 Flutter i18n | M16 | US | — | TC-0095 |
| F-0096 i18n governance | M16 | MA | 9001 | TC-0096 |

## M17 — Class Booking [v2]

| Req | Module | 25010 | 27001 | Test |
|-----|--------|-------|-------|------|
| F-0104..F-0106 | M17 | — | — | — (v2) |

---

## Completeness Check

- v1 modules: M01–M11, M13–M16 → all features mapped above.
- v2 modules/features: F-0010, F-0033, F-0034, F-0049, F-0078, M12 (F-0063..66), M17 (F-0104..06) → excluded from tests, documented for completeness.
- Every v1 feature has exactly one TC reference; TC definitions live in `08`.
