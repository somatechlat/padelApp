import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:padel_app/core/form_validation.dart';
import 'package:padel_app/core/friendly_error.dart';
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
  String? _codeError;
  String? _passwordError;
  String? _confirmError;

  @override
  void dispose() {
    _code.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    final codeErr = FormValidation.code(l10n, _code.text);
    final passErr = FormValidation.password(l10n, _password.text);
    String? confirmErr;
    if (_confirm.text.isEmpty) {
      confirmErr = l10n.fieldRequiredNamed(l10n.confirmPassword);
    } else if (_password.text != _confirm.text) {
      confirmErr = l10n.passwordMismatch;
    }
    setState(() {
      _codeError = codeErr;
      _passwordError = passErr;
      _confirmError = confirmErr;
    });
    final firstBad =
        FormValidation.first([() => codeErr, () => passErr, () => confirmErr]);
    if (firstBad != null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(firstBad)));
      return;
    }
    final auth = context.read<AuthState>();
    await auth.resetConfirm(widget.email, _code.text.trim(), _password.text);
    if (!mounted) return;
    if (auth.hasError) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(friendlyErrorMessage(auth.lastError!, l10n))),
      );
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(l10n.saveButton)),
    );
    Navigator.of(context).popUntil((route) => route.isFirst);
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
            onChanged: (_) => setState(() => _codeError = null),
            decoration: InputDecoration(
              labelText: l10n.code,
              errorText: _codeError,
              prefixIcon: const Icon(Icons.pin_outlined),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          PasswordField(
            controller: _password,
            label: l10n.password,
            errorText: _passwordError,
            onChanged: (_) => setState(() => _passwordError = null),
            textInputAction: TextInputAction.next,
          ),
          const SizedBox(height: 16),
          PasswordField(
            controller: _confirm,
            label: l10n.confirmPassword,
            errorText: _confirmError,
            onChanged: (_) => setState(() => _confirmError = null),
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
