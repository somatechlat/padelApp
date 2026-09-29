import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:padel_app/core/friendly_error.dart';
import 'package:padel_app/core/form_validation.dart';
import 'package:padel_app/core/widgets/password_field.dart';
import '../../core/push_notification_service.dart';
import 'auth_state.dart';
import 'reset_screen.dart';
import 'register_screen.dart';
import 'widgets/auth_scaffold.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  String? _emailError;
  String? _passwordError;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  void _toast(String message) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    final emailErr = FormValidation.email(l10n, _email.text);
    final passErr = FormValidation.password(l10n, _password.text);
    setState(() {
      _emailError = emailErr;
      _passwordError = passErr;
    });
    if (emailErr != null || passErr != null) {
      _toast(emailErr ?? passErr!);
      return;
    }
    final auth = context.read<AuthState>();
    final pushService = context.read<PushNotificationService>();
    final nav = Navigator.of(context);
    await auth.login(_email.text.trim(), _password.text);
    if (!mounted) return;
    if (auth.authenticated) {
      try {
        await pushService.registerToken();
      } catch (_) {}
      nav.pushNamedAndRemoveUntil('/shell', (route) => false);
      return;
    }
    // Wrong password / locked / unverified — always a specific message.
    if (auth.lastError != null) {
      final msg = friendlyErrorMessage(auth.lastError!, l10n);
      // Highlight the field that is wrong when we know.
      final lower = msg.toLowerCase();
      setState(() {
        if (lower.contains('credencial') ||
            lower.contains('contrase') ||
            lower.contains('password')) {
          _passwordError = msg;
          _emailError = null;
        } else if (lower.contains('email') && !lower.contains('verifica')) {
          _emailError = msg;
          _passwordError = null;
        } else {
          _passwordError = msg;
        }
      });
      _toast(msg);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AuthScaffold(
      title: l10n.login,
      subtitle: l10n.loginSubtitle,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            autofillHints: const [AutofillHints.email],
            textInputAction: TextInputAction.next,
            onChanged: (_) => setState(() => _emailError = null),
            decoration: InputDecoration(
              labelText: l10n.email,
              errorText: _emailError,
              prefixIcon: const Icon(Icons.mail_outline),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          PasswordField(
            controller: _password,
            label: l10n.password,
            errorText: _passwordError,
            onChanged: (_) => setState(() => _passwordError = null),
            onSubmitted: (_) => _submit(),
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => const ResetScreen(),
                  ),
                );
              },
              child: Text(l10n.forgotPassword),
            ),
          ),
          const SizedBox(height: 8),
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
                  : Text(l10n.loginButton),
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            alignment: WrapAlignment.center,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text(l10n.noAccount),
              TextButton(
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => const RegisterScreen(),
                    ),
                  );
                },
                child: Text(l10n.registerLink),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
