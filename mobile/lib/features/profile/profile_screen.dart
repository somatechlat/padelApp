import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import '../../core/api_client.dart';
import '../../core/locale_controller.dart';
import '../../core/theme/app_theme.dart';
import '../auth/auth_state.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  static const _languages = [
    ('es', 'Español'),
    ('en', 'English'),
    ('pt', 'Português'),
    ('ca', 'Català'),
  ];

  Future<void> _confirmLogout(BuildContext context) async {
    final l10n = AppLocalizations.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.logout),
        content: Text(l10n.logoutConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.confirm),
          ),
        ],
      ),
    );
    if (confirmed == true && context.mounted) {
      final auth = context.read<AuthState>();
      final nav = Navigator.of(context);
      await auth.logout();
      // AuthGate also flips to LoginScreen; this clears any nested stack.
      nav.pushNamedAndRemoveUntil('/login', (route) => false);
    }
  }

  /// Apple Guideline 5.1.1(v): an app that supports account creation must
  /// offer account deletion from inside the app. The backend already has
  /// POST /api/gdpr/me/erase/; this wires it to a button the user can reach.
  Future<void> _confirmDeleteAccount(BuildContext context) async {
    final l10n = AppLocalizations.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.deleteAccount),
        content: Text(l10n.deleteAccountConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.cancel),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.deleteAccount),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted) return;

    final api = context.read<ApiClient>();
    final auth = context.read<AuthState>();
    final nav = Navigator.of(context);
    try {
      await api.post('/gdpr/me/erase/');
    } catch (_) {
      // Even if the request fails the session is not something to keep
      // hanging around after the user asked to be erased; log out either way.
    }
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(l10n.deleteAccountDone)),
    );
    await auth.logout();
    nav.pushNamedAndRemoveUntil('/login', (route) => false);
  }

  Future<void> _pickLanguage(BuildContext context) async {
    final l10n = AppLocalizations.of(context);
    final locale = context.read<LocaleController>();
    final auth = context.read<AuthState>();
    final api = context.read<ApiClient>();
    final selected = await showDialog<String>(
      context: context,
      builder: (context) => RadioGroup<String>(
        groupValue: locale.code,
        onChanged: (v) => Navigator.of(context).pop(v),
        child: SimpleDialog(
          title: Text(l10n.language),
          children: [
            for (final (code, name) in _languages)
              RadioListTile<String>(
                value: code,
                title: Text(name),
              ),
          ],
        ),
      ),
    );
    if (selected == null || selected == locale.code) return;
    await locale.setLanguage(selected);
    auth.applyUserPatch({'language_code': selected});
    try {
      await api.patch('/auth/me/', data: {'language_code': selected});
    } catch (_) {
      // Local language is already applied; backend sync will happen on next login.
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final auth = context.watch<AuthState>();
    final user = auth.user;
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: Text(l10n.profile)),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 36,
                    backgroundColor: AppColors.accentSoft,
                    child: Icon(
                      Icons.person_outline,
                      size: 36,
                      color: scheme.primary,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    (user?['full_name'] as String?) ?? '',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: AppSpacing.xxs),
                  Text(
                    (user?['email'] as String?) ?? '',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.badge_outlined),
                  title: Text(l10n.role),
                  trailing: Text(_roleLabel(l10n, '${user?['role']}')),
                ),
                ListTile(
                  leading: const Icon(Icons.language),
                  title: Text(l10n.language),
                  trailing: Text(
                    _languages
                        .firstWhere((l) =>
                            l.$1 == context.read<LocaleController>().code)
                        .$2,
                  ),
                  onTap: () => _pickLanguage(context),
                ),
                const Divider(),
                ListTile(
                  leading: Icon(
                    Icons.logout,
                    color: AppColors.danger,
                  ),
                  title: Text(
                    l10n.logout,
                    style: TextStyle(color: AppColors.danger),
                  ),
                  onTap: () => _confirmLogout(context),
                ),
                ListTile(
                  leading: Icon(
                    Icons.delete_outline,
                    color: AppColors.danger,
                  ),
                  title: Text(
                    l10n.deleteAccount,
                    style: TextStyle(color: AppColors.danger),
                  ),
                  onTap: () => _confirmDeleteAccount(context),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _roleLabel(AppLocalizations l10n, String role) {
    switch (role) {
      case 'cliente':
        return l10n.role_cliente;
      case 'recepcionista':
        return l10n.role_recepcionista;
      case 'gerente':
        return l10n.role_gerente;
      case 'dueno':
        return l10n.role_dueno;
      case 'superadmin':
        return l10n.role_superadmin;
      default:
        return role;
    }
  }
}
