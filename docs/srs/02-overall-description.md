# 02 — Overall Description (ISO/IEC/IEEE 29148 §5.3)

## 2.1 Product Perspective

PadelApp is a **new, self-contained system** replacing a static AI-generated visual prototype (no real functionality). It is:

- A new product, new codebase, no legacy data migration (v1 seeds master data from scratch).
- Composed of three subsystems sharing one backend: Flutter app, Web Admin, REST API.
- Dependent on external services: Stripe (payments), FCM (push), SMTP (email).

### Context Diagram

```
┌──────────────────┐        ┌──────────────────┐
│  Flutter App     │◄──────►│                  │
│  (iOS/Android)   │  HTTPS │                  │
└──────────────────┘        │   Django Backend │
┌──────────────────┐        │   + PostgreSQL   │
│  Web Admin       │◄──────►│   + Celery       │
└──────────────────┘        └────────┬─────────┘
                                      │ HTTPS
                     ┌────────────────┼────────────────┐
                     │                │                │
                ┌────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
                │  Stripe  │    │  FCM/APNS │    │   SMTP    │
                └──────────┘    └───────────┘    └───────────┘
```

## 2.2 Product Functions (Overview)

| # | Function Area | Summary |
|---|--------------|---------|
| 1 | Identity & Access | Registration, login, JWT, RBAC, profile, password mgmt |
| 2 | Court Management | CRUD courts, types, schedules, maintenance |
| 3 | Scheduling | 30-min slots, availability, blocking, holds |
| 4 | Booking Engine | Create/modify/cancel, state machine, conflict safety |
| 5 | Pricing Engine | Tariffs, zones, multipliers, price preview |
| 6 | Payments | Stripe, transfer, cash, refunds, receipts |
| 7 | Cancellations | Policy windows, penalties, no-shows |
| 8 | Notifications | Push/email/in-app, triggers, preferences |
| 9 | Admin Panel | Dashboard, calendar, users, payments, audit |
| 10 | Reports | Revenue, occupancy, customers, cancellations, export |
| 11 | Events & Tournaments | Event/tournament/news publication, registration, feed |
| 12 | Security & Audit | Logging, validation, rate limits, GDPR, token mgmt |
| 13 | API | Versioned REST, docs, errors, pagination |
| 14 | Mobile App | All user-facing screens & flows |
| 15 | i18n | Full internationalization of all subsystems |

## 2.3 User Classes and Characteristics

| Class | Role | System | Privileges (summary) | Skill |
|-------|------|--------|----------------------|-------|
| **Guest** | Unauthenticated visitor | App | Browse courts/events/availability, register/login | Low |
| **Cliente** | Registered user | App | Book, pay, manage own bookings, register to tournaments, notifications | Low |
| **Recepcionista** | Front-desk staff | Web Admin | Confirm/cancel bookings, mark no-show, record cash, block slots, create events/news | Medium |
| **Gerente** | Manager | Web Admin | Recepcionista + pricing, refunds, reports, user mgmt, publish events/tournaments | Medium |
| **Dueño** | Owner | Web Admin | Gerente + role mgmt, financial reports, settings | High |
| **Superadmin** | Technical | Web Admin/Django | Full system incl. audit view, maintenance | High |

## 2.4 Operating Environment

| Component | Environment |
|-----------|-------------|
| Backend | Linux server; Python 3.12+; Django 5.x; PostgreSQL 15+; Redis (Celery broker); Gunicorn/ASGI |
| Mobile | iOS 15+ / Android 8.0+ (API 26+); Flutter 3.x |
| Web Admin | Modern evergreen browsers (Chrome, Edge, Firefox, Safari) |
| Time | All persistence in UTC; display in venue local timezone (**America/Guayaquil**, Quito, Ecuador) |
| Currency | **USD** (US Dollar, integer minor units = cents); VAT 0% (client under RIMPE regime, no IVA) |

## 2.5 Design and Implementation Constraints

| # | Constraint | Origin |
|---|-----------|--------|
| C1 | Django as the ONLY backend framework | Client |
| C2 | No environment-variable secrets; all settings in Django settings package; `secrets.py` git-ignored | Client |
| C3 | All secrets use Django-native mechanisms (django.core.signing, cryptography/Fernet, django SECRET_KEY) | Client |
| C4 | Passwords via Django Argon2 hasher + full password validators | ISO 27001 / Client |
| C5 | Full i18n; Spanish default; all strings via gettext/ARB | Client |
| C6 | Native apps only (Flutter); PWA not in scope | Client |
| C7 | PostgreSQL only (no SQLite in prod) | Team |
| C8 | All times stored UTC; TZ conversions server-side only | Team |
| C9 | OpenAPI/Swagger auto-generated API docs required | Team |
| C10 | Testing required per module (unit + integration); no code without tests | ISO 9001 |
| C11 | Payment card data never stored server-side (Stripe Elements / deferred payments) | PCI-DSS |
| C12 | Flutter tokens stored in platform secure storage (Keychain/Keystore) | ISO 27001 |

## 2.6 Assumptions and Dependencies

### Assumptions (baseline — the client survey left these unanswered)

| # | Assumption |
|---|-----------|
| A1 | Business model: **hourly court rental**; classes are v2. |
| A2 | Multiple courts per single venue (**Andes Pádel**, Quito); multiple venues possible but v1 ships one venue. |
| A3 | Operating hours **08:00–23:00** every day; configurable per court. |
| A4 | Registration is **mandatory** to book; guests may browse. |
| A5 | Payment methods v1: card (Stripe), bank transfer (admin-confirmed), cash at venue. |
| A6 | Free cancellation **≥24h** before start; 50% penalty inside 24h; 100% on no-show. Defaults configurable. |
| A7 | Tiered pricing: valle/pico zones, weekend multiplier, techada & lighting surcharge. |
| A8 | No inventory/product sales in v1. |
| A9 | No offline mode in v1 (online-only; local cache of static data allowed). |
| A10 | No chat functionality in v1. |
| A11 | Notifications v1: push + email + in-app center. |
| A12 | Locales v1: `es` (default), `en`, `pt`, `ca`. |
| A13 | Client owns/operates venue; admin roles created by superadmin seed. |
| A14 | Seat on premises free for players; courts sold as whole (not per player). |
| A15 | **Events & Tournaments are in v1 scope** per the approved proposal: event/tournament/news publication, tournament registration (players). Tournament brackets/score-keeping are v2 (publication + registration only). |
| A16 | **No venue map** (Q17 "mapa de la sede") in v1 — venue address/directions shown as text; interactive map is v2. |
| A17 | **Integrations (Q19) v1 = Stripe only.** Google Calendar sync, WhatsApp Business, smart locks, and cameras are **excluded from v1** (documented as v2 candidates; not currently specified). |
| A18 | **Current booking process (Q9)** — phone/WhatsApp/walk-in requests are handled by admin staff creating bookings on the customer's behalf through the Web Admin calendar (F-0051); no guest self-service booking. |

### Dependencies

| # | Dependency | Notes |
|---|-----------|-------|
| D1 | Stripe account (API keys) | Sandbox for dev; production keys only in prod `secrets.py` |
| D2 | FCM project (mobile push) | APNS needed for iOS push |
| D3 | SMTP provider | Transactional email |
| D4 | PostgreSQL + Redis | Provisioned by deployment |

## 2.7 Requirements Organization

Functional requirements are grouped by module in `03-functional-requirements.md`. Each module has an identifier (M01–M17) and each feature a unique ID (F-xxxx). Non-functional requirements in `04` cross-reference features via the traceability matrix in `07`.
