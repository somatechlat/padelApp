import 'dart:convert';
import 'dart:io';

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

/// Real file-backed token storage (no in-memory fakes). Used by tests and
/// any host without a platform secure-storage plugin.
class FileTokenStorage implements TokenStorage {
  FileTokenStorage(this._file);

  final File _file;

  Map<String, String> _load() {
    if (!_file.existsSync()) return {};
    try {
      final raw = jsonDecode(_file.readAsStringSync());
      if (raw is Map) {
        return raw.map((k, v) => MapEntry(k.toString(), v.toString()));
      }
    } catch (_) {
      // Corrupt file — start empty and overwrite on next write.
    }
    return {};
  }

  void _save(Map<String, String> values) {
    _file.parent.createSync(recursive: true);
    _file.writeAsStringSync(jsonEncode(values));
  }

  @override
  Future<String?> read(String key) async => _load()[key];

  @override
  Future<void> write(String key, String value) async {
    final data = _load()..[key] = value;
    _save(data);
  }

  @override
  Future<void> delete(String key) async {
    final data = _load()..remove(key);
    _save(data);
  }

  @override
  Future<void> clearTokens() async {
    final data = _load()
      ..remove(SecureTokenStorage.accessKey)
      ..remove(SecureTokenStorage.refreshKey);
    _save(data);
  }
}
