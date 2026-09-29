import 'package:flutter/material.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';

/// Password [TextField] with show/hide visibility toggle.
class PasswordField extends StatefulWidget {
  const PasswordField({
    super.key,
    required this.controller,
    required this.label,
    this.autofillHints = const [AutofillHints.password],
    this.onSubmitted,
    this.onChanged,
    this.textInputAction,
    this.enabled = true,
    this.prefixIcon = const Icon(Icons.lock_outline),
    this.errorText,
  });

  final TextEditingController controller;
  final String label;
  final Iterable<String>? autofillHints;
  final ValueChanged<String>? onSubmitted;
  final ValueChanged<String>? onChanged;
  final TextInputAction? textInputAction;
  final bool enabled;
  final Widget? prefixIcon;
  final String? errorText;

  @override
  State<PasswordField> createState() => _PasswordFieldState();
}

class _PasswordFieldState extends State<PasswordField> {
  bool _obscure = true;

  void _toggle() => setState(() => _obscure = !_obscure);

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return TextField(
      controller: widget.controller,
      obscureText: _obscure,
      autofillHints: widget.autofillHints,
      onSubmitted: widget.onSubmitted,
      onChanged: widget.onChanged,
      textInputAction: widget.textInputAction,
      enabled: widget.enabled,
      decoration: InputDecoration(
        labelText: widget.label,
        errorText: widget.errorText,
        prefixIcon: widget.prefixIcon,
        border: const OutlineInputBorder(),
        suffixIcon: IconButton(
          onPressed: _toggle,
          tooltip: _obscure ? l10n.showPassword : l10n.hidePassword,
          icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility),
        ),
      ),
    );
  }
}
