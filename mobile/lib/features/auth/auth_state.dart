import 'package:flutter/foundation.dart';

import '../../core/api_client.dart';
import '../../core/storage.dart';

class AuthState extends ChangeNotifier {
  AuthState({required ApiClient api, required TokenStorage storage})
      : _api = api,
        _storage = storage;

  final ApiClient _api;
  final TokenStorage _storage;

  bool _initialized = false;
  bool _authenticated = false;
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _user;

  bool get initialized => _initialized;
  bool get authenticated => _authenticated;
  bool get loading => _loading;
  String? get error => _error;
  Map<String, dynamic>? get user => _user;

  Future<void> restoreSession() async {
    final access = await _storage.read(SecureTokenStorage.accessKey);
    if (access != null && access.isNotEmpty) {
      _authenticated = true;
    }
    _initialized = true;
    notifyListeners();
  }

  Future<void> _run(Future<void> Function() action) async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      await action();
    } catch (e) {
      _error = e.toString();
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
    required String fullName,
    String? phone,
  }) {
    return _run(() async {
      await _api.post('/auth/register/', data: {
        'email': email.trim().toLowerCase(),
        'password': password,
        'full_name': fullName,
        'phone': phone ?? '',
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
    final access = data['access'] as String;
    final refresh = data['refresh'] as String;
    if (_storage is SecureTokenStorage) {
      await _storage.saveTokens(access: access, refresh: refresh);
    } else {
      await _storage.write(SecureTokenStorage.accessKey, access);
      await _storage.write(SecureTokenStorage.refreshKey, refresh);
    }
    _user = data['user'] as Map<String, dynamic>?;
    _authenticated = true;
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
    if (_storage is SecureTokenStorage && refresh != null) {
      await _api.logout(refresh);
    } else {
      await _storage.clearTokens();
    }
    _user = null;
    _authenticated = false;
    notifyListeners();
  }
}
