import 'dart:io';

import 'package:integration_test/integration_test_driver_extended.dart';

/// Collects screenshots from the running app and writes them on the host.
///
/// The app under test cannot write to the host filesystem and cannot read
/// host environment variables, so the test only *names* the screenshot and
/// this driver persists the bytes.
Future<void> main() async {
  final outDir = Directory(Platform.environment['SCREENSHOT_DIR'] ?? 'shots')
    ..createSync(recursive: true);

  await integrationDriver(
    onScreenshot: (String name, List<int> bytes,
        [Map<String, Object?>? args]) async {
      final file = File('${outDir.path}/$name.png');
      file.writeAsBytesSync(bytes);
      stdout.writeln('SNAPSHOT $name -> ${file.path}');
      return true;
    },
  );
}
