import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/api_client.dart';
import 'core/locale_controller.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import 'core/storage.dart';
import 'features/auth/auth_state.dart';
import 'features/auth/login_screen.dart';
import 'features/booking/booking_wizard_screen.dart';
import 'shell/app_shell.dart';

class AndesPadelApp extends StatelessWidget {
  AndesPadelApp(
      {super.key,
      required ApiClient api,
      required TokenStorage storage,
      required LocaleController localeController})
      : _auth = AuthState(api: api, storage: storage),
        _localeController = localeController;

  final AuthState _auth;
  final LocaleController _localeController;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthState>.value(value: _auth),
        ChangeNotifierProvider<LocaleController>.value(value: _localeController),
      ],
      child: Consumer<LocaleController>(
        builder: (context, locale, _) {
          return MaterialApp(
            onGenerateTitle: (context) =>
                AppLocalizations.of(context).appTitle,
            localizationsDelegates:
                AppLocalizations.localizationsDelegates,
            supportedLocales: AppLocalizations.supportedLocales,
            locale: locale.locale ?? const Locale('es'),
            theme: ThemeData(
              colorScheme:
                  ColorScheme.fromSeed(seedColor: const Color(0xFF1B5E20)),
              useMaterial3: true,
            ),
            routes: {
              '/login': (_) => const LoginScreen(),
              '/shell': (_) => const AppShell(),
              '/bookings/new': (_) => const BookingWizardScreen(),
            },
            home: _AuthGate(auth: _auth),
          );
        },
      ),
    );
  }
}

class _AuthGate extends StatefulWidget {
  const _AuthGate({required this.auth});

  final AuthState auth;

  @override
  State<_AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<_AuthGate> {
  @override
  void initState() {
    super.initState();
    final locale = context.read<LocaleController>();
    widget.auth.restoreSession().then((_) {
      if (widget.auth.authenticated) {
        widget.auth.loadMe().then((_) {
          final user = widget.auth.user;
          if (user != null) {
            final code = user['language_code'] as String?;
            if (code != null && code.isNotEmpty) {
              locale.setLanguage(code);
            }
          }
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthState>(
      builder: (context, auth, _) {
        if (!auth.initialized) {
          return const Scaffold(
              body: Center(child: CircularProgressIndicator()));
        }
        return auth.authenticated ? const AppShell() : const LoginScreen();
      },
    );
  }
}
