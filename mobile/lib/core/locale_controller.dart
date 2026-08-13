import 'package:flutter/widgets.dart';

import 'storage.dart';

/// Holds the app UI language and persists it across sessions.
///
/// The backend is kept in sync through `PATCH /auth/me/ {language_code}`
/// (done by the profile screen); the last user choice is stored locally so the
/// app opens in the right language even while offline.
class LocaleController extends ChangeNotifier {
  LocaleController({required TokenStorage storage}) : _storage = storage;

  static const _key = 'app_language';

  final TokenStorage _storage;

  Locale? _locale;
  bool _loaded = false;

  Locale? get locale => _locale;
  bool get loaded => _loaded;
  String get code => _locale?.languageCode ?? 'es';

  Future<void> load() async {
    final stored = await _storage.read(_key);
    _locale = stored != null && stored.isNotEmpty ? Locale(stored) : null;
    _loaded = true;
    notifyListeners();
  }

  Future<void> setLanguage(String code) async {
    await _storage.write(_key, code);
    _locale = Locale(code);
    notifyListeners();
  }
}
