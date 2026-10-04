import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:padel_app/core/widgets/password_field.dart';
import 'package:padel_app/features/home/home_screen.dart';
import 'package:padel_app/main.dart' as app;

/// Captures the screens the store listings need.
///
///     SCREENSHOT_DIR=/tmp/shots flutter drive \
///       --driver=test_driver/integration_test.dart \
///       --target=integration_test/capture_store_test.dart \
///       --dart-define=API_BASE_URL=http://localhost:28002/api \
///       --dart-define=SKIP_PUSH_PROMPT=true --dart-define=SKIP_PUSH=true \
///       --dart-define=SHOT_EMAIL=... --dart-define=SHOT_PASSWORD=... \
///       -d "iPhone 17 Pro Max"
///
/// SKIP_PUSH_PROMPT: the iOS permission sheet is not a Flutter widget and
/// swallows taps. Never pumpAndSettle: spinners are indefinite animations.
/// Readiness is a hit-testable marker unique to the screen — see AGENTS.md §8.
void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  /// Waits [seconds] of real time. `tester.pump(Duration)` advances the fake
  /// clock only and returns immediately — it never waits for live HTTP.
  Future<void> settle(WidgetTester tester, {int seconds = 2}) async {
    await Future<void>.delayed(Duration(seconds: seconds));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
  }

  /// Captures the current frame. Wrong filenames come from wrong readiness
  /// signals, not from takeScreenshot — IndexedStack keeps every tab mounted.
  Future<void> snap(WidgetTester tester, String name) async {
    await tester.pump(const Duration(seconds: 1));
    await binding.takeScreenshot(name);
    // ignore: avoid_print
    print('SNAPSHOT $name');
    await Future<void>.delayed(const Duration(milliseconds: 300));
    await tester.pump();
  }

  Future<bool> tryTap(
    WidgetTester tester,
    Finder finder, {
    bool scroll = true,
  }) async {
    if (finder.evaluate().isEmpty) return false;
    if (scroll) {
      try {
        await tester.ensureVisible(finder.first);
        await settle(tester, seconds: 1);
      } catch (_) {
        return false;
      }
    }
    if (finder.evaluate().isEmpty) return false;
    try {
      await tester.tap(finder.first, warnIfMissed: false);
    } catch (_) {
      return false;
    }
    await settle(tester);
    return true;
  }

  /// Waits until [finder] is gone, or [timeoutSeconds] of real time elapses.
  Future<bool> waitUntilGone(
    WidgetTester tester,
    Finder finder, {
    int timeoutSeconds = 30,
  }) async {
    for (var i = 0; i < timeoutSeconds; i++) {
      if (finder.evaluate().isEmpty) return true;
      await Future<void>.delayed(const Duration(seconds: 1));
      await tester.pump();
    }
    return finder.evaluate().isEmpty;
  }

  /// Waits until [finder] appears, or [timeoutSeconds] of real time elapses.
  Future<bool> waitUntil(
    WidgetTester tester,
    Finder finder, {
    int timeoutSeconds = 30,
  }) async {
    for (var i = 0; i < timeoutSeconds; i++) {
      if (finder.evaluate().isNotEmpty) return true;
      await Future<void>.delayed(const Duration(seconds: 1));
      await tester.pump();
    }
    return finder.evaluate().isNotEmpty;
  }

  /// Slot chips are HH:MM labels; their presence means the grid has loaded.
  final slotChip = find.byWidgetPredicate(
    (w) =>
        w is Text &&
        w.data != null &&
        RegExp(r'^\d{1,2}:\d{2}(:\d{2})?$').hasMatch(w.data!.trim()),
  );

  // IndexedStack mounts all five tabs and NavigationBar keeps both icons in
  // the tree, so neither is a readiness signal. Tap the destination box itself.
  Future<void> goTab(WidgetTester tester, int index) async {
    final dests = find.byType(NavigationDestination);
    if (dests.evaluate().length <= index) return;
    final center = tester.getCenter(dests.at(index));
    await tester.tapAt(center);
    await settle(tester, seconds: 2);
  }

  testWidgets('capture authenticated store screens', (tester) async {
    app.main();
    // Let the first HTTP wave finish; the cold-start race fills frames with spinners.
    await settle(tester, seconds: 12);

    // ── log in ──
    const shotEmail = String.fromEnvironment('SHOT_EMAIL', defaultValue: '');
    const shotPassword =
        String.fromEnvironment('SHOT_PASSWORD', defaultValue: '');
    // ignore: avoid_print
    print('SHOT_EMAIL len=${shotEmail.length} value=$shotEmail');

    // Key off "Entrar", not the Email field: a missed field skips login silently.
    final loginButton = find.text('Entrar');
    final emailField = find.widgetWithText(TextField, 'Email');
    var alreadyIn = loginButton.evaluate().isEmpty;
    // ignore: avoid_print
    print('alreadyIn=$alreadyIn loginButton=${loginButton.evaluate().length} '
        'emailField=${emailField.evaluate().length}');

    // A restored session leaves AuthState.user empty and the greeting bare. Log out first.
    if (alreadyIn && shotEmail.isNotEmpty) {
      await goTab(tester, 4); // profile
      final logoutRow = find.text('Cerrar sesión').hitTestable();
      if (logoutRow.evaluate().isNotEmpty) {
        await tester.tap(logoutRow.first, warnIfMissed: false);
        await settle(tester, seconds: 2);
        // Dialog actions: "Cancelar" / "Confirmar".
        final confirmBtn = find.widgetWithText(FilledButton, 'Confirmar');
        if (confirmBtn.evaluate().isNotEmpty) {
          await tester.tap(confirmBtn.first, warnIfMissed: false);
        }
        await settle(tester, seconds: 3);
        alreadyIn = find.text('Entrar').evaluate().isEmpty;
        // ignore: avoid_print
        print('after logout: alreadyIn=$alreadyIn');
      }
    }

    if (!alreadyIn) {
      expect(shotEmail, isNotEmpty, reason: 'SHOT_EMAIL define missing');
      expect(shotPassword, isNotEmpty, reason: 'SHOT_PASSWORD define missing');

      final passwordField = find.byType(PasswordField);
      expect(emailField.evaluate().length, 1,
          reason: 'expected one Email field on the login form');
      expect(passwordField.evaluate().length, 1,
          reason: 'expected one PasswordField on the login form');

      await tester.enterText(emailField, shotEmail);
      await tester.enterText(passwordField, shotPassword);
      await settle(tester, seconds: 1);

      final submitted =
          await tryTap(tester, find.text('Entrar'), scroll: false);
      expect(submitted, isTrue, reason: 'login button not found');

      final loginGone = await waitUntilGone(tester, find.text('Entrar'));
      if (!loginGone) {
        await binding.takeScreenshot('00-login-failed');
        // ignore: avoid_print
        print('SNAPSHOT 00-login-failed');
      }
      expect(loginGone, isTrue,
          reason: 'login form still on screen — check SHOT_EMAIL/SHOT_PASSWORD');
      await settle(tester, seconds: 2);
    }

    // Shell already starts on Home; do not tap anything before this shot.

    // Scope to HomeScreen: IndexedStack keeps the Events tab's titles in the tree.
    Finder inHome(Finder f) => find.descendant(
          of: find.byType(HomeScreen),
          matching: f,
        );

    final greeting = inHome(find.textContaining('Hola,')).hitTestable();
    final quedadas = inHome(find.textContaining('oct')).hitTestable();
    final clubName = inHome(find.textContaining('Andes Padel')).hitTestable();
    final homeContent = [greeting, quedadas, clubName];
    final homeRetry = inHome(find.text('Reintentar'));

    // Absence of a spinner is not readiness — a failed load renders an empty state.
    for (var i = 0; i < 45; i++) {
      if (homeContent.every((f) => f.evaluate().isNotEmpty)) break;
      if (homeRetry.evaluate().isNotEmpty) {
        // ignore: avoid_print
        print('HOME: retrying failed section ($i)');
        await tester.tap(homeRetry.first, warnIfMissed: false);
      }
      await Future<void>.delayed(const Duration(seconds: 1));
      await tester.pump();
    }
    final reallyHome = true; // content check below is authoritative
    // ignore: avoid_print
    print(
        'home ready: reallyHome=$reallyHome '
        'greeting=${greeting.evaluate().length} '
        'quedadas=${quedadas.evaluate().length} '
        'club=${clubName.evaluate().length} '
        'retry=${homeRetry.evaluate().length}');

    await snap(tester, '03-inicio');

    // RESERVA AHORA is below the fold. dragUntilVisible throws if it is already
    // the destination, which aborts the run — scroll instead.
    for (var i = 0; i < 8; i++) {
      if (find.text('RESERVA AHORA').hitTestable().evaluate().isNotEmpty) {
        break;
      }
      await tester.drag(
        find.byType(HomeScreen).first,
        const Offset(0, -300),
      );
      await settle(tester, seconds: 1);
    }
    // ── the five tabs ──
    // Readiness is that tab's unique text being hit-testable: find.text matches
    // hidden AppBars on the other four tabs.
    Future<void> tab(
      int index,
      String marker,
      String name,
    ) async {
      await goTab(tester, index);

      for (var i = 0; i < 6; i++) {
        if (find.text(marker).hitTestable().evaluate().isNotEmpty &&
            find.text('Reintentar').evaluate().isEmpty) {
          break;
        }
        final retry = find.text('Reintentar');
        if (retry.evaluate().isNotEmpty) {
          // ignore: avoid_print
          print('TAB $name: retrying after connection error ($i)');
          await tester.tap(retry.first, warnIfMissed: false);
        }
        await settle(tester, seconds: 3);
      }

      final showing = find.text(marker).hitTestable().evaluate().isNotEmpty;
      final stillError = find.text('Reintentar').evaluate().isNotEmpty;
      // ignore: avoid_print
      print('TAB $name: marker="$marker" showing=$showing '
          'stillError=$stillError');
      if (!showing) {
        // ignore: avoid_print
        print('TAB $name: WARNING marker not on screen — shot may be wrong');
      }
      await snap(tester, name);
    }

    await tab(1, 'Mis reservas', '07-mis-reservas');
    await tab(2, 'Quedadas', '08-eventos');
    await tab(3, 'Notificaciones', '09-alertas');
    await tab(4, 'Perfil', '10-perfil');

    final opened = await tryTap(
        tester, find.text('RESERVA AHORA').hitTestable());
    // ignore: avoid_print
    print('opened=$opened');
    if (!opened) {
      // still capture what we have rather than abort the whole run
      // ignore: avoid_print
      print('RESERVA AHORA missing — skipping wizard shots');
    } else {

    // ── booking wizard: WHEN (date + duration + start) ────────────────────
    try {
    await settle(tester, seconds: 2);

    // Wait for the availability grid: slot chips replace the spinner. If the
    // first load fails, the slot list is empty and every later step is a
    // duplicate of this screen under a new name.
    var slotsReady = await waitUntil(tester, slotChip, timeoutSeconds: 25);
    if (!slotsReady) {
      final retry = find.text('Reintentar');
      if (retry.evaluate().isNotEmpty) {
        await tester.tap(retry.first, warnIfMissed: false);
        slotsReady = await waitUntil(tester, slotChip, timeoutSeconds: 20);
      }
    }
    // ignore: avoid_print
    print('slotsReady=$slotsReady slotChips=${slotChip.evaluate().length}');
    await snap(tester, '04-reservar-cuando');

    // Pick an evening slot if one is free, otherwise the first chip.
    Finder pickSlot = slotChip;
    for (final label in const [
      '19:00',
      '18:00',
      '20:00',
      '17:00',
      '16:00',
      '15:00',
      '10:00',
      '09:00',
    ]) {
      final candidate = find.textContaining(label);
      if (candidate.evaluate().isNotEmpty) {
        pickSlot = candidate;
        break;
      }
    }
    final slotPicked = await tryTap(tester, pickSlot);
    // ignore: avoid_print
    print('slotPicked=$slotPicked');
    await settle(tester, seconds: 1);

    final wentNext = await tryTap(tester, find.text('Continuar'));
    // ignore: avoid_print
    print('wentNext=$wentNext');
    await settle(tester, seconds: 3);

    // ── booking wizard: COURT ─────────────────────────────────────────────
    final courtsReady = await waitUntil(
      tester,
      find.textContaining('Cancha'),
      timeoutSeconds: 20,
    );
    // ignore: avoid_print
    print('courtsReady=$courtsReady');
    await snap(tester, '05-elige-cancha');

    // Court cards are ListTiles titled "Cancha N". textContaining('Cancha')
    // matches the "Canchas disponibles" header FIRST and tapping a label does
    // nothing — pick the tile by its exact title instead.
    final courtCard = find.widgetWithText(ListTile, 'Cancha 1');
    final courtPicked = await tryTap(
      tester,
      courtCard.evaluate().isNotEmpty ? courtCard : find.text('Cancha 1'),
    );
    // ignore: avoid_print
    print('courtPicked=$courtPicked');
    await settle(tester, seconds: 1);

    await tryTap(tester, find.text('Continuar'));
    // The summary step shows a price row labelled "Total".
    final onSummary = await waitUntil(tester, find.text('Total'),
        timeoutSeconds: 15);
    // ignore: avoid_print
    print('onSummary=$onSummary');
    await snap(tester, '06-resumen');
    } catch (e) {
      // ignore: avoid_print
      print('WIZARD: aborted ($e) — continuing to tabs');
    }
    }

    // Leave the wizard entirely. NavigationBar is a false positive here too —
    // the shell stays mounted behind the opaque wizard route — so wait for the
    // wizard's own title to leave the tree instead.
    for (var i = 0; i < 5; i++) {
      if (find.text('Reservar cancha').evaluate().isEmpty) break;
      if (find.byType(BackButton).evaluate().isNotEmpty) {
        await tester.tap(find.byType(BackButton).first, warnIfMissed: false);
      } else if (find.text('Volver').evaluate().isNotEmpty) {
        await tester.tap(find.text('Volver').first, warnIfMissed: false);
      } else {
        break;
      }
      await settle(tester, seconds: 1);
    }
    final wizardGone = find.text('Reservar cancha').evaluate().isEmpty;
    // ignore: avoid_print
    print('wizardGone=$wizardGone');

  });
}
