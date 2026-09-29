import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/app.dart';
import 'package:padel_app/core/api_client.dart';
import 'package:padel_app/core/locale_controller.dart';
import 'package:padel_app/core/push_notification_service.dart';
import 'package:padel_app/core/storage.dart';

import 'helpers/fake_api.dart';
import 'helpers/test_storage.dart';

/// Keeps Firebase/platform channels out of widget tests.
class FakePushService extends PushNotificationService {
  FakePushService({required super.api});

  @override
  Future<void> initialize() async {}

  @override
  Future<void> registerToken() async {}
}

Widget buildApp({
  required ApiClient api,
  required TokenStorage storage,
  PushNotificationService? pushService,
}) {
  return AndesPadelApp(
    api: api,
    storage: storage,
    localeController: LocaleController(storage: storage),
    pushService: pushService ?? FakePushService(api: api),
  );
}

void main() {
  testWidgets('shows login screen when no session', (tester) async {
    final storage = newTokenStorage();
    final api = FakeApi(storage: storage);

    await tester.pumpWidget(buildApp(api: api, storage: storage));
    await tester.pumpAndSettle();

    expect(find.byType(Image), findsOneWidget);
    expect(find.text('Iniciar sesión'), findsWidgets);
    expect(find.text('Accede para reservar tu cancha'), findsOneWidget);
    // Shell must NOT be up (its bottom bar is shell-only).
    expect(find.byType(NavigationBar), findsNothing);
    expect(find.byIcon(Icons.person_outline), findsNothing);
  });

  testWidgets('login with valid credentials navigates to shell', (tester) async {
    final storage = newTokenStorage();
    final api = FakeApi(storage: storage);

    await tester.pumpWidget(buildApp(api: api, storage: storage));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.widgetWithText(TextField, 'Email'),
      'cliente@andespadel.com',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Contraseña'),
      'Andes12345!',
    );
    await tester.tap(find.text('Entrar'));
    await tester.pumpAndSettle();

    // Bottom nav is icon-only (labels hidden) — assert via icons. The home
    // tab is selected, so it shows the filled `Icons.home` variant.
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.byIcon(Icons.home), findsOneWidget);
    expect(find.byIcon(Icons.event_note_outlined), findsOneWidget);
    expect(find.byIcon(Icons.person_outline), findsOneWidget);
    // Real success signal: the fake API minted tokens into storage.
    expect(await storage.read(SecureTokenStorage.accessKey), 'fake-access');
    expect(await storage.read(SecureTokenStorage.refreshKey), 'fake-refresh');
  });

  testWidgets('login with bad password stays on login and shows an error',
      (tester) async {
    final storage = newTokenStorage();
    final api = FakeApi(storage: storage);

    await tester.pumpWidget(buildApp(api: api, storage: storage));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.widgetWithText(TextField, 'Email'),
      'cliente@andespadel.com',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Contraseña'),
      'wrong-password',
    );
    await tester.tap(find.text('Entrar'));
    await tester.pumpAndSettle();

    // Real failure signal: still on login, error copy rendered, no tokens.
    expect(find.byType(NavigationBar), findsNothing);
    // The message is rendered by the field decoration, the inline error and
    // a SnackBar — any of them is a real failure signal.
    expect(find.text('Credenciales inválidas'), findsWidgets);
    expect(await storage.read(SecureTokenStorage.accessKey), isNull);
    expect(await storage.read(SecureTokenStorage.refreshKey), isNull);
  });

  testWidgets('restores stored session to shell', (tester) async {
    final storage = newTokenStorage();
    await storage.write(SecureTokenStorage.accessKey, 'fake-access');
    await storage.write(SecureTokenStorage.refreshKey, 'fake-refresh');
    final api = FakeApi(storage: storage);

    await tester.pumpWidget(buildApp(api: api, storage: storage));
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.event_note_outlined), findsOneWidget);
    expect(find.byIcon(Icons.person_outline), findsOneWidget);
  });

  testWidgets('logout returns to login and clears tokens', (tester) async {
    final storage = newTokenStorage();
    await storage.write(SecureTokenStorage.accessKey, 'fake-access');
    await storage.write(SecureTokenStorage.refreshKey, 'fake-refresh');
    final api = FakeApi(storage: storage);

    await tester.pumpWidget(buildApp(api: api, storage: storage));
    await tester.pumpAndSettle();

    await tester.tap(find.byIcon(Icons.person_outline));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cerrar sesión'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Confirmar'));
    await tester.pumpAndSettle();

    expect(find.text('Iniciar sesión'), findsWidgets);
    expect(api.loggedOut, isTrue);
    expect(await storage.read(SecureTokenStorage.accessKey), isNull);
    expect(await storage.read(SecureTokenStorage.refreshKey), isNull);
  });
}
