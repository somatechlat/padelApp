import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:padel_app/core/friendly_error.dart';
import 'package:padel_app/core/form_validation.dart';
import 'package:padel_app/core/widgets/password_field.dart';
import '../../core/api_client.dart';
import 'auth_state.dart';
import 'widgets/auth_scaffold.dart';

class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({super.key});

  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final _current = TextEditingController();
  final _new = TextEditingController();
  final _confirm = TextEditingController();
  String? _currentError;
  String? _newError;
  String? _confirmError;
  bool _loading = false;

  @override
  void dispose() {
    _current.dispose();
    _new.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    final currentErr = _current.text.isEmpty ? l10n.currentPasswordRequired : null;
    final newErr = FormValidation.password(l10n, _new.text);
    final confirmErr = _new.text == _confirm.text ? null : l10n.passwordsDontMatch;
    setState(() {
      _currentError = currentErr;
      _newError = newErr;
      _confirmError = confirmErr;
    });
    if (currentErr != null || newErr != null || confirmErr != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(currentErr ?? newErr ?? confirmErr!)),
      );
      return;
    }

    setState(() => _loading = true);
    try {
      await context.read<ApiClient>().post('/auth/password/change/', data: {
        'old_password': _current.text,
        'new_password': _new.text,
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(friendlyErrorMessage(e, l10n))),
      );
      return;
    }
    if (!mounted) return;
    setState(() => _loading = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(l10n.passwordChanged)),
    );
    // Server blacklists outstanding tokens on password change — local logout.
    await context.read<AuthState>().logout();
    if (!mounted) return;
    Navigator.of(context).pushNamedAndRemoveUntil('/login', (route) => false);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AuthScaffold(
      title: l10n.changePassword,
      subtitle: l10n.changePasswordSubtitle,
      appBarTitle: l10n.changePassword,
      showBackButton: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          PasswordField(
            controller: _current,
            label: l10n.currentPassword,
            errorText: _currentError,
            onChanged: (_) => setState(() => _currentError = null),
          ),
          const SizedBox(height: 16),
          PasswordField(
            controller: _new,
            label: l10n.newPassword,
            errorText: _newError,
            onChanged: (_) => setState(() => _newError = null),
          ),
          const SizedBox(height: 16),
          PasswordField(
            controller: _confirm,
            label: l10n.confirmPassword,
            errorText: _confirmError,
            onChanged: (_) => setState(() => _confirmError = null),
            onSubmitted: (_) => _submit(),
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _loading ? null : _submit,
            style: FilledButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
            child: _loading
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(l10n.saveButton),
          ),
        ],
      ),
    );
  }
}
