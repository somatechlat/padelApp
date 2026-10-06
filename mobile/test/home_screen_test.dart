import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/core/api_client.dart';
import 'package:padel_app/core/locale_controller.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:padel_app/features/auth/auth_state.dart';
import 'package:padel_app/features/home/home_screen.dart';
import 'package:provider/provider.dart';

import 'helpers/fake_api.dart';
import 'helpers/test_storage.dart';

Widget buildHome(FakeApi api) {
  final storage = newTokenStorage();
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
    child: const MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      locale: Locale('es'),
      home: HomeScreen(),
    ),
  );
}

void main() {
  testWidgets('home renders hero, events section and reserve CTA',
      (tester) async {
    final api = FakeApi()
      ..club = const FakeClub.empty()
      ..banners = const <FakeBanner>[]
      ..events = const <FakeEvent>[];

    await tester.pumpWidget(buildHome(api));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    // Hero + reserve CTA always present.
    expect(find.textContaining('RESERVA'), findsWidgets);
    // Events section title always present, with the empty-state copy.
    expect(find.text('Eventos'), findsWidgets);
    expect(
      find.text('Próximamente nuevas quedadas y eventos.'),
      findsOneWidget,
    );
    // Empty banners → carousel hidden (no PageView).
    expect(find.byType(PageView), findsNothing);
  });

  testWidgets('home shows event card from fake /events/', (tester) async {
    final api = FakeApi()
      ..club = const FakeClub.empty()
      ..events = const <FakeEvent>[
        FakeEvent(id: 7, titleEs: 'Quedada de los jueves'),
      ];

    await tester.pumpWidget(buildHome(api));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('Quedada de los jueves'), findsOneWidget);
  });

  testWidgets('home shows club contact card from fake /club/', (tester) async {
    final api = FakeApi()
      ..club = const FakeClub(
        name: 'Andes Padel',
        address: 'Rodriguez Labandera y Ernesto Alban, Quito',
        phone: '0992676842',
        email: 'andespadelclub@gmail.com',
        whatsappNumber: '593992676842',
        instagramUrl: 'https://instagram.com/andespadelec',
      );

    await tester.pumpWidget(buildHome(api));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);

    // Club card sits below the fold on a phone-sized surface.
    await tester.scrollUntilVisible(
      find.text('Andes Padel'),
      240,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();

    // Real success signals: the fake club payload reached the UI.
    expect(find.text('Andes Padel'), findsWidgets);
    expect(find.text('0992676842'), findsOneWidget);
    expect(find.text('andespadelclub@gmail.com'), findsOneWidget);
    expect(find.text('WhatsApp'), findsOneWidget);
    expect(find.text('Llamar'), findsOneWidget);
  });

  testWidgets('home hides contact rows when club fields are empty',
      (tester) async {
    final api = FakeApi()
      ..club = const FakeClub(
        name: 'Andes Padel',
        email: 'club@test.com',
      );

    await tester.pumpWidget(buildHome(api));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);

    await tester.scrollUntilVisible(
      find.text('Información del club'),
      240,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();

    expect(find.text('club@test.com'), findsOneWidget);
    expect(find.text('WhatsApp'), findsNothing);
    expect(find.text('0992676842'), findsNothing);
    // Address row label is only rendered when an address exists.
    expect(find.text('Contacto del club'), findsNothing);
  });

  testWidgets('home shows network-error state when /club/ is unreachable',
      (tester) async {
    final api = FakeApi()..offline = true;

    await tester.pumpWidget(buildHome(api));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);

    await tester.scrollUntilVisible(
      find.text('Error de conexión. Verifica tu internet.').first,
      240,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();

    // Real failure signal: the error state, not a silent empty card.
    expect(
      find.text('Error de conexión. Verifica tu internet.'),
      findsWidgets,
    );
    expect(find.text('Reintentar'), findsWidgets);
  });
}
