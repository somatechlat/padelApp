import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/core/api_client.dart';
import 'package:padel_app/core/storage.dart';
import 'package:padel_app/features/auth/auth_state.dart';

/// Real local API (Docker backend on :8000). No mocks, no fakes.
const kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000/api',
);

FileTokenStorage newTokenStorage() {
  final dir = Directory.systemTemp.createTempSync('andes_padel_tokens_');
  return FileTokenStorage(File('${dir.path}/tokens.json'));
}

ApiClient realApi({String? baseUrl, TokenStorage? storage}) {
  return ApiClient(
    storage: storage ?? newTokenStorage(),
    baseUrl: baseUrl ?? kApiBaseUrl,
  );
}

String uniqueEmail() {
  final ts = DateTime.now().microsecondsSinceEpoch;
  return 'test.user.$ts@andespadel.test';
}

void main() {
  setUpAll(() {
    // Pure `test()` — real HTTP is allowed (no TestWidgetsFlutterBinding).
    final client = Dio(BaseOptions(baseUrl: kApiBaseUrl));
    addTearDown(client.close);
    // Fail fast if Docker backend is not running.
    expect(
      () async => await client.get('/courts/'),
      returnsNormally,
      reason: 'Docker backend must be up on $kApiBaseUrl',
    );
  });

  test('login stores real tokens and authenticates', () async {
    final storage = newTokenStorage();
    final auth = AuthState(api: realApi(storage: storage), storage: storage);

    await auth.login('cliente@andespadel.com', 'Andes12345!');

    expect(auth.authenticated, isTrue, reason: 'error=${auth.lastError}');
    final access = await storage.read(SecureTokenStorage.accessKey);
    final refresh = await storage.read(SecureTokenStorage.refreshKey);
    expect(access, isNotEmpty);
    expect(refresh, isNotEmpty);
  });

  test('register creates a real account without a session', () async {
    final storage = newTokenStorage();
    final auth = AuthState(api: realApi(storage: storage), storage: storage);
    final email = uniqueEmail();

    await auth.register(
      email: email,
      password: 'pass12345',
      firstName: 'Ana',
      lastName: 'Prueba',
      birthDate: '1995-04-12',
      skillLevelId: null,
    );

    expect(auth.error, isNull, reason: '${auth.lastError}');
    expect(auth.authenticated, isFalse);
  });

  test('requestReset reports success for known format email', () async {
    final storage = newTokenStorage();
    final auth = AuthState(api: realApi(storage: storage), storage: storage);

    await auth.requestReset('cliente@andespadel.com');

    expect(auth.error, isNull, reason: '${auth.lastError}');
  });

  test('restoreSession authenticates when real token exists', () async {
    final storage = newTokenStorage();
    final auth = AuthState(api: realApi(storage: storage), storage: storage);
    await auth.login('cliente@andespadel.com', 'Andes12345!');

    final auth2 = AuthState(api: realApi(storage: storage), storage: storage);
    await auth2.restoreSession();
    expect(auth2.authenticated, isTrue);
    expect(auth2.initialized, isTrue);
  });

  test('logout clears real stored tokens', () async {
    final storage = newTokenStorage();
    final auth = AuthState(api: realApi(storage: storage), storage: storage);
    await auth.login('cliente@andespadel.com', 'Andes12345!');
    await auth.restoreSession();
    await auth.logout();

    expect(auth.authenticated, isFalse);
    expect(await storage.read(SecureTokenStorage.accessKey), isNull);
    expect(await storage.read(SecureTokenStorage.refreshKey), isNull);
  });

  test('login rejects bad password against real API', () async {
    final storage = newTokenStorage();
    final auth = AuthState(api: realApi(storage: storage), storage: storage);

    await auth.login('cliente@andespadel.com', 'wrong-password');

    expect(auth.authenticated, isFalse);
    expect(auth.lastError, isNotNull);
  });
}
