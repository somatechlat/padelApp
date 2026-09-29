import 'dart:io';

import 'package:padel_app/core/storage.dart';

/// Map-backed [TokenStorage] for hermetic tests: no filesystem, no platform
/// secure-storage plugin, no network.
class InMemoryTokenStorage implements TokenStorage {
  final Map<String, String> _values = <String, String>{};

  @override
  Future<String?> read(String key) async => _values[key];

  @override
  Future<void> write(String key, String value) async {
    _values[key] = value;
  }

  @override
  Future<void> delete(String key) async {
    _values.remove(key);
  }

  @override
  Future<void> clearTokens() async {
    _values.remove(SecureTokenStorage.accessKey);
    _values.remove(SecureTokenStorage.refreshKey);
  }
}

/// Fresh file-backed [FileTokenStorage] in a new temp directory.
///
/// Shared by the tests so the `newTokenStorage()` copy-paste stays in one
/// place. Still hermetic: the file lives under `Directory.systemTemp` and is
/// never read over the network.
FileTokenStorage newTokenStorage() {
  final dir = Directory.systemTemp.createTempSync('andes_padel_tokens_');
  return FileTokenStorage(File('${dir.path}/tokens.json'));
}
