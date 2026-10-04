import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:padel_app/core/widgets/password_field.dart';
import 'package:padel_app/main.dart' as app;

/// Captures the public (no-login) screens for store listings.
///
///   SCREENSHOT_DIR=/tmp/shots flutter drive \
///     --driver=test_driver/integration_test.dart \
///     --target=integration_test/capture_public_test.dart \
///     --dart-define=API_BASE_URL=http://127.0.0.1:28002/api \
///     --dart-define=SKIP_PUSH_PROMPT=true \
///     -d "iPhone 17 Pro Max"
///
/// Two traps this file exists to avoid:
///   1. SKIP_PUSH_PROMPT is required — the iOS notification sheet is not a
///      Flutter widget, so it swallows every tap and the test times out.
///   2. Never use pumpAndSettle here. Loading indicators are indefinite
///      animations, so pumpAndSettle waits forever and the driver exits
///      without writing a single screenshot. Use timed pump() instead.
void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  Future<void> snap(WidgetTester tester, String name) async {
    // Fixed settle window: enough for the frame to paint, and immune to
    // spinning progress indicators.
    await tester.pump(const Duration(seconds: 2));
    await tester.pump(const Duration(milliseconds: 500));
    await binding.takeScreenshot(name);
    // ignore: avoid_print
    print('SNAPSHOT $name');
  }

  testWidgets('capture login and register', (tester) async {
    app.main();
    await tester.pump(const Duration(seconds: 5));
    await tester.pump(const Duration(seconds: 2));

    await snap(tester, '01-login');

    final registerLink = find.textContaining('Regístrate');
    if (registerLink.evaluate().isNotEmpty) {
      await tester.ensureVisible(registerLink.first);
      await tester.pump(const Duration(seconds: 1));
      await tester.tap(registerLink.first, warnIfMissed: false);
      await tester.pump(const Duration(seconds: 3));
      await tester.pump(const Duration(seconds: 1));

      // Fill the form so the store shot shows a real registration in progress
      // rather than an empty form. Operator-supplied address.
      Future<void> fill(Finder field, String text) async {
        if (field.evaluate().isEmpty) return;
        await tester.ensureVisible(field.first);
        await tester.pump(const Duration(milliseconds: 400));
        await tester.enterText(field.first, text);
        await tester.pump(const Duration(milliseconds: 400));
      }

      await fill(find.widgetWithText(TextField, 'Nombre'), 'Cannachain');
      await fill(find.widgetWithText(TextField, 'Apellido'), 'Costa');
      await fill(find.widgetWithText(TextField, 'Email'), 'cannachaincosta@gmail.com');
      await fill(find.widgetWithText(PasswordField, 'Contraseña'), 'Andes12345!');
      await tester.pump(const Duration(seconds: 1));

      await snap(tester, '02-register');

      final back = find.byType(BackButton);
      if (back.evaluate().isNotEmpty) {
        await tester.tap(back.first, warnIfMissed: false);
        await tester.pump(const Duration(seconds: 2));
        await snap(tester, '03-login-again');
      }
    }

    expect(find.byType(TextField).evaluate().isNotEmpty, isTrue,
        reason: 'no form on screen — capture did not reach login/register');
  });
}
