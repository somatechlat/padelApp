import 'package:padel_app/core/l10n/app_localizations.dart';

/// Shared field validation for every form in the app.
/// Always show a specific, localized message — never silent submit.
class FormValidation {
  static final _emailRe = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

  static String? required(AppLocalizations l10n, String? value,
      {String? label}) {
    if (value == null || value.trim().isEmpty) {
      return label == null
          ? l10n.fieldRequired
          : l10n.fieldRequiredNamed(label);
    }
    return null;
  }

  static String? email(AppLocalizations l10n, String? value) {
    final v = (value ?? '').trim();
    if (v.isEmpty) return l10n.emailRequired;
    if (!_emailRe.hasMatch(v)) return l10n.emailInvalid;
    return null;
  }

  static String? password(AppLocalizations l10n, String? value) {
    final v = value ?? '';
    if (v.isEmpty) return l10n.passwordRequired;
    if (v.length < 8) return l10n.passwordTooShort;
    return null;
  }

  static String? code(AppLocalizations l10n, String? value) {
    final v = (value ?? '').trim();
    if (v.isEmpty) return l10n.codeRequired;
    if (v.length != 6 || int.tryParse(v) == null) return l10n.codeInvalid;
    return null;
  }

  static String? name(AppLocalizations l10n, String? value, {String? label}) {
    final v = (value ?? '').trim();
    if (v.isEmpty) {
      return label == null
          ? l10n.fieldRequired
          : l10n.fieldRequiredNamed(label);
    }
    if (v.length < 2) return l10n.fieldTooShort;
    return null;
  }

  /// Returns the first error among [checks], or null when all pass.
  static String? first(List<String? Function()> checks) {
    for (final check in checks) {
      final err = check();
      if (err != null) return err;
    }
    return null;
  }
}
