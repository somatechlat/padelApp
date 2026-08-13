import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/core/storage.dart';
import 'package:padel_app/features/auth/auth_state.dart';

import 'helpers/fake_api.dart';

void main() {
  test('login stores tokens and authenticates', () async {
    final storage = InMemoryTokenStorage();
    final auth = AuthState(api: FakeApi(), storage: storage);

    await auth.login('CLIENTE@andespadel.com', 'pass12345');

    expect(auth.authenticated, isTrue);
    expect(auth.error, isNull);
    expect(await storage.read(SecureTokenStorage.accessKey), 'fake-access');
    expect(await storage.read(SecureTokenStorage.refreshKey), 'fake-refresh');
  });

  test('register does not create a session', () async {
    final auth = AuthState(api: FakeApi(), storage: InMemoryTokenStorage());

    await auth.register(
      email: 'ana@test.com',
      password: 'pass12345',
      fullName: 'Ana',
    );

    expect(auth.authenticated, isFalse);
    expect(auth.error, isNull);
  });

  test('verify without tokens does not authenticate', () async {
    final auth = AuthState(api: FakeApi(), storage: InMemoryTokenStorage());

    await auth.verify('ana@test.com', '123456');

    expect(auth.authenticated, isFalse);
    expect(auth.error, isNull);
  });

  test('requestReset reports success', () async {
    final auth = AuthState(api: FakeApi(), storage: InMemoryTokenStorage());

    await auth.requestReset('ana@test.com');

    expect(auth.error, isNull);
  });

  test('resetConfirm reports success', () async {
    final auth = AuthState(api: FakeApi(), storage: InMemoryTokenStorage());

    await auth.resetConfirm('ana@test.com', '123456', 'nueva12345');

    expect(auth.error, isNull);
  });

  test('restoreSession authenticates when token exists', () async {
    final storage = InMemoryTokenStorage();
    await storage.write(SecureTokenStorage.accessKey, 'fake-access');
    await storage.write(SecureTokenStorage.refreshKey, 'fake-refresh');
    final auth = AuthState(api: FakeApi(), storage: storage);

    await auth.restoreSession();

    expect(auth.authenticated, isTrue);
    expect(auth.initialized, isTrue);
  });

  test('logout clears session and tokens', () async {
    final storage = InMemoryTokenStorage();
    await storage.write(SecureTokenStorage.accessKey, 'fake-access');
    await storage.write(SecureTokenStorage.refreshKey, 'fake-refresh');
    final auth = AuthState(api: FakeApi(), storage: storage);

    await auth.restoreSession();
    await auth.logout();

    expect(auth.authenticated, isFalse);
    expect(await storage.read(SecureTokenStorage.accessKey), isNull);
    expect(await storage.read(SecureTokenStorage.refreshKey), isNull);
  });
}
