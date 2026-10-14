
## 2026-10-06 security-flow-audit — ACTIVE
| Path | Owner | Scope |
|---|---|---|
| apps/gdpr/** | backend-security | erase PII scrub |
| apps/users/** | backend-security + flutter-auth (urls/views vs mobile) | split by extension |
| apps/adminpanel/views/users.py | backend-security | is_active sync |
| apps/users/permissions.py | backend-security | status gate |
| apps/verification/** | backend-security | attempts locking |
| mobile/lib/features/profile/** | flutter-ui | erase + change password UI |
| mobile/lib/features/auth/** | flutter-ui | session/verify/register |
| mobile/lib/core/** | flutter-ui | api/auth helpers |
| mobile/lib/core/l10n/app_*.arb | flutter-ui | all new keys |
| apps/*/tests*.py | qa-tests | tests only |
| mobile/test/** | qa-tests | tests only |
