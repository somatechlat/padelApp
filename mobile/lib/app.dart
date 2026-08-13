import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/api_client.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import 'core/storage.dart';
import 'features/auth/auth_state.dart';
import 'features/auth/login_screen.dart';
import 'features/booking/booking_wizard_screen.dart';
import 'shell/app_shell.dart';

class AndesPadelApp extends StatelessWidget {
  AndesPadelApp(
      {super.key, required ApiClient api, required TokenStorage storage})
      : _auth = AuthState(api: api, storage: storage);

  final AuthState _auth;

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider<AuthState>.value(
      value: _auth,
      child: MaterialApp(
        onGenerateTitle: (context) => AppLocalizations.of(context).appTitle,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('es'),
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1B5E20)),
          useMaterial3: true,
        ),
        routes: {
          '/login': (_) => const LoginScreen(),
          '/shell': (_) => const AppShell(),
          '/bookings/new': (_) => const BookingWizardScreen(),
        },
        home: _AuthGate(auth: _auth),
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
    widget.auth.restoreSession().then((_) {
      if (widget.auth.authenticated) {
        widget.auth.loadMe();
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
