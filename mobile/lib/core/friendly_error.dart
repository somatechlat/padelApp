import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';

import 'l10n/app_localizations.dart';

/// Maps raw exceptions to short, localized UI copy.
/// Never returns stack traces or `Exception: ...` dumps.
String friendlyErrorMessage(Object error, AppLocalizations l10n) {
  if (error is DioException) {
    if (_isNetworkError(error)) {
      return l10n.networkError;
    }
    if (error.type == DioExceptionType.badResponse) {
      final res = error.response;
      final code = res?.statusCode ?? 0;
      final body = _asJsonMap(res?.data);
      final mapped = _fromApiBody(body, code, l10n);
      if (mapped != null) return mapped;
      if (code == 401) return l10n.invalidCredentials;
      if (code == 403) return l10n.accountInactive;
      if (code == 409) return _pick(body, l10n.error);
      if (code == 404) return l10n.error;
      return l10n.error;
    }
    return l10n.error;
  }

  if (error is AppAuthException) {
    return error.message;
  }

  if (error is SocketException || error is HttpException) {
    return l10n.networkError;
  }

  return l10n.error;
}

class AppAuthException implements Exception {
  AppAuthException(this.message);
  final String message;
  @override
  String toString() => message;
}

bool _isNetworkError(DioException e) {
  switch (e.type) {
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
    case DioExceptionType.transformTimeout:
    case DioExceptionType.connectionError:
    case DioExceptionType.badCertificate:
      return true;
    case DioExceptionType.unknown:
      return e.error is SocketException || e.error is HttpException;
    case DioExceptionType.cancel:
    case DioExceptionType.badResponse:
      return false;
  }
}

Map<String, dynamic>? _asJsonMap(dynamic data) {
  if (data is Map) return data.map((k, v) => MapEntry(k.toString(), v));
  if (data is String) {
    try {
      final decoded = jsonDecode(data);
      if (decoded is Map) {
        return decoded.map((k, v) => MapEntry(k.toString(), v));
      }
    } catch (_) {
      return null;
    }
  }
  return null;
}

/// Prefer structured API `code`, then a safe human `detail`.
String? _fromApiBody(
    Map<String, dynamic>? body, int status, AppLocalizations l10n) {
  if (body == null) {
    return status == 401 ? l10n.invalidCredentials : null;
  }

  final apiCode = (body['code'] ?? body['error_code'] ?? '').toString();
  switch (apiCode) {
    case 'invalid_credentials':
      return l10n.invalidCredentials;
    case 'account_locked':
      return l10n.accountLocked;
    case 'account_inactive':
      return l10n.accountInactive;
    case 'email_not_verified':
      return l10n.emailNotVerified;
  }

  // DRF field errors: {"password": ["..."]} / {"email": ["..."]}
  for (final key in const [
    'password',
    'email',
    'non_field_errors',
    'detail',
    'message',
    'error',
  ]) {
    final mapped = _humanValue(body[key], l10n, status: status);
    if (mapped != null) return mapped;
  }

  // Any other short string values (first only).
  for (final value in body.values) {
    final mapped = _humanValue(value, l10n, status: status);
    if (mapped != null) return mapped;
  }
  return null;
}

String? _humanValue(dynamic raw, AppLocalizations l10n, {int status = 0}) {
  if (raw == null) return null;
  if (raw is List) {
    for (final item in raw) {
      final mapped = _humanValue(item, l10n, status: status);
      if (mapped != null) return mapped;
    }
    return null;
  }
  if (raw is Map) {
    // AuthenticationFailed: {code, message}
    final code = (raw['code'] ?? '').toString();
    if (code == 'invalid_credentials') return l10n.invalidCredentials;
    if (code == 'account_locked') return l10n.accountLocked;
    if (code == 'account_inactive') return l10n.accountInactive;
    if (code == 'email_not_verified') return l10n.emailNotVerified;
    return _humanValue(raw['message'] ?? raw['detail'] ?? raw['error'], l10n,
        status: status);
  }
  if (raw is! String) return null;
  final text = raw.trim();
  if (text.isEmpty || text.length > 180) return null;
  if (_looksLikeDebug(text)) return null;

  final lower = text.toLowerCase();
  if (lower.contains('credencial') || lower.contains('invalid_credentials')) {
    return l10n.invalidCredentials;
  }
  if (lower.contains('bloquead') || lower.contains('account_locked')) {
    return l10n.accountLocked;
  }
  if (lower.contains('no activa') || lower.contains('account_inactive')) {
    return l10n.accountInactive;
  }
  if (lower.contains('verifica tu email') ||
      lower.contains('email_not_verified')) {
    return l10n.emailNotVerified;
  }
  return text;
}

String _pick(Map<String, dynamic>? body, String fallback) {
  if (body == null) return fallback;
  final raw = body['detail'] ?? body['message'] ?? body['error'];
  if (raw is String && raw.trim().isNotEmpty && !_looksLikeDebug(raw)) {
    return raw.trim();
  }
  return fallback;
}

bool _looksLikeDebug(String text) {
  return text.contains('Exception') ||
      text.contains('DioException') ||
      text.contains('#0') ||
      text.contains('package:') ||
      text.contains('StackTrace') ||
      text.contains('{') ||
      text.contains('[');
}
