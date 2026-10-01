import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:padel_app/main.dart' as app;

/// Drives the real app on a device/simulator against a live API.
///
///   flutter drive \
///     --driver=test_driver/integration_test.dart \
///     --target=integration_test/app_journeys_test.dart \
///     --dart-define=API_BASE_URL=https://app.andespadelclub.com/api
///
/// The driver writes screenshots on the host (SCREENSHOT_DIR) — the app
/// sandbox is read-only and host env vars never reach it.
void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  final email = Platform.environment['E2E_EMAIL'] ?? 'cliente@andespadel.com';
  final password = Platform.environment['E2E_PASSWORD'] ?? 'Andes12345!';

  Future<void> snap(WidgetTester tester, String name) async {
    await tester.pumpAndSettle(const Duration(seconds: 2));
    await binding.takeScreenshot(name);
    // ignore: avoid_print
    print('SNAPSHOT $name');
  }

  testWidgets('login, browse every tab', (tester) async {
    // Surface the URL the app is compiled against — a dart-define that fails
    // to propagate silently sends the app to the dev default
    // (127.0.0.1:28002) and every call dies with a connection error.
    const apiUrl = String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://127.0.0.1:28002/api',
    );
    // ignore: avoid_print
    print('E2E_API_BASE_URL=$apiUrl');

    // Probe the API from this isolate with a plain HttpClient. This separates
    // "the app is broken" from "this simulator has no network at all".
    try {
      final client = HttpClient()
        ..connectionTimeout = const Duration(seconds: 15);
      final req = await client
          .getUrl(Uri.parse('https://app.andespadelclub.com/api/courts/'));
      final resp = await req.close();
      // ignore: avoid_print
      print('PROBE_HTTP_STATUS=${resp.statusCode}');
      await resp.drain<void>();
      client.close(force: true);
    } catch (e) {
      // ignore: avoid_print
      print('PROBE_ERROR=${e.runtimeType}: $e');
    }

    app.main();
    await tester.pump(const Duration(seconds: 4));
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // A previous run may have left a session in secure storage, in which case
    // we land straight on the shell and there is no login form to fill. Only
    // drive the form when it is actually on screen.
    final hasForm = find.byType(TextField).evaluate().isNotEmpty;
    final onShellAlready = find.byType(NavigationBar).evaluate().isNotEmpty;
    // ignore: avoid_print
    print('STATE hasForm=$hasForm onShell=$onShellAlready');

    if (hasForm && !onShellAlready) {
      await snap(tester, '01-login');
      await tester.enterText(find.byType(TextField).at(0), email);
      await tester.enterText(find.byType(TextField).at(1), password);
      await snap(tester, '02-login-filled');

      final filled = find.widgetWithText(FilledButton, 'Entrar');
      final elevated = find.widgetWithText(ElevatedButton, 'Entrar');
      final target = filled.evaluate().isNotEmpty ? filled : elevated;
      await tester.ensureVisible(target);
      await tester.pumpAndSettle(const Duration(seconds: 1));
      await tester.tap(target, warnIfMissed: false);
      await tester.pump(const Duration(seconds: 12));
      await tester.pumpAndSettle(const Duration(seconds: 4));
      await snap(tester, '03-after-login');
    }

    final texts = find.byType(Text).evaluate().map((e) {
      final w = e.widget as Text;
      return w.data ?? w.textSpan?.toPlainText() ?? '<span>';
    }).toList();
    // ignore: avoid_print
    print('SCREEN_TEXTS(${texts.length}): ${texts.take(30).join(' | ')}');

    expect(find.byType(NavigationBar).evaluate().isNotEmpty, isTrue,
        reason: 'app shell not reached — still on auth (see screenshots)');
    await snap(tester, '03-home');

    const tabs = [
      (1, '04-bookings'),
      (2, '05-events'),
      (3, '06-notifications'),
      (4, '07-profile'),
      (0, '08-home-again'),
    ];
    for (final (index, name) in tabs) {
      final destinations = find.descendant(
        of: find.byType(NavigationBar),
        matching: find.byType(NavigationDestination),
      );
      await tester.tap(destinations.at(index));
      await tester.pumpAndSettle(const Duration(seconds: 3));
      await snap(tester, name);
    }

    final destinations = find.descendant(
      of: find.byType(NavigationBar),
      matching: find.byType(NavigationDestination),
    );
    await tester.tap(destinations.at(4));
    await tester.pumpAndSettle(const Duration(seconds: 2));
    await snap(tester, '09-profile');
  });
}
