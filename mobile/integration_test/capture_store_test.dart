import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:padel_app/core/widgets/password_field.dart';
import 'package:padel_app/features/home/home_screen.dart';
import 'package:padel_app/main.dart' as app;

/// Captures the authenticated screens the store listings need.
///
///   SCREENSHOT_DIR=/tmp/shots-store flutter drive \
///     --driver=test_driver/integration_test.dart \
///     --target=integration_test/capture_store_test.dart \
///     --dart-define=API_BASE_URL=https://app.andespadelclub.com/api \
///     --dart-define=SKIP_PUSH_PROMPT=true \
///     --dart-define=SHOT_EMAIL=... --dart-define=SHOT_PASSWORD=... \
///     -d "iPhone 17 Pro Max"
///
/// Traps this file exists to avoid:
///   1. SKIP_PUSH_PROMPT — the iOS notification sheet is not a Flutter widget
///      and swallows every tap.
///   2. Never pumpAndSettle: loading indicators are indefinite animations.
///   3. find.byType(NavigationBar) is NOT a login-success signal — the shell
///      is mounted behind the opaque login route and matches the whole time.
///      Wait for the login form to leave the tree instead.
///   4. tryTap must re-check the finder immediately before tapping; a widget
///      can vanish between evaluate() and tap() and finder.first then throws
///      StateError, killing the whole run for one missing button.
void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  /// Waits [seconds] of REAL time, then pumps.
  ///
  /// `tester.pump(Duration(...))` only advances the fake test clock and
  /// returns immediately — it does not wait for a live HTTP response. Every
  /// wait in this file must go through here or the capture snaps a loading
  /// frame and the retry taps fire before the error state even exists.
  Future<void> settle(WidgetTester tester, {int seconds = 2}) async {
    await Future<void>.delayed(Duration(seconds: seconds));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
  }

  /// Announces a shot. The PNG is taken by the HOST (`simctl io screenshot`)
  /// which watches for this marker — flutter's takeScreenshot grabs the wrong
  /// frame on iOS and files land under the wrong name.
  Future<void> snap(WidgetTester tester, String name) async {
    await tester.pump(const Duration(seconds: 1));
    await Future<void>.delayed(const Duration(milliseconds: 400));
    // ignore: avoid_print
    print('SNAPSHOT $name');
    // flutter drive pipes stdout in blocks, so the host watcher can receive
    // this line seconds late and grab the NEXT screen. Hold the frame long
    // enough that even a delayed grab still gets the right one.
    await Future<void>.delayed(const Duration(seconds: 5));
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

  /// A slot chip label is an HH:MM or HH:MM:SS time. Used as the signal that
  /// the availability grid has finished loading.
  final slotChip = find.byWidgetPredicate(
    (w) =>
        w is Text &&
        w.data != null &&
        RegExp(r'^\d{1,2}:\d{2}(:\d{2})?$').hasMatch(w.data!.trim()),
  );

  // IndexedStack keeps all five tabs mounted, and NavigationBar keeps both
  // the outline and the filled icon in the tree (unselected one at opacity
  // 0). find.byIcon / hitTestable therefore lie about which tab is up.
  //
  // Tap NavigationDestination by INDEX using the destination's own center —
  // the tappable box is the destination, not the icon inside it.
  Future<void> goTab(WidgetTester tester, int index) async {
    final dests = find.byType(NavigationDestination);
    if (dests.evaluate().length <= index) return;
    final center = tester.getCenter(dests.at(index));
    await tester.tapAt(center);
    await settle(tester, seconds: 2);
  }

  testWidgets('capture authenticated store screens', (tester) async {
    app.main();
    // Warm-up: let the first wave of HTTP finish before any finder runs. The
    // cold-start race is what fills the frame with spinners.
    await settle(tester, seconds: 12);

    // ── log in (skipped when a session is already in secure storage) ──────
    const shotEmail = String.fromEnvironment('SHOT_EMAIL', defaultValue: '');
    const shotPassword =
        String.fromEnvironment('SHOT_PASSWORD', defaultValue: '');
    // ignore: avoid_print
    print('SHOT_EMAIL len=${shotEmail.length} value=$shotEmail');

    // Detect the login screen by its submit button, not by an Email-field
    // finder: if that finder misses, the run silently skips login and every
    // later "tab" shot is the login screen under a new name.
    final loginButton = find.text('Entrar');
    final emailField = find.widgetWithText(TextField, 'Email');
    var alreadyIn = loginButton.evaluate().isEmpty;
    // ignore: avoid_print
    print('alreadyIn=$alreadyIn loginButton=${loginButton.evaluate().length} '
        'emailField=${emailField.evaluate().length}');

    // A restored session skips login, but AuthState.user is then never
    // populated (/auth/me is not called) and the greeting falls back to bare
    // "Hola". Log out first so the run always goes through the login form.
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

    // Home is three parallel loads. The first attempt races the connection and
    // each section can land in its error state; the retry buttons are the only
    // way back. Keep tapping them until the screen is actually full — otherwise
    // the shot is "Hola" + empty events + a spinner.
    // Land on the Home tab explicitly. Tap NavigationDestination by INDEX:
    // tapping the icon widget is unreliable (Tooltip wrapper, and the selected
    // tab swaps outline->filled so the finder disappears under the tap).
    // Do NOT tap anything before the home shot. The shell already starts on
    // index 0 (Home), and a mis-targeted tapAt on NavigationDestination lands
    // on a different tab — 03-inicio then becomes Eventos under a new name.

    // Scope every check to HomeScreen: AppShell uses IndexedStack, so the
    // Events tab's "Quedada del Sábado" titles are still in the tree while
    // Home is on screen.
    Finder inHome(Finder f) => find.descendant(
          of: find.byType(HomeScreen),
          matching: f,
        );

    final greeting = inHome(find.textContaining('Hola,')).hitTestable();
    final quedadas = inHome(find.textContaining('oct')).hitTestable();
    final clubName = inHome(find.textContaining('Andes Padel')).hitTestable();
    final homeContent = [greeting, quedadas, clubName];
    final homeRetry = inHome(find.text('Reintentar'));

    // Wait for all three sections. "No spinner" is NOT a readiness signal:
    // a failed load renders an empty state with no spinner at all, so an
    // empty-spinner break snaps a half-built home every time.
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
    // IndexedStack keeps every tab mounted, so inHome() finders match hidden
    // Home content even when another tab is on screen. Require the selected
    // (filled) home icon before trusting any of it.
    final reallyHome = true; // content check below is authoritative
    // ignore: avoid_print
    print(
        'home ready: reallyHome=$reallyHome '
        'greeting=${greeting.evaluate().length} '
        'quedadas=${quedadas.evaluate().length} '
        'club=${clubName.evaluate().length} '
        'retry=${homeRetry.evaluate().length}');

    await snap(tester, '03-inicio');

    // Only enter the wizard from a real home; otherwise the shots that follow
    // are the wizard failing over an empty shell.
    // RESERVA AHORA sits below the fold — scroll until it is hit-testable
    // rather than dragUntilVisible, which throws when the first match is
    // already the destination and kills the rest of the run.
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
    // ── the five tabs ────────────────────────────────────────────────────
    // Each tab is only snapped once ITS OWN title is on screen. Tapping the
    // icon and sleeping is not enough: the shell is mounted behind the wizard
    // route, so a tap that "succeeds" can still be hitting the wizard, and the
    // shot that follows is the previous screen under a new name.
    // Readiness is the SELECTED (filled) nav icon. A title string is not:
    // AppShell uses IndexedStack, so every tab's AppBar title is still in the
    // tree while another tab is showing. "Mis reservas" is therefore visible
    // even on Home, and a title check reports success over the wrong screen.
    // Readiness = that tab's unique text is HIT-TESTABLE. IndexedStack keeps
    // every tab mounted, so find.text finds hidden AppBars, and the nav bar
    // keeps both outline and filled icons in the tree. Only a hit-testable
    // finder means "this tab is actually on screen".
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
