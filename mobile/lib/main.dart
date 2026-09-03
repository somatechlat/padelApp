import 'package:flutter/material.dart';

import 'app.dart';
import 'core/api_client.dart';
import 'core/locale_controller.dart';
import 'core/push_notification_service.dart';
import 'core/storage.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final storage = SecureTokenStorage();
  final api = ApiClient(storage: storage);
  final localeController = LocaleController(storage: storage);
  final pushService = PushNotificationService(api: api);
  await localeController.load();
  await pushService.initialize();
  runApp(AndesPadelApp(
    api: api,
    storage: storage,
    localeController: localeController,
    pushService: pushService,
  ));
}
