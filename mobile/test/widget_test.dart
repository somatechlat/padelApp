import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/app.dart';
import 'package:padel_app/core/storage.dart';

import 'helpers/fake_api.dart';

Widget buildApp(FakeApi api) {
  final storage = InMemoryTokenStorage();
  return AndesPadelApp(api: api, storage: storage);
}

void main() {
  testWidgets('shows login screen when no session', (tester) async {
    await tester.pumpWidget(buildApp(FakeApi()));
    await tester.pumpAndSettle();

    expect(find.text('Andes Padel'), findsOneWidget);
    expect(find.text('Iniciar sesión'), findsWidgets);
    expect(find.byType(TextButton), findsWidgets);
  });

  testWidgets('login navigates to app shell', (tester) async {
    await tester.pumpWidget(buildApp(FakeApi()));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.widgetWithText(TextField, 'Email'),
      'cliente@andespadel.com',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Contraseña'),
      'pass12345',
    );
    await tester.tap(find.text('Entrar'));
    await tester.pumpAndSettle();

    expect(find.text('Mis reservas'), findsOneWidget);
    expect(find.text('Perfil'), findsOneWidget);
  });

  testWidgets('register navigates to verify screen', (tester) async {
    await tester.pumpWidget(buildApp(FakeApi()));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Regístrate'));
    await tester.pumpAndSettle();

    expect(find.text('Crear cuenta'), findsWidgets);
    await tester.enterText(
      find.widgetWithText(TextField, 'Nombre completo'),
      'Ana',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Email'),
      'ana@test.com',
    );
    await tester.enterText(
      find.widgetWithText(TextField, 'Contraseña'),
      'pass12345',
    );
    await tester.tap(find.text('Acepto los términos y condiciones'));
    await tester.tap(find.widgetWithText(FilledButton, 'Crear cuenta'));
    await tester.pumpAndSettle();

    expect(find.text('Verificar email'), findsOneWidget);
    expect(find.text('ana@test.com'), findsOneWidget);
  });

  testWidgets('restores session from storage to shell', (tester) async {
    final storage = InMemoryTokenStorage();
    await storage.write(SecureTokenStorage.accessKey, 'fake-access');
    await storage.write(SecureTokenStorage.refreshKey, 'fake-refresh');
    await tester.pumpWidget(AndesPadelApp(api: FakeApi(), storage: storage));
    await tester.pumpAndSettle();

    expect(find.text('Inicio'), findsWidgets);
    expect(find.text('Mis reservas'), findsOneWidget);
  });

  testWidgets('logout returns to login', (tester) async {
    final storage = InMemoryTokenStorage();
    await storage.write(SecureTokenStorage.accessKey, 'fake-access');
    await storage.write(SecureTokenStorage.refreshKey, 'fake-refresh');
    await tester.pumpWidget(AndesPadelApp(api: FakeApi(), storage: storage));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Perfil'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cerrar sesión'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Confirmar'));
    await tester.pumpAndSettle();

    expect(find.text('Iniciar sesión'), findsWidgets);
  });
}
