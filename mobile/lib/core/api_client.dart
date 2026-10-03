import 'dart:io';

import 'package:dio/dio.dart';
import 'package:dio/io.dart';
import 'package:flutter/foundation.dart';

import 'storage.dart';

/// Where a debug build talks when nobody says otherwise: the dev compose stack.
const String _devFallbackBaseUrl = 'http://127.0.0.1:28002/api';

/// Addresses that resolve to the phone itself (or an emulator on the laptop),
/// never to a deployed API.
bool _isNotADeployedHost(String url) {
  final host = Uri.tryParse(url)?.host ?? '';
  return host.isNotEmpty &&
      host != '127.0.0.1' &&
      host != 'localhost' &&
      host != '::1' &&
      host != '10.0.2.2';
}

/// Decides the API base URL for a build, refusing to guess in release mode.
///
/// Split from [resolveApiBaseUrl] so the release rule can be unit tested: the
/// test VM is never in release mode, so a guard that can only be exercised by
/// shipping is a guard nobody exercises.
String baseUrlFor(String configured, {required bool isRelease}) {
  if (isRelease && !_isNotADeployedHost(configured)) {
    throw StateError(
      'Refusing to build a release app against "$configured". Pass '
      '--dart-define=API_BASE_URL=https://<host>/api. A release binary must '
      'name a real host: loopback resolves to the device itself.',
    );
  }
  return configured.isEmpty ? _devFallbackBaseUrl : configured;
}

/// Resolves the API base URL for this build.
///
/// The previous build path defaulted to `127.0.0.1:28002` and relied on a
/// comment telling the operator to pass `--dart-define`. That is exactly the
/// kind of instruction that gets skipped, and the result ships an app that
/// cannot reach any API on any real device — silent, and only visible to a user
/// who installed it. A release binary must name a real host, so a missing or
/// loopback value is an error instead.
String resolveApiBaseUrl(String? override) => baseUrlFor(
      override ?? const String.fromEnvironment('API_BASE_URL', defaultValue: ''),
      isRelease: kReleaseMode,
    );

/// Thin wrapper around [Dio] for the Andes Padel REST API.
///
/// Adds the JWT `Authorization` header on every request and transparently
/// refreshes the access token (single retry) when the API answers 401.
/// The [baseUrl] can be overridden at build time with
/// `--dart-define=API_BASE_URL=...`; release builds require a real host, see
/// [resolveApiBaseUrl].
class ApiClient {
  ApiClient(
      {required TokenStorage storage,
      Dio? dio,
      String? baseUrl,
      String Function()? languageCode})
      : _storage = storage,
        _languageCode = languageCode,
        _dio = dio ?? Dio() {
    _dio.options.baseUrl = resolveApiBaseUrl(baseUrl);
    _dio.options.headers['Accept'] = 'application/json';
    // 10s was too tight: iOS stalls on this host's happy-eyeballs/IPv6 path
    // and mobile networks routinely need longer for the TLS handshake.
    _dio.options.connectTimeout = const Duration(seconds: 30);
    _dio.options.receiveTimeout = const Duration(seconds: 30);
    // Reset the adapter's client factory so each dial gets a fresh HttpClient
    // with an explicit connection timeout. (An earlier comment here claimed
    // this forced IPv4 A records; it never did. Dart's HttpClient does not
    // expose an address-family preference, so there is nothing to set.)
    (_dio.httpClientAdapter as IOHttpClientAdapter).createHttpClient = () {
      final client = HttpClient();
      client.connectionTimeout = const Duration(seconds: 30);
      return client;
    };
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Pin Accept-Language to the in-app choice. Without this the device
          // locale leaks through and login silently rewrites the account's
          // language_code (that is how the UI jumped to Portuguese).
          final lang = _languageCode?.call();
          options.headers['Accept-Language'] =
              (lang == null || lang.isEmpty) ? 'es' : lang;
          // Storage failures must never block the request itself (e.g.
          // flutter_secure_storage throwing on an iOS simulator would
          // otherwise kill every call, including public ones).
          String? token;
          try {
            token = await _storage.read(SecureTokenStorage.accessKey);
          } catch (_) {
            token = null;
          }
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final response = error.response;
          if (response != null && response.statusCode == 401) {
            final refreshed = await _tryRefresh();
            if (refreshed) {
              String? token;
              try {
                token = await _storage.read(SecureTokenStorage.accessKey);
              } catch (_) {
                token = null;
              }
              error.requestOptions.headers['Authorization'] = 'Bearer $token';
              try {
                final retry = await _dio.fetch(error.requestOptions);
                return handler.resolve(retry);
              } catch (e) {
                return handler.next(e is DioException
                    ? e
                    : DioException(
                        requestOptions: error.requestOptions,
                        error: e,
                      ));
              }
            }
          }
          handler.next(error);
        },
      ),
    );
  }

  final Dio _dio;
  final TokenStorage _storage;
  final String Function()? _languageCode;

  Future<bool> _tryRefresh() async {
    final refresh = await _storage.read(SecureTokenStorage.refreshKey);
    if (refresh == null || refresh.isEmpty) return false;
    try {
      final res = await _dio.post('/auth/refresh/', data: {'refresh': refresh});
      final data = res.data;
      if (data is! Map) return false;
      final access = data['access'];
      if (access is! String || access.isEmpty) return false;
      final newRefresh = data['refresh'];
      await _storage.write(SecureTokenStorage.accessKey, access);
      if (newRefresh is String && newRefresh.isNotEmpty) {
        await _storage.write(SecureTokenStorage.refreshKey, newRefresh);
      }
      return true;
    } on DioException catch (e) {
      // Only clear tokens on auth failures (401/403), not on network errors.
      final code = e.response?.statusCode;
      if (code == 401 || code == 400 || code == 403) {
        await _storage.clearTokens();
        return false;
      }
      // Network error — keep tokens so retry on next request works.
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<dynamic> get(String path, {Map<String, dynamic>? query}) async {
    final res = await _dio.get<dynamic>(path, queryParameters: query);
    return res.data;
  }

  Future<dynamic> post(String path, {Object? data}) async {
    final res = await _dio.post<dynamic>(path, data: data);
    return res.data;
  }

  Future<dynamic> put(String path, {Object? data}) async {
    final res = await _dio.put<dynamic>(path, data: data);
    return res.data;
  }

  Future<dynamic> patch(String path, {Object? data}) async {
    final res = await _dio.patch<dynamic>(path, data: data);
    return res.data;
  }

  Future<dynamic> delete(String path) async {
    final res = await _dio.delete<dynamic>(path);
    return res.data;
  }

  Future<void> logout(String refresh) async {
    try {
      await _dio.post('/auth/logout/', data: {'refresh': refresh});
    } catch (_) {
      // Ignore network errors on logout: tokens are cleared locally.
    }
    await _storage.clearTokens();
  }
}
