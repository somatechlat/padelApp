import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:padel_app/core/widgets/password_field.dart';
import 'auth_state.dart';
import 'widgets/auth_scaffold.dart';

class ResetConfirmScreen extends StatefulWidget {
  const ResetConfirmScreen({super.key, required this.email});

  final String email;

  @override
  State<ResetConfirmScreen> createState() => _ResetConfirmScreenState();
}

class _ResetConfirmScreenState extends State<ResetConfirmScreen> {
  final _code = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();

  @override
  void dispose() {
    _code.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    if (_password.text != _confirm.text) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(l10n.passwordMismatch)));
      return;
    }
    final auth = context.read<AuthState>();
    await auth.resetConfirm(widget.email, _code.text, _password.text);
    if (!mounted) return;
    if (!auth.hasError) {
      Navigator.of(context).popUntil((route) => route.isFirst);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AuthScaffold(
      title: l10n.resetConfirm,
      subtitle: l10n.resetConfirmSubtitle,
      appBarTitle: l10n.resetConfirm,
      showBackButton: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextField(
            controller: _code,
            keyboardType: TextInputType.number,
            maxLength: 6,
            textInputAction: TextInputAction.next,
            decoration: InputDecoration(
              labelText: l10n.code,
              prefixIcon: const Icon(Icons.pin_outlined),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          PasswordField(
            controller: _password,
            label: l10n.password,
            textInputAction: TextInputAction.next,
          ),
          const SizedBox(height: 16),
          PasswordField(
            controller: _confirm,
            label: l10n.confirmPassword,
            textInputAction: TextInputAction.done,
            onSubmitted: (_) => _submit(),
          ),
          const SizedBox(height: 24),
          Consumer<AuthState>(
            builder: (context, auth, _) => FilledButton(
              onPressed: auth.loading ? null : _submit,
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: auth.loading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(l10n.saveButton),
            ),
          ),
        ],
      ),
    );
  }
}
