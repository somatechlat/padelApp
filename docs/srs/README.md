# Padel App — Software Requirements Specification (SRS)

**Project:** Andes Pádel — Padel Court Reservation & Management System
**Client:** Andes Pádel (Quito, Ecuador)
**Version:** 1.0
**Status:** Draft for review
**Date:** 2026-08-12
**Standards:** ISO/IEC/IEEE 29148:2018 · ISO/IEC 25010:2011 · ISO/IEC 27001:2022 · ISO 9001:2015 · GDPR (EU) 2016/679

---

## Purpose

This document set is the authoritative requirements baseline for the Andes Pádel court reservation system. It defines **every module**, **every feature**, and **every non-functional constraint** required to build the complete product:

- **Backend:** Django 5.x + Django REST Framework + PostgreSQL
- **Mobile:** Flutter (iOS + Android, single codebase)
- **Web Admin:** Customized Django Admin
- **Deployment:** Settings-package driven (no environment-variable secrets)

The scope defined here is the *complete contract* for implementation, derived from the approved proposal (**Andes Pádel — Desarrollo e Implementación de Aplicación Móvil de Reservas**, USD 350,00, TrustX). Nothing may be added, removed, or altered without a documented change through the control process in `00-document-control.md`.

---

## Document Set Index

| Doc | Title | Content |
|-----|-------|---------|
| 00 | `00-document-control.md` | Approvals, change log, requirement numbering legend, abbreviations |
| 01 | `01-introduction.md` | §5.2 Purpose, scope, product overview, definitions, references |
| 02 | `02-overall-description.md` | §5.3 Product perspective, user classes, operating environment, constraints, assumptions, dependencies |
| 03 | `03-functional-requirements.md` | §5.4 Every functional requirement F-0001+ across modules M01–M17 |
| 04 | `04-nonfunctional-requirements.md` | NFR-xxxx per ISO/IEC 25010 quality model, ISO 27001 security controls |
| 05 | `05-interface-requirements.md` | REST API contract, Flutter UI, Web Admin UI, external interfaces |
| 06 | `06-data-requirements.md` | Data dictionary, integrity rules, retention, GDPR erasure |
| 07 | `07-traceability-matrix.md` | F-xxx ↔ Module ↔ ISO 25010 ↔ ISO 27001 ↔ Test case |
| 08 | `08-verification-matrix.md` | Verification method and acceptance criteria per requirement |

---

## How to Read This SRS

1. **Modules (M01–M17)** define logical functional areas.
2. **Features (F-xxxx)** are individual functional requirements; each belongs to exactly one module.
3. **Non-functional requirements (NFR-xxxx)** apply system-wide and cross-reference features.
4. **Traceability** is maintained in `07` and `08`; every requirement is testable.

## Conventions

- Text `Monospace` = identifiers, fields, endpoint names, settings keys.
- **v2** = future scope; documented but NOT built in the first release.
- Requirement IDs are stable. Never reuse a retired ID.

---

## Source Requirements Document

The business requirements were collected in two client documents:
1. `levantamiento-requisitos-padel.docx` (Padel Court Management Application — Requirements Survey, 20 questions).
2. Approved proposal **"Andes Pádel — Desarrollo e Implementación de Aplicación Móvil de Reservas"** (scope: Users, Reservations, Administration, Events/Tournaments, Tech Infrastructure, Mobile App).

The survey answers were not provided by the client; the SRS therefore records the agreed **assumptions** in `02-overall-description.md` §7, which constitute the baseline for v1.
