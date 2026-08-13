import 'package:flutter/material.dart';

import 'app.dart';
import 'core/api_client.dart';
import 'core/storage.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final storage = SecureTokenStorage();
  final api = ApiClient(storage: storage);
  runApp(AndesPadelApp(api: api, storage: storage));
}
