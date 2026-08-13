import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract class TokenStorage {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
  Future<void> delete(String key);
  Future<void> clearTokens();
}

class SecureTokenStorage implements TokenStorage {
  SecureTokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const accessKey = 'jwt_access';
  static const refreshKey = 'jwt_refresh';

  final FlutterSecureStorage _storage;

  @override
  Future<String?> read(String key) => _storage.read(key: key);

  @override
  Future<void> write(String key, String value) =>
      _storage.write(key: key, value: value);

  @override
  Future<void> delete(String key) => _storage.delete(key: key);

  Future<void> saveTokens(
      {required String access, required String refresh}) async {
    await _storage.write(key: accessKey, value: access);
    await _storage.write(key: refreshKey, value: refresh);
  }

  @override
  Future<void> clearTokens() async {
    await _storage.delete(key: SecureTokenStorage.accessKey);
    await _storage.delete(key: SecureTokenStorage.refreshKey);
  }
}

class InMemoryTokenStorage implements TokenStorage {
  final Map<String, String> _values = {};

  @override
  Future<String?> read(String key) async => _values[key];

  @override
  Future<void> write(String key, String value) async => _values[key] = value;

  @override
  Future<void> delete(String key) async => _values.remove(key);

  @override
  Future<void> clearTokens() async {
    _values.remove(SecureTokenStorage.accessKey);
    _values.remove(SecureTokenStorage.refreshKey);
  }
}
