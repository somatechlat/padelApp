# 01 — Introduction (ISO/IEC/IEEE 29148 §5.2)

## 1.1 Purpose

This document defines the complete software requirements for the **Andes Pádel Court Reservation & Management System** ("PadelApp"). It specifies the functional behavior, quality attributes, interfaces, and data requirements for three integrated deliverables:

1. **Flutter mobile application** — iOS and Android, single codebase.
2. **Web administration panel** — operations and management.
3. **Django backend** — REST API, business logic, data persistence.

This SRS is the single source of truth for design, implementation, verification, and acceptance. It is written to be **complete, consistent, unambiguous, and testable** in accordance with ISO/IEC/IEEE 29148:2018.

## 1.2 Product Scope

The product manages the operation of a padel court rental business:

- Users discover venues and courts, view real-time availability, and book court time.
- Bookings are priced according to configurable tariffs (peak/off-peak, weekend, court type) and paid via supported payment methods.
- The business (admin roles) manages courts, schedules, users, payments, cancellations, penalties, events, tournaments, and reporting.
- The system enforces cancellation policies, no-show penalties, concurrency-safe slot locking, and full auditability.
- All user-facing text is internationalized (i18n) with Spanish as the default locale.

**Client context (from approved proposal):** Andes Pádel (Quito, Ecuador). Currency **USD** (no IVA — client is RIMPE regime). Venue timezone **America/Guayaquil**.

**In scope (v1):** modules M01–M11, M13–M16 (i.e., Auth, Courts, Scheduling, Booking, Pricing, Payments, Cancellation, Notifications, Admin Panel, Reports, **Events & Tournaments**, Security, API, Flutter App, i18n).
**Out of scope (v1, documented as v2):** M12 Loyalty, M17 Class Booking, plus the v2-flagged features (social login, promotions/coupons, webhooks, offline sync, local reminders, partner matching).

## 1.3 Product Overview

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| Mobile App | Flutter (Dart) | User booking experience, events/tournaments feed, payments, notifications, profile |
| Web Admin | Django Admin (customized) | Operations, schedule, users, payments, events, reports |
| Backend | Django 5.x + DRF + PostgreSQL | REST API, business logic, persistence, async jobs (Celery) |
| Notifications | FCM + email (Celery queue) | Push / email delivery |
| Payments | Stripe + manual transfer + cash | Payment lifecycle |

**Proposal deliverables mapping (§3 of the approved proposal):**

| Proposal deliverable | SRS reference |
|----------------------|---------------|
| Aplicación móvil funcional | M14, M15 (Flutter app) |
| Sistema de reservas operativo | M03, M04, M05, M06, M07 |
| Sistema de gestión de usuarios | M01 |
| Sistema de administración | M09 |
| Base de datos configurada | 06-Data-requirements, infra |
| Configuración inicial del servidor | 02 §2.4, deployment plan (delivered separately after SRS approval) |
| Soporte Google Play Store | NFR-0025, release checklist |
| Soporte Apple App Store | NFR-0025, release checklist |

All settings are defined in the Django settings package (`settings/base.py`, `dev.py`, `prod.py`, `secrets.py`). No secrets are read from environment variables; `secrets.py` is git-ignored and validated at boot.

## 1.4 Definitions, Acronyms, and Abbreviations

See `00-document-control.md` §0.6.

## 1.5 References

| Ref | Document / Standard | Version |
|-----|--------------------|---------|
| [R1] | ISO/IEC/IEEE 29148:2018 — Requirements Engineering | 2018 |
| [R2] | ISO/IEC 25010:2011 — Quality Model | 2011 |
| [R3] | ISO/IEC 27001:2022 — Information Security | 2022 |
| [R4] | ISO 9001:2015 — Quality Management | 2015 |
| [R5] | GDPR (EU) 2016/679 | 2018 |
| [R6] | OWASP API Security Top 10 | 2023 |
| [R7] | Django 5.x Documentation | 5.x |
| [R8] | Django REST Framework Documentation | 3.15+ |
| [R9] | Flutter Documentation (flutter_localizations) | 3.x |
| [R10] | Business survey: `levantamiento-requisitos-padel.docx` | 2026 |

## 1.6 Overview of the Document

- §02 Product perspective, users, operating environment, constraints, assumptions.
- §03 Functional requirements by module (M01–M17).
- §04 Non-functional requirements (ISO 25010 + ISO 27001).
- §05 Interface requirements (REST, UI, external).
- §06 Data requirements (dictionary, integrity, retention, GDPR).
- §07 Traceability matrix.
- §08 Verification matrix.
