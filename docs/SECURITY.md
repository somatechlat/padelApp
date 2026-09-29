# Andes Padel — Security Model

Operational reference for how authorization and payment safety actually work in
this codebase. Read alongside `AGENTS.md` §3b for the short form.

Last verified against the code: 2026-09-29.

---

## 1. Roles

Five roles, strictly ordered:

```
cliente < recepcionista < gerente < dueno < superadmin
```

Defined on the user model (`apps/users/models.py`). Comparison helpers live in
`apps/adminpanel/mixins.py`:

| Helper | Meaning |
|---|---|
| `ROLE_LEVEL` | role → integer, for "is this above me?" checks |
| `user_role(user)` | the role string, or `None` |
| `require_roles(request, roles)` | raise `PermissionDenied` unless the actor is in `roles` |

Role sets in `apps/adminpanel/admin_base.py`:

| Constant | Members |
|---|---|
| `STAFF_ROLES` | recepcionista, gerente, dueno, superadmin |
| `MANAGER_ROLES` | gerente, dueno, superadmin |
| `FINANCIAL_ROLES` | dueno, superadmin |

---

## 2. Two gates, not one

The staff dashboard at `/adminpanel/` and Django admin at `/admin/` are gated
separately and **do not share logic**. Do not assume a rule on one applies to
the other.

### 2.1 Custom admin panel

View mixins (`apps/adminpanel/mixins.py`) gate whole views:

| Mixin | Allowed roles | Used for |
|---|---|---|
| `StaffRequiredMixin` | `STAFF_ROLES` | calendar, courts, banners, events, payments, users, dashboard |
| `ManagerRequiredMixin` | `MANAGER_ROLES` | reports page |
| `FinanceRequiredMixin` | `FINANCIAL_ROLES` | club settings, audit log |

Per-action checks inside a `post()` handler use `require_roles`. This is the
right pattern when a single view mixes routine and privileged actions — for
example `PaymentsAdminView`, where confirming a transfer is front-desk work and
issuing a refund is not.

**Failures raise `PermissionDenied` (403).** They are not converted to
`messages.error` + redirect. A soft failure is scriptable and invisible in the
request log; a 4xx is neither.

### 2.2 Django admin

`RoleGatedAdmin` (`apps/adminpanel/admin_base.py`) is coarser: superadmin/dueno
get everything, gerente is barred from add/delete on financial models,
recepcionista is barred from financial models entirely. Treat it as a separate
surface to tighten. See `AGENTS.md` §10.

---

## 3. Action matrix

What each role may actually do in `/adminpanel/`:

| Action | recepcionista | gerente | dueno / superadmin |
|---|---|---|---|
| Calendar, courts, banners, events | yes | yes | yes |
| Create/cancel booking, block slot | yes | yes | yes |
| **Confirm / reject bank transfer** | **yes** | yes | yes |
| Record cash | yes | yes | yes |
| **Refund** | no | no | **yes** |
| **Change user status** (suspend/activate) | no | **yes** | yes |
| **Change user role** | no | no | **yes** |
| Club settings (bank details, policies) | no | no | **yes** |
| Audit log | no | no | **yes** |
| Reports — booking counts | no | **yes** | yes |
| Reports — revenue / per-court income / top customers | no | restricted | **yes** |
| Reports — CSV export (customer emails) | no | no | **yes** |

---

## 4. Why the boundaries sit where they do

These are decisions, not accidents. Revisit them deliberately.

**Transfer confirm/reject → receptionists.** The receipt is verified at the
counter by whoever is standing there. Routing it through a manager queues
customers at the desk for a reversible, non-financial action. Money still does
not move until someone issues a refund.

**Refund → owners only.** Refund moves money out of the club. It is the one
irreversible financial action in the panel.

**Role changes refuse privilege escalation with 403.** A `dueno` cannot mint a
`superadmin`, and nobody can assign a role above their own
(`role_level(new) > role_level(actor)` → `PermissionDenied`). Previously this
was a flash message and a redirect, which reads like validation rather than an
attack.

**The last `superadmin` cannot be demoted.** Demoting the only account at the
top of the hierarchy locks every privileged surface with no way back in. The
guard refuses the change until another `superadmin` exists.

**Status changes are manager+.** Suspending an account locks its owner out.
That is operational management, not front-desk work — a receptionist must not
be able to lock anyone out, including a manager or an owner.

**Revenue is owner-only.** `ReportsAdminView` does not compute the aggregates
at all unless the actor is in `FINANCIAL_ROLES`. It is not a template-level
`if`: the queries never run, so a template slip cannot leak the numbers.
Managers see booking counts and the literal `Restringido` where the money
figures would be.

---

## 5. Payment service safety bounds

RBAC decides *who* may call an operation. The service layer decides whether the
operation is safe to run at all, because the same method can be reached from
more than one view (and from Celery). Both layers are required.

`apps/payments/services.py`:

| Method | Guarantee |
|---|---|
| `confirm_transfer` | **Idempotent** and `transaction.atomic()`. A double-click or two receptionists on the same receipt do not send two notifications or re-run the booking transition. A second call on an already-`CAPTURED` payment returns immediately. |
| `reject_transfer` | Refuses any payment no longer `PENDING` / `PENDING_TRANSFER`, raising `ValueError`. |
| `refund` | Refuses a non-positive amount, an amount greater than what was captured, and a second refund of the same payment. Amounts are coerced via `Decimal(str(...))` because `payment.amount` can arrive as a bare string on an unsaved instance. |
| `_record_cash_payment` | `transaction.atomic()` around the `Payment` insert **and** the booking transition. If `booking.transition_to("confirmed")` raises — cancelled in a race, illegal transition, lock timeout — the `Payment` row rolls back with it. No orphan. |

The Stripe call in `refund` happens *after* the bounds checks and *before* the
status write, so an over-amount refund never reaches Stripe.

---

## 6. Rules that keep this true

1. **Business logic belongs in `services.py`.** Views authorize and dispatch;
   services decide what is safe. Adding a new caller of a payment method must
   not require re-deriving the bounds.
2. **Authorization failures raise `PermissionDenied`.** Never
   `messages.error` + redirect, never a silent no-op.
3. **Never use `_` as a throwaway variable** in any module that calls gettext.
   It shadows gettext and every earlier `_("...")` in the function raises
   `UnboundLocalError` — which is an availability bug on the error path itself.
4. **Never show raw exceptions in the UI** (Django: `DEBUG` must be off in
   prod; Flutter: route through `friendlyErrorMessage`). Exception text leaks
   schema, paths and sometimes values.
5. **Secrets never enter the repo.** `.gitignore` covers Firebase config,
   keystores, `*.ipa`/`*.apk`, service accounts, `runsecrets/`. If you find one
   tracked, `git rm --cached` it and say so in the commit message.

---

## 7. Known gaps

Ordered by cost of ignoring them. Not a checklist — a map.

1. **Firebase API keys remain in git history** (`AIza...` for Android and iOS,
   committed in `d26820e`). Untracking does not erase history.

   **Decision (2026-09-29): do not rotate** — accepted as-is by the owner.

   Worth stating plainly, because the rationale for accepting was "the keys
   will expire soon": that is true of the time-boxed GitHub PAT, which has now
   lapsed on its own. It is **not** true of Google API keys. They do not
   self-expire. They remain valid until revoked in Google Cloud Console or the
   project is shut down.

   The risk is therefore open-ended rather than self-limiting. In practice
   these keys are client-side identifiers (the mobile app has to ship one),
   so they are not a bearer secret in the way a service-account key is — but
   they do authorize the FCM/Identity surfaces they are scoped to, and they
   will keep doing so indefinitely. This entry is a known, owned risk. Do not
   re-raise it as a new finding; revisit only if the decision changes.
2. **Django admin RBAC is coarser than the panel** (see §2.2).
3. **Production target is unset.** A new server and domain replace the
   retired ones; the replacements are not yet supplied. Do not deploy to or
   document the old addresses as live.
4. **No rate limiting on the admin panel `post()` endpoints** beyond Django's
   defaults. They are session-authenticated and staff-only, which bounds the
   risk, but a compromised staff session can still act fast.
5. **Audit log is append-only in spirit, not enforced.** Nothing stops a
   `superadmin` from deleting rows through Django admin.

---

## 8. Tests that pin this down

| Concern | Test |
|---|---|
| Receptionist can confirm/reject transfer | `apps/adminpanel/tests.py::test_recepcionista_can_confirm_transfer` |
| Receptionist cannot refund | `::test_recepcionista_cannot_refund` |
| Receptionist cannot change status | `::test_recepcionista_cannot_change_status` |
| Manager can change status | `::test_gerente_can_change_status` |
| Escalation is 403 | `::test_dueno_cannot_promote_above_self`, `::test_dueno_cannot_promote_to_superadmin` |
| Last superadmin is protected | `::test_last_superadmin_cannot_be_demoted` |
| Revenue hidden from managers | `::test_gerente_sees_no_revenue_on_reports` |
| Revenue shown to owners | `::test_dueno_sees_revenue_on_reports` |
| Refund bounds and idempotency | `apps/payments/tests.py::TestPaymentSafetyBounds` |
| No orphan Payment on failed transition | `::test_cash_on_arrival_leaves_no_orphan_on_failed_transition` |

If you change a boundary in §3, change the matching test in the same commit.
