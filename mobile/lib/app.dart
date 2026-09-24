import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/api_client.dart';
import 'core/locale_controller.dart';
import 'core/push_notification_service.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'core/storage.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/auth_state.dart';
import 'features/auth/login_screen.dart';
import 'features/booking/booking_wizard_screen.dart';
import 'features/notifications/unread_store.dart';
import 'shell/app_shell.dart';

class AndesPadelApp extends StatelessWidget {
  AndesPadelApp(
      {super.key,
      required ApiClient api,
      required TokenStorage storage,
      required LocaleController localeController,
      required PushNotificationService pushService,
      GlobalKey<NavigatorState>? navigatorKey})
      : _api = api,
        _auth = AuthState(api: api, storage: storage),
        _localeController = localeController,
        _pushService = pushService,
        _navigatorKey = navigatorKey;

  final ApiClient _api;
  final AuthState _auth;
  final LocaleController _localeController;
  final PushNotificationService _pushService;
  final GlobalKey<NavigatorState>? _navigatorKey;
  final UnreadStore _unread = UnreadStore();

  @override
  Widget build(BuildContext context) {
    // A foreground push must show up as a new/unread item immediately.
    _pushService.onNotificationReceived ??= _unread.increment;
    return MultiProvider(
      providers: [
        Provider<ApiClient>.value(value: _api),
        Provider<PushNotificationService>.value(value: _pushService),
        ChangeNotifierProvider<AuthState>.value(value: _auth),
        ChangeNotifierProvider<LocaleController>.value(value: _localeController),
        ChangeNotifierProvider<UnreadStore>.value(value: _unread),
      ],
      child: Consumer<LocaleController>(
        builder: (context, locale, _) {
          return MaterialApp(
            debugShowCheckedModeBanner: false,
            navigatorKey: _navigatorKey,
            onGenerateTitle: (context) =>
                AppLocalizations.of(context).appTitle,
            localizationsDelegates:
                AppLocalizations.localizationsDelegates,
            supportedLocales: AppLocalizations.supportedLocales,
            // ALWAYS the in-app choice (Spanish by default). Never the device
            // locale — a Portuguese phone must not translate the UI.
            locale: locale.locale,
            localeResolutionCallback: (device, supported) {
              final chosen = locale.locale;
              for (final l in supported) {
                if (l.languageCode == chosen.languageCode) return l;
              }
              return const Locale('es');
            },
            theme: AppTheme.light,
            darkTheme: AppTheme.dark,
            themeMode: ThemeMode.system,
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
    final pushService = context.read<PushNotificationService>();
    widget.auth.restoreSession().then((_) {
      if (widget.auth.authenticated) {
        // Load profile data only. NEVER apply `language_code` to the UI:
        // the in-app Profile picker owns the language, and letting the server
        // (or an error rebuild) touch it is what flipped the app to Portuguese.
        widget.auth.loadMe().catchError((_) {});
        pushService.registerToken().catchError((_) {});
      }
    }).catchError((_) {
      // Always ensure app shows login even if restore fails
      if (!widget.auth.initialized) {
        widget.auth.markInitialized();
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
