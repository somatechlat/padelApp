import 'package:flutter/widgets.dart';

import 'storage.dart';

/// Holds the app UI language and persists it across sessions.
///
/// The language is controlled ONLY by the in-app picker (profile screen).
/// Nothing else may change it: not the device locale, not the backend
/// `language_code`, and not an error/rebuild. That is what made the UI jump
/// to Portuguese unprompted.
class LocaleController extends ChangeNotifier {
  LocaleController({required TokenStorage storage}) : _storage = storage;

  /// v2 key: the old `app_language` slot was also written by a server-side
  /// seed and ended up holding a leaked `pt`. Ignore those values so the
  /// default is Spanish again until the user picks in Profile.
  static const _key = 'app_language_v2';

  /// Club default. Never follow the device locale.
  static const fallbackCode = 'es';

  /// Languages the app actually ships. Must match
  /// `AppLocalizations.supportedLocales`.
  ///
  /// This is load-bearing: the generated `AppLocalizations` lookup *throws*
  /// for a locale with no translation class, so a `pt`/`ca` left in storage
  /// from before those languages were dropped would crash the app on launch.
  static const supportedCodes = {'es', 'en'};

  final TokenStorage _storage;

  /// Starts as Spanish. Never null — a null locale lets Flutter fall back to
  /// the device language (that is how the UI showed Portuguese).
  Locale _locale = const Locale(fallbackCode);

  Locale get locale => _locale;

  /// True once the user picked a language explicitly in Profile.

  String get code => _locale.languageCode;

  Future<void> load() async {
    String? stored;
    try {
      stored = await _storage.read(_key);
    } catch (_) {
      stored = null;
    }
    // Only a Profile pick may change the language, and only to a language we
    // still ship. Anything else stays Spanish.
    if (stored != null && supportedCodes.contains(stored)) {
      _locale = Locale(stored);
    }
    notifyListeners();
  }

  /// Apply a language chosen in Profile. This is the ONLY public setter.
  Future<void> setLanguage(String code) async {
    // The picker only offers supported languages, but guard anyway: persisting
    // an unsupported code would make `load()` fall back on the next launch.
    if (!supportedCodes.contains(code)) return;
    try {
      await _storage.write(_key, code);
    } catch (_) {
      // Keep the in-memory choice even if secure storage is unavailable.
    }
    _locale = Locale(code);
    notifyListeners();
  }
}
