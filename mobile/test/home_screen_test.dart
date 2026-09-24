import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:padel_app/core/api_client.dart';
import 'package:padel_app/core/locale_controller.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:padel_app/core/storage.dart';
import 'package:padel_app/features/auth/auth_state.dart';
import 'package:padel_app/features/home/home_screen.dart';

import 'helpers/fake_api.dart';

Widget buildHome(FakeApi api) {
  final storage = InMemoryTokenStorage();
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
  testWidgets('home renders with empty banners and no club contact',
      (tester) async {
    final api = FakeApi()
      ..bannersResponse = []
      ..clubResponse = {
        'name': '',
        'address': '',
        'phone': '',
        'email': '',
        'whatsapp_number': '',
        'instagram_url': '',
        'home_section_title': '',
      }
      ..courtsResponse = [];

    await tester.pumpWidget(buildHome(api));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    // Section title falls back to i18n when club.home_section_title is empty.
    expect(find.text('Reserva tu cancha'), findsOneWidget);
    // Empty banners → carousel hidden (no PageView).
    expect(find.byType(PageView), findsNothing);
    // No contact → contact card hidden.
    expect(find.text('Contacto del club'), findsNothing);
    // Empty courts → empty state.
    expect(find.text('No hay canchas disponibles en este momento'), findsOneWidget);
  });

  testWidgets('home shows section title from club API and banners',
      (tester) async {
    final api = FakeApi()
      ..bannersResponse = [
        {
          'id': 1,
          'title': 'Torneo de Verano',
          'subtitle': '',
          'image': 'https://example.com/banner.jpg',
          'link_url': '',
          'link_type': '',
          'sort_order': 0,
        },
      ]
      ..clubResponse = {
        'name': 'Andes Padel',
        'address': 'Rodriguez Labandera y Ernesto Alban, Quito',
        'phone': '0992676842',
        'email': 'andespadelclub@gmail.com',
        'whatsapp_number': '593992676842',
        'instagram_url': 'https://instagram.com/andespadelec',
        'home_section_title': 'Reserva tu cancha',
        'bank_name': 'Banco Test',
        'bank_account_number': '123',
        'bank_account_holder': 'Titular',
        'bank_account_code': 'CODE',
      }
      ..courtsResponse = [
        {
          'name': 'Cancha 1',
          'description': 'Principal',
          'court_type': 'techada',
          'has_lighting': true,
          'price_base': '25.00',
          'image': null,
        },
      ];

    await tester.pumpWidget(buildHome(api));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('Reserva tu cancha'), findsOneWidget);
    expect(find.byType(PageView), findsOneWidget);
    expect(find.text('Torneo de Verano'), findsOneWidget);
    expect(find.text('Cancha 1'), findsOneWidget);

    // Contact card sits below courts — scroll slivers into view.
    await tester.scrollUntilVisible(
      find.text('Contacto del club'),
      240,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    expect(find.text('Contacto del club'), findsOneWidget);
    expect(find.text('WhatsApp'), findsOneWidget);
  });

  testWidgets('home hides contact rows when fields are empty', (tester) async {
    final api = FakeApi()
      ..clubResponse = {
        'name': 'Andes Padel',
        'address': '',
        'phone': '',
        'email': 'club@test.com',
        'whatsapp_number': '',
        'instagram_url': '',
        'home_section_title': '',
      };

    await tester.pumpWidget(buildHome(api));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    await tester.scrollUntilVisible(
      find.text('Contacto del club'),
      240,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    expect(find.text('Contacto del club'), findsOneWidget);
    expect(find.text('club@test.com'), findsOneWidget);
    expect(find.text('WhatsApp'), findsNothing);
  });
}
