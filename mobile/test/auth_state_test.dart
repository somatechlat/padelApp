import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/core/l10n/app_localizations_es.dart';
import 'package:padel_app/core/storage.dart';
import 'package:padel_app/features/auth/auth_state.dart';

import 'helpers/fake_api.dart';
import 'helpers/test_storage.dart';

void main() {
  test('login stores tokens and authenticates', () async {
    final storage = newTokenStorage();
    final api = FakeApi(storage: storage);
    final auth = AuthState(api: api, storage: storage);

    await auth.login('CLIENTE@andespadelclub.com', 'Andes12345!');

    // Real success signals — never just `auth.error, isNull`.
    expect(auth.hasError, isFalse, reason: 'lastError=${auth.lastError}');
    expect(auth.authenticated, isTrue);
    expect(auth.user, isNotNull);
    expect(auth.user?['email'], 'cliente@andespadelclub.com');
    expect(await storage.read(SecureTokenStorage.accessKey), 'fake-access');
    expect(await storage.read(SecureTokenStorage.refreshKey), 'fake-refresh');
  });

  test('register records the account and opens no session', () async {
    final storage = newTokenStorage();
    final api = FakeApi(storage: storage);
    final auth = AuthState(api: api, storage: storage);

    await auth.register(
      email: 'Ana@Test.com',
      password: 'pass12345',
      firstName: 'Ana',
      lastName: 'Prueba',
      birthDate: '1995-04-12',
      skillLevelId: null,
    );

    // The API really received the registration (lower-cased email).
    expect(api.registeredEmails, <String>['ana@test.com']);
    expect(auth.hasError, isFalse, reason: 'lastError=${auth.lastError}');
    expect(auth.authenticated, isFalse);
    expect(auth.user, isNull);
    expect(await storage.read(SecureTokenStorage.accessKey), isNull);
  });

  test('verify without tokens does not authenticate', () async {
    final storage = newTokenStorage();
    final auth = AuthState(api: FakeApi(storage: storage), storage: storage);

    await auth.verify('ana@test.com', '123456');

    expect(auth.hasError, isFalse, reason: 'lastError=${auth.lastError}');
    expect(auth.authenticated, isFalse);
    expect(await storage.read(SecureTokenStorage.accessKey), isNull);
  });

  test('requestReset is accepted for a known-format email', () async {
    final storage = newTokenStorage();
    final api = FakeApi(storage: storage);
    final auth = AuthState(api: api, storage: storage);

    await auth.requestReset('Cliente@Andespadelclub.com');

    expect(api.passwordResetEmails, <String>['cliente@andespadelclub.com']);
    expect(auth.hasError, isFalse, reason: 'lastError=${auth.lastError}');
  });

  test('resetConfirm reports success', () async {
    final storage = newTokenStorage();
    final auth = AuthState(api: FakeApi(storage: storage), storage: storage);

    await auth.resetConfirm('ana@test.com', '123456', 'nueva12345');

    expect(auth.hasError, isFalse, reason: 'lastError=${auth.lastError}');
  });

  test('restoreSession authenticates when a token exists', () async {
    final storage = newTokenStorage();
    await storage.write(SecureTokenStorage.accessKey, 'fake-access');
    await storage.write(SecureTokenStorage.refreshKey, 'fake-refresh');
    final auth = AuthState(api: FakeApi(storage: storage), storage: storage);

    await auth.restoreSession();

    expect(auth.initialized, isTrue);
    expect(auth.authenticated, isTrue);
  });

  test('logout clears session and stored tokens', () async {
    final storage = newTokenStorage();
    final api = FakeApi(storage: storage);
    await storage.write(SecureTokenStorage.accessKey, 'fake-access');
    await storage.write(SecureTokenStorage.refreshKey, 'fake-refresh');
    final auth = AuthState(api: api, storage: storage);

    await auth.restoreSession();
    await auth.logout();

    expect(auth.authenticated, isFalse);
    expect(auth.user, isNull);
    expect(api.loggedOut, isTrue, reason: 'logout must reach the API');
    expect(api.logoutRefreshes, <String>['fake-refresh']);
    expect(await storage.read(SecureTokenStorage.accessKey), isNull);
    expect(await storage.read(SecureTokenStorage.refreshKey), isNull);
  });

  test('login rejects a wrong password with a real 401', () async {
    final storage = newTokenStorage();
    final api = FakeApi(storage: storage);
    final auth = AuthState(api: api, storage: storage);

    await auth.login('cliente@andespadelclub.com', 'wrong-password');

    expect(auth.authenticated, isFalse);
    // Real failure signal: a 401 DioException, not merely "some error".
    expect(auth.hasError, isTrue);
    expect(auth.lastError, isA<DioException>());
    final err = auth.lastError! as DioException;
    expect(err.type, DioExceptionType.badResponse);
    expect(err.response?.statusCode, 401);
    // A rejected login must never mint a session.
    expect(auth.user, isNull);
    expect(await storage.read(SecureTokenStorage.accessKey), isNull);
    expect(await storage.read(SecureTokenStorage.refreshKey), isNull);
  });

  test('network failure surfaces a friendly message, never a raw dump',
      () async {
    // Regression: `AuthState.error` used to drop Dio/network failures on the
    // floor, so any caller checking it showed nothing. It now requires l10n
    // and maps through `friendlyErrorMessage`, returning non-null whenever
    // [hasError] is true. Never assert `error, isNull` as a success signal.
    final storage = newTokenStorage();
    final api = FakeApi(storage: storage)..offline = true;
    final auth = AuthState(api: api, storage: storage);
    final l10n = AppLocalizationsEs();

    await auth.login('cliente@andespadelclub.com', 'Andes12345!');

    expect(auth.hasError, isTrue);
    expect(auth.lastError, isA<DioException>());
    expect((auth.lastError! as DioException).type,
        DioExceptionType.connectionError);

    final message = auth.error(l10n);
    expect(message, isNotNull, reason: 'error(l10n) must surface the failure');
    expect(message, isNot(contains('DioException')));
    expect(message, isNot(contains('Stack Trace')));
    expect(auth.authenticated, isFalse);
  });

  test('error(l10n) is null only when the last call succeeded', () async {
    final storage = newTokenStorage();
    final api = FakeApi(storage: storage);
    final auth = AuthState(api: api, storage: storage);
    final l10n = AppLocalizationsEs();

    await auth.login('cliente@andespadelclub.com', 'Andes12345!');

    expect(auth.authenticated, isTrue);
    expect(auth.hasError, isFalse);
    expect(auth.error(l10n), isNull);
  });
}
