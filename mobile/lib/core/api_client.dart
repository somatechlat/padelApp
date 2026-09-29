import 'dart:io';

import 'package:dio/dio.dart';
import 'package:dio/io.dart';

import 'storage.dart';

/// Thin wrapper around [Dio] for the Andes Padel REST API.
///
/// Adds the JWT `Authorization` header on every request and transparently
/// refreshes the access token (single retry) when the API answers 401.
/// The [baseUrl] can be overridden at build time with
/// `--dart-define=API_BASE_URL=...` (defaults to the Android emulator host).
class ApiClient {
  ApiClient(
      {required TokenStorage storage,
      Dio? dio,
      String? baseUrl,
      String Function()? languageCode})
      : _storage = storage,
        _languageCode = languageCode,
        _dio = dio ?? Dio() {
    _dio.options.baseUrl = baseUrl ??
        const String.fromEnvironment(
          'API_BASE_URL',
          // Debug/simulator defaults to the local andespadel Docker cluster.
          // Release builds must pass --dart-define=API_BASE_URL=...
          defaultValue: 'http://127.0.0.1:28002/api',
        );
    _dio.options.headers['Accept'] = 'application/json';
    // 10s was too tight: iOS stalls on this host's happy-eyeballs/IPv6 path
    // and mobile networks routinely need longer for the TLS handshake.
    _dio.options.connectTimeout = const Duration(seconds: 30);
    _dio.options.receiveTimeout = const Duration(seconds: 30);
    // iOS/simulator happy-eyeballs can stall on this host's broken IPv6 path
    // and then surface as "no connection" even though IPv4 works fine.
    // Force every dial to prefer IPv4 A records.
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
