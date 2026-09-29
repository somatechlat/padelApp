import 'dart:convert';
import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import '../core/api_client.dart';

// Firebase config (google-services.json / GoogleService-Info.plist /
// firebase_options.dart) is supplied out-of-band and is gitignored on purpose.
// This service therefore does NOT import firebase_options.dart: when Firebase
// is not configured, push is disabled at runtime and every method is a no-op,
// so a fresh clone still compiles and runs.

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
  ///
  /// Safe to call when Firebase config is absent: logs that push is disabled
  /// and returns without throwing.
  Future<void> initialize() async {
    // Native config (google-services.json via the Gradle plugin, or
    // GoogleService-Info.plist) is enough when present. firebase_options.dart
    // is intentionally not imported — it is gitignored and must not be
    // required for the tree to compile. If Firebase is not configured,
    // initializeApp throws and we leave push disabled.
    try {
      await Firebase.initializeApp();
      _firebaseReady = true;
    } catch (e) {
      _firebaseReady = false;
      debugPrint(
          'Push notifications disabled (Firebase not configured, config is supplied out-of-band and gitignored): $e');
      return;
    }

    // Request permission (iOS required, Android auto-grants)
    final settings = await FirebaseMessaging.instance.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );
    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      debugPrint('Push notifications permission denied');
      return;
    }

    // Create Android notification channel
    await _localNotifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(_channel);

    // Initialize local notifications for foreground display
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

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // Handle notification tap when app is in background/terminated
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);

    // Check if app was opened from a notification
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
