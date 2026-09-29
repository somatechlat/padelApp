import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/app.dart';
import 'package:padel_app/core/api_client.dart';
import 'package:padel_app/core/locale_controller.dart';
import 'package:padel_app/core/push_notification_service.dart';
import 'package:padel_app/core/storage.dart';

const kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000/api',
);

FileTokenStorage newTokenStorage() {
  final dir = Directory.systemTemp.createTempSync('andes_padel_app_');
  return FileTokenStorage(File('${dir.path}/tokens.json'));
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
    pushService: pushService ?? PushNotificationService(api: api),
  );
}

void main() {
  final binding = LiveTestWidgetsFlutterBinding.ensureInitialized();
  // Flutter test binding replaces HttpClient with a stub that returns 400.
  // Real API calls need the real HttpClient — remove that override.
  setUpAll(() {
    HttpOverrides.global = null;
  });

  testWidgets('shows login screen when no session', (tester) async {
    final storage = newTokenStorage();
    final api = ApiClient(storage: storage, baseUrl: kApiBaseUrl);

    await tester.pumpWidget(buildApp(api: api, storage: storage));
    await tester.pump(const Duration(milliseconds: 50));
    await tester.pumpAndSettle(const Duration(seconds: 2));

    expect(find.byType(Image), findsOneWidget);
    expect(find.text('Iniciar sesión'), findsWidgets);
    expect(find.text('Accede para reservar tu cancha'), findsOneWidget);
  });

  testWidgets('login with real credentials navigates to shell', (tester) async {
    binding.platformDispatcher.textScaleFactorTestValue = 1.0;
    addTearDown(binding.platformDispatcher.clearAllTestValues);

    final storage = newTokenStorage();
    final api = ApiClient(storage: storage, baseUrl: kApiBaseUrl);

    await tester.pumpWidget(buildApp(api: api, storage: storage));
    await tester.pump(const Duration(milliseconds: 50));
    await tester.pumpAndSettle(const Duration(seconds: 2));

    await tester.enterText(
      find.widgetWithText(TextField, 'Email'),
      'cliente@andespadel.com',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Contraseña'),
      'Andes12345!',
    );
    await tester.tap(find.text('Entrar'));
    await tester.pump(const Duration(milliseconds: 50));
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Bottom nav is icon-only (labels hidden) — assert via icons.
    expect(find.byIcon(Icons.event_note_outlined), findsOneWidget);
    expect(find.byIcon(Icons.home_outlined), findsOneWidget);
    expect(find.byIcon(Icons.person_outline), findsOneWidget);
  });

  testWidgets('restores real session from file storage to shell',
      (tester) async {
    final storage = newTokenStorage();
    final api = ApiClient(storage: storage, baseUrl: kApiBaseUrl);

    // Obtain a real JWT from the Docker API, then restore it cold.
    final authProbe = ApiClient(storage: storage, baseUrl: kApiBaseUrl);
    final login = await authProbe.post('/auth/login/', data: {
      'email': 'cliente@andespadel.com',
      'password': 'Andes12345!',
    });
    await storage.write(
        SecureTokenStorage.accessKey, login['access'] as String);
    await storage.write(
        SecureTokenStorage.refreshKey, login['refresh'] as String? ?? '');

    await tester.pumpWidget(buildApp(api: api, storage: storage));
    await tester.pump(const Duration(milliseconds: 50));
    await tester.pumpAndSettle(const Duration(seconds: 3));

    expect(find.byIcon(Icons.event_note_outlined), findsOneWidget);
    expect(find.byIcon(Icons.person_outline), findsOneWidget);
  });

  testWidgets('logout with real session returns to login', (tester) async {
    final storage = newTokenStorage();
    final api = ApiClient(storage: storage, baseUrl: kApiBaseUrl);
    final login = await api.post('/auth/login/', data: {
      'email': 'cliente@andespadel.com',
      'password': 'Andes12345!',
    });
    await storage.write(
        SecureTokenStorage.accessKey, login['access'] as String);
    await storage.write(
        SecureTokenStorage.refreshKey, login['refresh'] as String? ?? '');

    await tester.pumpWidget(buildApp(api: api, storage: storage));
    await tester.pump(const Duration(milliseconds: 50));
    await tester.pumpAndSettle(const Duration(seconds: 3));

    await tester.tap(find.byIcon(Icons.person_outline));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cerrar sesión'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Confirmar'));
    await tester.pump(const Duration(milliseconds: 50));
    await tester.pumpAndSettle(const Duration(seconds: 2));

    expect(find.text('Iniciar sesión'), findsWidgets);
  });
}
