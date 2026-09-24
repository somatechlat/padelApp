import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import 'auth_state.dart';
import 'reset_confirm_screen.dart';
import 'widgets/auth_scaffold.dart';

class ResetScreen extends StatefulWidget {
  const ResetScreen({super.key});

  @override
  State<ResetScreen> createState() => _ResetScreenState();
}

class _ResetScreenState extends State<ResetScreen> {
  final _email = TextEditingController();

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    final auth = context.read<AuthState>();
    await auth.requestReset(_email.text);
    if (!mounted) return;
    if (!auth.hasError) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(l10n.codeSent)));
      Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ResetConfirmScreen(
            email: _email.text.trim().toLowerCase(),
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AuthScaffold(
      title: l10n.resetPassword,
      subtitle: l10n.resetSubtitle,
      appBarTitle: l10n.resetPassword,
      showBackButton: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            autofillHints: const [AutofillHints.email],
            onSubmitted: (_) => _submit(),
            decoration: InputDecoration(
              labelText: l10n.email,
              prefixIcon: const Icon(Icons.mail_outline),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
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
                  : Text(l10n.resetButton),
            ),
          ),
        ],
      ),
    );
  }
}
