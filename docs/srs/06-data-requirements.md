# 06 — Data Requirements (ISO/IEC/IEEE 29148 §5.7)

## 6.1 Data Dictionary

> All timestamps stored in UTC (`USE_TZ=True`). Monetary values in integer minor units (USD cents) — **integers in minor units** throughout. Soft-deletes via `is_active`/archive flags; history preserved (no destructive deletes except GDPR erase).

### Core Entities

| Entity | Key Fields | Notes |
|--------|-----------|-------|
| **User** (`custom user model`) | `email` (unique), `full_name`, `phone`, `avatar`, `language_code`, `role`, `status`, `email_verified`, `consent_version`/`consent_ts`, `last_login`, `is_active`, `created_at` | Custom `AbstractUser`-based; `USERNAME_FIELD=email` |
| **Role** | `cliente, recepcionista, gerente, dueño, superadmin` | Enum, not free text |
| **Venue** (Sede) | `name`, `timezone`, `currency`, `address`, `holiday_calendar` | v1: one venue |
| **Court** | `venue`, `name`, `number`, `type` (techada/abierta), `has_lighting`, `status`, `images`, `archived` | |
| **CourtSchedule** | `court`, `weekday`, `open_time`, `close_time`, `holiday_override` | Per-weekday |
| **MaintenanceWindow** | `court`, `weekday` or `date`, `start`, `end`, `recurring`, `reason` | Auto-blocks slots |
| **TimeSlot** | `court`, `start_utc`, `end_utc`, `date_local`, `status` | 30-min granularity |
| **Booking** | `user`, `court`, `start_utc`, `end_utc`, `duration_min`, `state`, `total_minor`, `penalty_minor`, `invoice_number`, `cancelled_at`, `cancelled_reason`, `no_show_at` | State machine F-0022 |
| **BookingSlot** | `booking`, `timeslot`, `position` | Unique `(timeslot, booking)` |
| **BookingHold** | `user`, `timeslot`, `expires_at` | Soft-reserve F-0019 |
| **PriceRule** | `name`, `court_type`, `zone` (valle/pico), `weekday`, `base_minor`, `multipliers` (JSON) | Versioned, audited |
| **Holiday** | `date`, `name`, `zone` | Feeds multipliers |
| **Payment** | `booking`, `method` (card/transfer/cash), `provider` (stripe), `provider_ref`, `amount_minor`, `status`, `type` (auth/capture/refund/penalty), `proof_image` (transfer receipt, nullable), `rejection_reason` (nullable), `created_at` | Lifecycle F-0036, Transfer proof F-0035a |
| **PaymentMethod (stored)** | `user`, `provider`, `tokenized_ref` | Card data never stored (PCI) |
| **Invoice** | `booking`, `number`, `issued_at`, `items` (JSON lines), `total_minor`, `pdf_url` | F-0028 |
| **Notification** | `user`, `type`, `channel`, `status`, `payload`, `read_at`, `idempotency_key` | In-app center |
| **NotificationPreference** | `user`, `event_type`, `channels` | F-0047 |
| **DeviceToken** | `user`, `platform`, `token`, `last_seen` | FCM/APNS |
| **AuditLog** | `actor`, `action`, `entity_type`, `entity_id`, `before`/`after` (JSON), `ip`, `created_at` | Immutable F-0067 |
| **RefreshTokenFamily** | `user`, `device_id`, `seed` (encrypted), `rotations`, `revoked_at` | F-0072 |
| **ConsentRecord** | `user`, `version`, `accepted_at`, `ip` | GDPR F-0071 |
| **Event** | `title` (i18n), `description` (i18n), `category`, `start/end_utc`, `venue`, `court` (nullable), `cover_image`, `status` (draft/published/cancelled), `created_by` | F-0097 |
| **Tournament** | `name`, `modality`, `category`, `start_date`, `reg_deadline`, `max_pairs`, `price_minor` (nullable), `rules`, `prizes`, `status` (draft/open/closed/in_progress/finished), `created_by` | F-0098 |
| **TournamentRegistration** | `tournament`, `user`, `partner_name` (nullable), `state` (pending_payment/confirmed/cancelled), `payment` (nullable), `created_at` | F-0099 |
| **NewsPost** | `title` (i18n), `body` (i18n), `image`, `pinned`, `published_at`, `created_by` | F-0100 |

## 6.2 Integrity Rules

| Rule | Enforcement |
|------|-------------|
| No double-booking of a TimeSlot | Unique constraint `(timeslot, booking)` + `select_for_update` (F-0020) |
| Booking slots must be consecutive & same court | Service-layer validation |
| Duration ∈ {60, 90, 120} minutes | Validation |
| `end_utc > start_utc`, slots aligned to 30-min grid | Validation |
| Price server-computed, never client-supplied | Serializer ignores client price |
| State transitions only per F-0022 | Model-level transition guard |
| `total_minor`, `penalty_minor`, amounts ≥ 0 | DB check constraint |
| Foreign keys protected with `PROTECT` where history required | ORM `on_delete` policy |
| Email uniqueness case-insensitive | Unique + normalization |
| AuditLog append-only | No update/delete API; DB user lacks UPDATE/DELETE on the table |

## 6.3 Data Retention (ISO 9001 records · GDPR)

| Data | Retention |
|------|-----------|
| Bookings, invoices, payments, audit log | 5 years (tax/accounting) — **legal retention, not erasable** |
| User account data | Until deletion request |
| RefreshTokenFamily | 90 days after revocation (housekeeping job) |
| BookingHold | 10 min (auto-expire + purge) |
| Notification logs | 180 days |
| Export packages | 30 days then purged |
| Failed-login records | 30 days |

## 6.4 GDPR Erasure (F-0071 · DT-0018)

- **Erase request:** `account_erase` job → anonymizes PII (name→"Usuario eliminado", email→`deleted-<uuid>@invalid`, phone cleared, avatar removed, GDPR consent revoked, personal device tokens removed) **except** legally retained records (bookings/invoices/payments/audit) which keep only non-personal business data and a hash link to the anonymized user.
- **Export request:** full personal data as JSON within 30 days (queue job + link expiry 48h).
- **Consent:** recorded with version + timestamp; withdrawal revokes marketing channels only (transactional messages still delivered — F-0047).

## 6.5 Backup & Recovery (NFR-0017/0018)

- Daily full backups + continuous WAL archiving (RPO ≤ 24h target → 1h with WAL).
- Restore tested quarterly; RTO ≤ 4h.
- Backups encrypted at rest; off-site copy.
