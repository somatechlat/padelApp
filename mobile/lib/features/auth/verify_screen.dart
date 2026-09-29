import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:padel_app/core/friendly_error.dart';
import 'package:padel_app/core/form_validation.dart';
import 'auth_state.dart';
import 'widgets/auth_scaffold.dart';

class VerifyScreen extends StatefulWidget {
  const VerifyScreen({super.key, required this.email});

  final String email;

  @override
  State<VerifyScreen> createState() => _VerifyScreenState();
}

class _VerifyScreenState extends State<VerifyScreen> {
  final _code = TextEditingController();
  String? _codeError;

  @override
  void dispose() {
    _code.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    final codeErr = FormValidation.code(l10n, _code.text);
    setState(() => _codeError = codeErr);
    if (codeErr != null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(codeErr)));
      return;
    }
    final auth = context.read<AuthState>();
    await auth.verify(widget.email, _code.text.trim());
    if (mounted && auth.authenticated) {
      Navigator.of(context).pushNamedAndRemoveUntil('/shell', (route) => false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AuthScaffold(
      title: l10n.verify,
      subtitle: l10n.verifySubtitle,
      appBarTitle: l10n.verify,
      showBackButton: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            widget.email,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
          ),
          const SizedBox(height: 24),
          TextField(
            controller: _code,
            keyboardType: TextInputType.number,
            maxLength: 6,
            onChanged: (_) => setState(() => _codeError = null),
            onSubmitted: (_) => _submit(),
            decoration: InputDecoration(
              labelText: l10n.code,
              errorText: _codeError,
              prefixIcon: const Icon(Icons.pin_outlined),
              border: const OutlineInputBorder(),
            ),
          ),
          Consumer<AuthState>(
            builder: (context, auth, _) {
              if (auth.hasError) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(
                    friendlyErrorMessage(auth.lastError!, l10n),
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                    textAlign: TextAlign.center,
                  ),
                );
              }
              return const SizedBox.shrink();
            },
          ),
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
                  : Text(l10n.verifyButton),
            ),
          ),
          TextButton(
            onPressed: () async {
              final auth = context.read<AuthState>();
              final messenger = ScaffoldMessenger.of(context);
              await auth.resendVerification(widget.email);
              if (!context.mounted) return;
              final msg = auth.hasError
                  ? friendlyErrorMessage(auth.lastError!, l10n)
                  : l10n.resendCode;
              messenger.showSnackBar(SnackBar(content: Text(msg)));
            },
            child: Text(l10n.resendCode),
          ),
        ],
      ),
    );
  }
}
