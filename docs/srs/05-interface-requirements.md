# 05 — Interface Requirements (ISO/IEC/IEEE 29148 §5.6)

## 5.1 REST API Contract (Backend ↔ Flutter / Web)

### 5.1.1 Conventions
- **Base URL:** `/api/v1/` — stable within a version.
- **Auth:** `Authorization: Bearer <access_token>` for protected endpoints.
- **Content:** `application/json`; UTF-8.
- **Language:** `Accept-Language: es|en|pt|ca` (default `es`).
- **Versioning:** URL path (`/api/v1/`); `X-API-Version` header echoes supported version.
- **Idempotency:** Write endpoints accept `Idempotency-Key` (32-char) for retry safety.

### 5.1.2 Error Envelope (F-0075)
```json
{
  "error": {
    "code": "slot_not_available",
    "message": "This slot is no longer available.",
    "field_errors": { "slots": ["Slot 18:00 has just been taken."] },
    "detail": null
  }
}
```
- `code` = stable machine string. `message` = localized. `field_errors` optional.

### 5.1.3 Pagination (F-0076)
```json
{ "count": 120, "next": "/api/v1/bookings/?page=3", "previous": "...", "results": [ ... ] }
```

### 5.1.4 Endpoint Map

| Method | Path | Auth | Roles | Description | F-ref |
|--------|------|------|-------|-------------|-------|
| POST | `/auth/register/` | — | guest | Register | F-0001 |
| POST | `/auth/verify/` | — | guest | Verify email code | F-0003 |
| POST | `/auth/login/` | — | guest | Login → tokens | F-0002 |
| POST | `/auth/refresh/` | refresh | user | Rotate refresh | F-0002 |
| POST | `/auth/logout/` | refresh | user | Revoke refresh | F-0002 |
| POST | `/auth/password-reset/` | — | guest | Send reset link | F-0004 |
| POST | `/auth/password-reset/confirm/` | — | guest | Set new password | F-0004 |
| POST | `/auth/password/change/` | access | user | Change password | F-0005 |
| GET | `/me/` · PATCH `/me/` | access | user | Profile read/update | F-0006 |
| GET | `/me/devices/` · DELETE `/me/devices/{id}/` | access | user | Sessions | F-0009 |
| POST | `/me/export/` · POST `/me/erase/` | access | user | GDPR | F-0071 |
| GET | `/courts/` · GET `/courts/{id}/` | optional | all | Court list/detail | F-0011/12/13 |
| GET | `/courts/{id}/availability/?date=YYYY-MM-DD` | access | user | Free slots | F-0017 |
| POST | `/bookings/preview/` | access | user | Price preview | F-0030 |
| POST | `/bookings/` | access | user | Create (hold+pending) | F-0021 |
| GET | `/bookings/?status=upcoming` | access | user | History | F-0023 |
| GET | `/bookings/{id}/` | access | owner/admin | Detail | F-0023 |
| PATCH | `/bookings/{id}/reschedule/` | access | owner/admin | Modify | F-0024 |
| POST | `/bookings/{id}/cancel/` | access | owner/admin | Cancel | F-0025 |
| POST | `/bookings/{id}/confirm-payment/` | access | user | Stripe confirm | F-0021 |
| POST | `/payments/{id}/upload-proof/` | access | owner | Upload transfer receipt photo | F-0035a |
| GET | `/bookings/{id}/invoice.pdf` | access | user | Invoice | F-0028 |
| GET | `/notifications/` | access | user | In-app center | F-0046 |
| PATCH | `/notifications/preferences/` | access | user | Prefs | F-0047 |
| POST | `/notifications/register-device/` | access | user | FCM token | F-0086 |
| GET | `/events/` | optional | all | Public events feed | F-0102 |
| GET | `/events/{id}/` | optional | all | Event detail | F-0102 |
| GET | `/tournaments/` | optional | all | Tournament list (open/upcoming) | F-0098 |
| GET | `/tournaments/{id}/` | optional | all | Tournament detail | F-0098 |
| POST | `/tournaments/{id}/register/` | access | user | Register to tournament | F-0099 |
| GET | `/news/` | optional | all | News/announcements feed | F-0100 |
| GET | `/health/` | — | all | Health | F-0077 |
| — Admin namespace (role-gated, F-0056) — | | | | | |
| GET/POST/PATCH/DELETE | `/admin/courts/...` | access | g,d,s | Court mgmt | F-0011 |
| GET/POST/PATCH/DELETE | `/admin/schedules/...` | access | g,d,s | Schedule/maint | F-0014/15 |
| POST | `/admin/slots/block/` | access | r,g,d,s | Blocking | F-0018 |
| GET | `/admin/bookings/?filters` | access | r,g,d,s | Booking ops | F-0051 |
| POST | `/admin/bookings/{id}/mark-no-show/` | access | r,g | No-show | F-0026 |
| GET/PATCH | `/admin/users/...` | access | g,d,s | Users | F-0052 |
| POST | `/admin/payments/{id}/confirm-transfer/` | access | r,g | Transfers | F-0053 |
| POST | `/admin/payments/{id}/reject-transfer/` | access | r,g | Reject transfer with reason | F-0035a |
| POST | `/admin/payments/{id}/cash/` | access | r,g | Cash | F-0053 |
| POST | `/admin/payments/{id}/refund/` | access | g,d | Refunds | F-0038 |
| GET | `/admin/settings/...` · PATCH | access | d,s | Settings | F-0055 |
| GET | `/admin/audit/` | access | g,d,s | Audit log | F-0054 |
| GET | `/reports/revenue/` | access | g,d | Report | F-0058 |
| GET | `/reports/occupancy/` | access | g,d | Report | F-0059 |
| GET | `/reports/customers/` | access | g,d | Report | F-0060 |
| GET | `/reports/cancellations/` | access | g,d | Report | F-0061 |
| GET/POST/PATCH/DELETE | `/admin/events/...` | access | r,g,d,s | Event mgmt | F-0097/103 |
| GET/POST/PATCH/DELETE | `/admin/tournaments/...` | access | g,d,s | Tournament mgmt | F-0098/103 |
| GET | `/admin/tournaments/{id}/registrations/` | access | g,d,s | Registrations | F-0103 |
| POST | `/admin/tournaments/{id}/publish/` · `/unpublish/` | access | g,d | Publish control | F-0098 |
| GET/POST/PATCH/DELETE | `/admin/news/...` | access | r,g,d,s | News mgmt | F-0100 |

Roles legend: `r`=recepcionista, `g`=gerente, `d`=dueño, `s`=superadmin.

### 5.1.5 API Documentation
- Swagger UI at `/api/v1/docs/`, OpenAPI JSON at `/api/v1/schema/` (drf-spectacular). Updated per change (NFR-0026).

---

## 5.2 Flutter Mobile App Interfaces

### 5.2.1 Screen Map
| Screen | Purpose | F-ref |
|--------|---------|-------|
| Onboarding | Guest CTA | F-0079 |
| Login / Register / Verify | Auth | F-0080 |
| Court List | Browse courts | F-0081 |
| Court Detail | Schedule, availability, start booking | F-0081 |
| Booking Wizard (4 steps) | Date → Time → Summary → Pay | F-0082 |
| Payment | Stripe / transfer / cash instructions | F-0083 |
| My Bookings (upcoming/past/cancelled) | Manage | F-0084 |
| Booking Detail | Info, cancel/reschedule, invoice | F-0084 |
| Events Feed | Events, tournaments, news list | F-0087/F-0102 |
| Event / Tournament Detail | Info + register CTA | F-0099/F-0102 |
| Notifications | In-app center | F-0086 |
| Profile | Edit, language, prefs, GDPR actions | F-0085 |
| Settings | Language, notifications, devices, security | F-0085 |

### 5.2.2 Navigation
- Bottom tabs: Home · Bookings · **Events** · Notifications · Profile.
- Push deep links: `/booking/{id}`, `/notifications`, `/courts/{id}`, `/events/{id}`, `/tournaments/{id}`.

### 5.2.3 Local Data
- Secure storage: access/refresh tokens (Keychain/Keystore). Cache: courts, own bookings, locale packs.

### 5.2.4 Platform Interfaces
- **FCM/APNS** registration + token refresh; push handling with deep links.
- **Stripe SDK** (Elements / PaymentSheet) for card + Apple/Google Pay.
- **Keychain/Keystore** secure storage; biometric (v2).

---

## 5.3 Web Admin Interfaces

### 5.3.1 Technology
- Django Admin customized (ModelAdmin + custom admin views), Django templates, i18n via `locale/`.

### 5.3.2 Key Views
- Dashboard (F-0050), Calendar grid (F-0051), Bookings list, Users, Payments, Settings, Audit viewer, Reports, Language switcher (F-0057).

### 5.3.3 Security
- Session auth (Django), CSRF, `SECURE_*` headers, RBAC via admin permissions mapped to roles (F-0056).

---

## 5.4 External Interfaces

| Interface | Protocol | Data | Security |
|-----------|----------|------|----------|
| Stripe API | HTTPS REST | Payment intents, refunds, payouts | API keys in `secrets.py`; signature verification (v2 webhook) |
| Stripe SDK (mobile) | Native SDK | Card/payment sheets | PCI SAQ-A |
| FCM | HTTPS | Push payloads | Server key in `secrets.py` |
| APNS | HTTPS | iOS push | JWT/provider key in `secrets.py` |
| SMTP | SMTP/TLS | Transactional email | Credentials in `secrets.py` |
| PostgreSQL | TCP/TLS | Persistence | Credentials in `secrets.py` |
| Redis | TCP | Celery broker, JWT blacklist | Password in `secrets.py` |
