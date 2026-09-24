// File manually wired from google-services.json / GoogleService-Info.plist
// (equivalent to what `flutterfire configure` would generate). These values are
// public client identifiers that ship inside the app binary — not secrets.
import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Default [FirebaseOptions] for use with your Firebase apps.
///
/// Example:
/// ```dart
/// import 'firebase_options.dart';
/// // ...
/// await Firebase.initializeApp(
///   options: DefaultFirebaseOptions.currentPlatform,
/// );
/// ```
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      throw UnsupportedError(
        'DefaultFirebaseOptions have not been configured for web - '
        'you can reconfigure this by running the FlutterFire CLI again.',
      );
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        return ios;
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }
  }

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyCP68Y2pOx4SRovejnoUum9NfC-T8IIix4',
    appId: '1:311968091307:android:1521f3723f4d639ec7fbee',
    messagingSenderId: '311968091307',
    projectId: 'andespadel-21f1e',
    storageBucket: 'andespadel-21f1e.firebasestorage.app',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyBGHaf9lKl-co2CYlvqDQXZbiKeGMCj8ts',
    appId: '1:311968091307:ios:769c6cb44ad49270c7fbee',
    messagingSenderId: '311968091307',
    projectId: 'andespadel-21f1e',
    storageBucket: 'andespadel-21f1e.firebasestorage.app',
    iosBundleId: 'com.andes.padel.padelApp',
  );
}
