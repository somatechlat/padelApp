import 'package:flutter/material.dart';

import 'app.dart';
import 'core/api_client.dart';
import 'core/locale_controller.dart';
import 'core/push_notification_service.dart';
import 'core/storage.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final navigatorKey = GlobalKey<NavigatorState>();
  final storage = SecureTokenStorage();
  final localeController = LocaleController(storage: storage);
  final api = ApiClient(
    storage: storage,
    languageCode: () => localeController.code,
  );
  final pushService =
      PushNotificationService(api: api, navigatorKey: navigatorKey);

  // Draw the first frame immediately. Secure-storage / Firebase / FCM can
  // block on the keychain or the network — never let that delay runApp or
  // the app opens to a blank white screen.
  runApp(AndesPadelApp(
    api: api,
    storage: storage,
    localeController: localeController,
    pushService: pushService,
    navigatorKey: navigatorKey,
  ));

  await _initBackground(localeController, pushService);
}

Future<void> _initBackground(
  LocaleController localeController,
  PushNotificationService pushService,
) async {
  try {
    await localeController.load().timeout(const Duration(seconds: 5));
  } catch (e) {
    debugPrint('Locale load failed: $e');
  }
  try {
    await pushService.initialize().timeout(const Duration(seconds: 10));
  } catch (e) {
    debugPrint('Push notification init failed: $e');
  }
}
