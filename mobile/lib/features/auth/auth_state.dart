import 'package:flutter/foundation.dart';

import '../../core/api_client.dart';
import '../../core/friendly_error.dart';
import '../../core/storage.dart';
import '../../core/l10n/app_localizations.dart';

/// Thrown when the API rejects a request with a message the UI may show.
/// Anything else is mapped through [friendlyErrorMessage] before display.
export '../../core/friendly_error.dart' show AppAuthException;

class AuthState extends ChangeNotifier {
  AuthState({required ApiClient api, required TokenStorage storage})
      : _api = api,
        _storage = storage;

  final ApiClient _api;
  final TokenStorage _storage;

  bool _initialized = false;
  bool _authenticated = false;
  bool _loading = false;
  Object? _lastError;
  Map<String, dynamic>? _user;

  bool get initialized => _initialized;
  bool get authenticated => _authenticated;
  bool get loading => _loading;
  Map<String, dynamic>? get user => _user;

  /// Raw error from the last failed auth call. Render with
  /// `friendlyErrorMessage(auth.lastError!, l10n)` — never print it directly.
  Object? get lastError => _lastError;
  bool get hasError => _lastError != null;

  /// Localized, non-technical message for the last failure, or null when the
  /// last call succeeded. Takes [l10n] so a raw DioException/stack-trace dump
  /// can never reach the UI. Never use this as a success signal — check
  /// [authenticated] or the call's own result instead.
  String? error(AppLocalizations l10n) {
    final e = _lastError;
    if (e == null) return null;
    return friendlyErrorMessage(e, l10n);
  }

  Future<void> restoreSession() async {
    try {
      final access = await _storage.read(SecureTokenStorage.accessKey);
      if (access != null && access.isNotEmpty) {
        _authenticated = true;
      }
    } catch (_) {
      // Storage error — treat as not authenticated
    }
    _initialized = true;
    notifyListeners();
  }

  Future<void> _run(Future<void> Function() action) async {
    _loading = true;
    _lastError = null;
    notifyListeners();
    try {
      await action();
    } catch (e) {
      // Store the raw exception; the UI maps it via friendlyErrorMessage.
      _lastError = e;
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> login(String email, String password) {
    return _run(() async {
      final data = await _api.post('/auth/login/', data: {
        'email': email.trim().toLowerCase(),
        'password': password,
      });
      await _saveSession(data);
    });
  }

  Future<void> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String birthDate,
    required int? skillLevelId,
  }) {
    return _run(() async {
      await _api.post('/auth/register/', data: {
        'email': email.trim().toLowerCase(),
        'password': password,
        'first_name': firstName.trim(),
        'last_name': lastName.trim(),
        'birth_date': birthDate,
        if (skillLevelId != null) 'skill_level': skillLevelId,
        'consent_version': '1.0',
      });
    });
  }

  Future<void> verify(String email, String code) {
    return _run(() async {
      final data = await _api.post('/auth/verify/', data: {
        'email': email.trim().toLowerCase(),
        'code': code,
      });
      if (data is Map && data['access'] != null) {
        await _saveSession(data.cast<String, dynamic>());
      }
    });
  }

  Future<void> requestReset(String email) {
    return _run(() async {
      await _api.post('/auth/password-reset/', data: {
        'email': email.trim().toLowerCase(),
      });
    });
  }

  Future<void> resendVerification(String email) {
    return _run(() async {
      await _api.post('/auth/register/', data: {
        'email': email.trim().toLowerCase(),
      });
    });
  }

  Future<void> resetConfirm(String email, String code, String password) {
    return _run(() async {
      await _api.post('/auth/password-reset/confirm/', data: {
        'email': email.trim().toLowerCase(),
        'code': code,
        'password': password,
      });
    });
  }

  Future<void> _saveSession(Map<String, dynamic> data) async {
    final access = data['access'] as String?;
    final refresh = data['refresh'] as String?;
    if (access == null || access.isEmpty) {
      throw Exception('Invalid login response: missing access token');
    }
    if (_storage is SecureTokenStorage) {
      await _storage.saveTokens(access: access, refresh: refresh ?? '');
    } else {
      await _storage.write(SecureTokenStorage.accessKey, access);
      await _storage.write(SecureTokenStorage.refreshKey, refresh ?? '');
    }
    _user = data['user'] as Map<String, dynamic>?;
    _authenticated = true;
  }

  /// Marks session restore finished. Safe to call from `catchError` outside
  /// this class (unlike `notifyListeners`).
  void markInitialized() {
    _initialized = true;
    notifyListeners();
  }

  Future<void> loadMe() async {
    try {
      final data = await _api.get('/auth/me/');
      _user = data as Map<String, dynamic>?;
      notifyListeners();
    } catch (_) {
      // Ignore: user stays logged in with cached session.
    }
  }

  /// Merge a partial user payload (e.g. language change) into the cached user.
  void applyUserPatch(Map<String, dynamic> data) {
    final current = _user;
    if (current != null) {
      current.addAll(data);
      _user = current;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    final refresh = await _storage.read(SecureTokenStorage.refreshKey);
    if (refresh != null && refresh.isNotEmpty) {
      try {
        await _api.logout(refresh);
      } catch (_) {
        // Network/server errors must never block local logout.
      }
    }
    // ALWAYS clear local tokens — never depend on storage subclass type.
    await _storage.clearTokens();
    _user = null;
    _authenticated = false;
    notifyListeners();
  }
}
