import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import 'auth_state.dart';

class VerifyScreen extends StatefulWidget {
  const VerifyScreen({super.key, required this.email});

  final String email;

  @override
  State<VerifyScreen> createState() => _VerifyScreenState();
}

class _VerifyScreenState extends State<VerifyScreen> {
  final _code = TextEditingController();

  @override
  void dispose() {
    _code.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final auth = context.read<AuthState>();
    await auth.verify(widget.email, _code.text);
    if (mounted && auth.authenticated) {
      Navigator.of(context).pushNamedAndRemoveUntil('/shell', (route) => false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.verify)),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    l10n.verifySubtitle,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 8),
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
                    onSubmitted: (_) => _submit(),
                    decoration: InputDecoration(
                      labelText: l10n.code,
                      prefixIcon: const Icon(Icons.pin_outlined),
                      border: const OutlineInputBorder(),
                    ),
                  ),
                  Consumer<AuthState>(
                    builder: (context, auth, _) {
                      if (auth.error != null) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: Text(
                            auth.error!,
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
                    onPressed: () {
                      context.read<AuthState>().requestReset(widget.email);
                    },
                    child: Text(l10n.resendCode),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
