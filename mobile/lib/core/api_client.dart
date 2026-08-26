import 'package:dio/dio.dart';

import 'storage.dart';

/// Thin wrapper around [Dio] for the Andes Padel REST API.
///
/// Adds the JWT `Authorization` header on every request and transparently
/// refreshes the access token (single retry) when the API answers 401.
/// The [baseUrl] can be overridden at build time with
/// `--dart-define=API_BASE_URL=...` (defaults to the Android emulator host).
class ApiClient {
  ApiClient({required TokenStorage storage, Dio? dio, String? baseUrl})
      : _storage = storage,
        _dio = dio ?? Dio() {
    _dio.options.baseUrl = baseUrl ??
        const String.fromEnvironment('API_BASE_URL',
            defaultValue: 'https://andespadel.yachaq.io/api');
    _dio.options.headers['Accept'] = 'application/json';
    _dio.options.connectTimeout = const Duration(seconds: 10);
    _dio.options.receiveTimeout = const Duration(seconds: 15);
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(SecureTokenStorage.accessKey);
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
              final token = await _storage.read(SecureTokenStorage.accessKey);
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

  Future<bool> _tryRefresh() async {
    final refresh = await _storage.read(SecureTokenStorage.refreshKey);
    if (refresh == null || refresh.isEmpty) return false;
    try {
      final res = await _dio.post('/auth/refresh/', data: {'refresh': refresh});
      final access = res.data['access'] as String;
      final newRefresh = res.data['refresh'] as String?;
      await _storage.write(SecureTokenStorage.accessKey, access);
      if (newRefresh != null) {
        await _storage.write(SecureTokenStorage.refreshKey, newRefresh);
      }
      return true;
    } catch (_) {
      await _storage.clearTokens();
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
