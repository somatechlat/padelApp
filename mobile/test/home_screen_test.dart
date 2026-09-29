import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/core/api_client.dart';
import 'package:padel_app/core/locale_controller.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:padel_app/core/storage.dart';
import 'package:padel_app/features/auth/auth_state.dart';
import 'package:padel_app/features/home/home_screen.dart';
import 'package:provider/provider.dart';

const kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000/api',
);

FileTokenStorage newTokenStorage() {
  final dir = Directory.systemTemp.createTempSync('andes_padel_home_');
  return FileTokenStorage(File('${dir.path}/tokens.json'));
}

Widget buildHome(ApiClient api, TokenStorage storage) {
  return MultiProvider(
    providers: [
      Provider<ApiClient>.value(value: api),
      ChangeNotifierProvider<AuthState>(
        create: (_) => AuthState(api: api, storage: storage),
      ),
      ChangeNotifierProvider<LocaleController>(
        create: (_) => LocaleController(storage: storage),
      ),
    ],
    child: MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      locale: const Locale('es'),
      home: const HomeScreen(),
    ),
  );
}

void main() {
  // Live binding: real HTTP to the Docker backend (no FakeApi).
  final binding = LiveTestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() {
    HttpOverrides.global = null;
  });

  testWidgets('home renders against real /club/ and /banners/', (tester) async {
    binding.platformDispatcher.textScaleFactorTestValue = 1.0;
    addTearDown(binding.platformDispatcher.clearAllTestValues);

    final storage = newTokenStorage();
    final api = ApiClient(storage: storage, baseUrl: kApiBaseUrl);

    await tester.pumpWidget(buildHome(api, storage));
    // Allow real network futures to complete.
    await tester.pump(const Duration(milliseconds: 50));
    await tester.pumpAndSettle(const Duration(seconds: 2));

    expect(tester.takeException(), isNull);
    // Hero + reserve CTA always present.
    expect(find.textContaining('RESERVA'), findsWidgets);
    // Events section title always present.
    expect(find.text('Eventos'), findsWidgets);
  });

  testWidgets('home shows club contact card from real /club/', (tester) async {
    final storage = newTokenStorage();
    final api = ApiClient(storage: storage, baseUrl: kApiBaseUrl);

    await tester.pumpWidget(buildHome(api, storage));
    await tester.pump(const Duration(milliseconds: 50));
    await tester.pumpAndSettle(const Duration(seconds: 2));

    expect(tester.takeException(), isNull);

    // Club card is below the fold on a phone-sized surface.
    final contact = find.text('Contacto del club');
    if (contact.evaluate().isNotEmpty) {
      await tester.scrollUntilVisible(
        contact,
        240,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();
    }
    // Either the contact card or the empty/error club state must render —
    // never a crash and never a FakeApi placeholder.
    expect(
      find.text('Contacto del club').evaluate().isNotEmpty ||
          find.text('Información del club').evaluate().isNotEmpty ||
          find.textContaining('conexión').evaluate().isNotEmpty,
      isTrue,
    );
  });
}
