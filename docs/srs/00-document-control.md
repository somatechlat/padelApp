# 00 — Document Control

## 0.1 Document Identification

| Attribute | Value |
|-----------|-------|
| Project | Padel Court Reservation & Management System |
| Document | Software Requirements Specification (SRS) |
| Document ID | SRS-PADEL-001 |
| Version | 1.1 |
| Status | Draft for review |
| Date | 2026-08-12 |
| Standards | ISO/IEC/IEEE 29148:2018, ISO/IEC 25010:2011, ISO/IEC 27001:2022, ISO 9001:2015, GDPR |
| Author | Product Engineering (AI-assisted) |
| Classification | Internal — Confidential |

---

## 0.2 Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner / Client | TBD | | |
| Technical Lead | TBD | | |
| QA Lead | TBD | | |
| Security Officer | TBD | | |

> Status of this document is **Draft** until all approvers sign.

---

## 0.3 Change Log

| Version | Date | Author | Description of Change |
|---------|------|--------|----------------------|
| 1.0 | 2026-08-12 | Engineering | Initial baseline. All modules M01–M17 defined. v1/v2 scope split applied. |
| 1.1 | 2026-08-12 | Engineering | Corrected cross-references (cancellation policy F-0041/F-0042, audit log F-0067, password NFR-0002, transport NFR-0005); M01–M17 naming; EUR→USD; removed duplicate glossary entry; aligned wizard (4 steps) and nav tabs (5, incl. Events); added assumptions A16–A18 (venue map, integrations, phone/WhatsApp bookings). |

---

## 0.4 Change Control Process

1. Any requested change to requirements is submitted in writing (issue/CR) with rationale and impact.
2. The change is classified: **Editorial** (no behavior change) or **Baseline** (behavior/scope change).
3. Baseline changes require Product Owner + Technical Lead approval and update the Change Log.
4. Every baseline change updates the affected requirement IDs, the traceability matrix, and the verification matrix. No requirement is silently deleted; obsolete requirements are marked **DEPRECATED** and never reused.
5. Requirements are not modified during implementation without this process.

---

## 0.5 Requirement Numbering Legend

| Prefix | Meaning | Example |
|--------|---------|---------|
| `Mxx` | Module identifier | `M04` = Booking Engine |
| `F-xxxx` | Functional requirement | `F-0018` = Booking creation |
| `NFR-xxxx` | Non-functional requirement | `NFR-0001` = Response time |
| `IF-xxxx` | Interface requirement | `IF-0001` = REST base URL |
| `DT-xxxx` | Data requirement | `DT-0001` = Booking entity |
| `QC-xxxx` | Quality/compliance requirement | `QC-0001` = i18n |
| `TC-xxxx` | Test case identifier (verification matrix) | `TC-0018` |

---

## 0.6 Abbreviations & Glossary

| Term | Definition |
|------|-----------|
| **SRS** | Software Requirements Specification |
| **DRF** | Django REST Framework |
| **JWT** | JSON Web Token (access + refresh) |
| **RBAC** | Role-Based Access Control |
| **PWA** | Progressive Web App (out of scope; native apps only) |
| **FCM** | Firebase Cloud Messaging (push) |
| **GDPR** | General Data Protection Regulation (EU) 2016/679 |
| **TZ / UTC** | Timezone / Coordinated Universal Time |
| **No-show** | User fails to arrive for a confirmed booking |
| **Hold** | Temporary slot lock during payment (soft-reserve) |
| **Sede** | Venue / location (Spanish) |
| **Techada / Abierta** | Indoor (roofed) / Outdoor court (Spanish) |
| **Valle / Pico** | Off-peak / peak tariff zones |
| **i18n** | Internationalization |
| **L10n** | Localization |
| **ORM** | Object-Relational Mapping (Django) |
| **Celery** | Asynchronous task queue |
| **Stripe** | Payment gateway |
| **Argon2** | Password hashing algorithm (Django default) |
| **Fernet** | Symmetric encryption (cryptography lib) used by Django |
