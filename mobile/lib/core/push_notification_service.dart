import 'dart:convert';
import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import '../core/api_client.dart';
import '../firebase_options.dart';

// Firebase is configured from the real project (andespadel-21f1e) via
// firebase_options.dart, plus the native google-services.json /
// GoogleService-Info.plist. All three are gitignored because they are
// project credentials supplied out-of-band; run `flutterfire configure` on a
// fresh clone to regenerate them.

/// Handles Firebase Cloud Messaging (FCM) push notifications.
///
/// Responsibilities:
/// - Initialize Firebase and request notification permissions
/// - Register the FCM device token with the backend on login
/// - Display incoming push notifications when the app is in foreground
/// - Handle notification tap navigation
///
/// When Firebase is not configured (see comment above), [initialize] logs at
/// info that push is disabled and the registration/token calls become no-ops.
class PushNotificationService {
  PushNotificationService(
      {required ApiClient api, GlobalKey<NavigatorState>? navigatorKey})
      : _api = api,
        _navigatorKey = navigatorKey;

  final ApiClient _api;
  final GlobalKey<NavigatorState>? _navigatorKey;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  /// True only after [Firebase.initializeApp] succeeds. When false, push is
  /// disabled and every public method is a no-op.
  bool _firebaseReady = false;

  /// Fired when a push arrives (foreground) so the UI can mark it as new.
  void Function()? onNotificationReceived;

  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'andes_padel_channel',
    'Andes Padel',
    description: 'Notificaciones de reservas, pagos y eventos',
    importance: Importance.high,
  );

  /// Initialize Firebase, request permissions, and set up message handlers.
  /// Call this once at app startup (before runApp or in main).
  Future<void> initialize() async {
    // Explicit options from firebase_options.dart (project andespadel-21f1e).
    // A bare initializeApp() relies on the native plist being discovered and
    // logged "No app has been configured yet" before FCM came up; passing the
    // options makes init deterministic on both platforms.
    try {
      await Firebase.initializeApp(
        options: DefaultFirebaseOptions.currentPlatform,
      );
      _firebaseReady = true;
      debugPrint('Firebase initialised (push enabled)');
    } catch (e) {
      _firebaseReady = false;
      debugPrint('Push notifications disabled (Firebase init failed): $e');
      return;
    }

    // Create the Android channel and wire the foreground/notification-tap
    // handlers BEFORE the permission prompt. Registering handlers is what makes
    // delivery work; it must not be skipped if the user is slow to answer the
    // system permission sheet (or if it is denied).
    await _localNotifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(_channel);

    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );
    await _localNotifications.initialize(
      settings: const InitializationSettings(
        android: androidSettings,
        iOS: iosSettings,
      ),
    );

    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);

    // Request permission last (iOS shows a system sheet; Android auto-grants).
    // Do not return early on denial — handlers above stay registered so a later
    // grant in Settings starts delivering without an app restart.
    try {
      final settings = await FirebaseMessaging.instance.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        provisional: false,
      );
      debugPrint(
          'Push permission status: ${settings.authorizationStatus.name}');
    } catch (e) {
      debugPrint('Push permission request failed: $e');
    }

    // If the app was opened from a notification, navigate now.
    final initialMessage = await FirebaseMessaging.instance.getInitialMessage();
    if (initialMessage != null) {
      _handleNotificationTap(initialMessage);
    }
  }

  /// Register the FCM device token with the backend.
  /// Call this after successful login.
  /// No-op when Firebase is not configured.
  Future<void> registerToken() async {
    if (!_firebaseReady) {
      debugPrint('FCM token registration skipped (push disabled)');
      return;
    }
    try {
      final token = await FirebaseMessaging.instance.getToken();
      if (token != null && token.isNotEmpty) {
        await _api.post('/auth/me/devices/', data: {
          'platform': Platform.isIOS ? 'ios' : 'android',
          'device_token': token,
        });
        debugPrint('FCM token registered: ${token.substring(0, 20)}...');
      }

      // Listen for token refresh
      FirebaseMessaging.instance.onTokenRefresh.listen((newToken) async {
        try {
          await _api.post('/auth/me/devices/', data: {
            'platform': Platform.isIOS ? 'ios' : 'android',
            'device_token': newToken,
          });
        } catch (e) {
          debugPrint('FCM token refresh registration failed: $e');
        }
      });
    } catch (e) {
      debugPrint('FCM token registration failed: $e');
    }
  }

  /// Handle a message received while the app is in the foreground.
  void _handleForegroundMessage(RemoteMessage message) {
    onNotificationReceived?.call();

    final notification = message.notification;
    if (notification == null) return;

    _localNotifications.show(
      id: notification.hashCode,
      title: notification.title,
      body: notification.body,
      notificationDetails: NotificationDetails(
        android: AndroidNotificationDetails(
          _channel.id,
          _channel.name,
          channelDescription: _channel.description,
          icon: '@mipmap/ic_launcher',
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: const DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        ),
      ),
      payload: jsonEncode(message.data),
    );
  }

  /// Handle a notification tap (app opened from background/terminated).
  void _handleNotificationTap(RemoteMessage message) {
    final data = message.data;
    debugPrint('Notification tapped: $data');
    final nav = _navigatorKey?.currentState;
    if (nav == null) return;
    // Navigate to the shell (notifications tab will be visible)
    nav.pushNamedAndRemoveUntil('/shell', (route) => false);
  }
}
