import 'dart:io';

import 'package:dio/dio.dart';

import 'l10n/app_localizations.dart';

/// Maps raw exceptions (especially `DioException`) to short, human-readable,
/// localized copy. Never returns a stack trace, `Exception: ...` dump, or
/// anything with braces — those belong in `debugPrint`, not in the UI.
String friendlyErrorMessage(Object error, AppLocalizations l10n) {
  if (error is DioException) {
    if (_isNetworkError(error)) {
      return l10n.networkError;
    }

    if (error.type == DioExceptionType.badResponse) {
      final code = error.response?.statusCode ?? 0;
      final detail = _humanDetail(error.response?.data);
      if (detail != null) return detail;
      if (code >= 500) return l10n.error;
      return l10n.error;
    }

    // unknown / cancel / badCertificate fall through to a short message
    return l10n.error;
  }

  if (error is SocketException || error is HttpException) {
    return l10n.networkError;
  }

  return l10n.error;
}

/// True for every flavour of "could not reach the server".
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

/// Pull a short human `detail`/`message` out of an API error body.
/// Returns null when the body is missing, non-text, or itself looks like a
/// debug dump (so it can never leak back to the user).
String? _humanDetail(dynamic data) {
  if (data is! Map) return null;
  final raw = data['detail'] ?? data['message'] ?? data['error'];
  if (raw is! String) return null;
  final text = raw.trim();
  if (text.isEmpty || text.length > 180) return null;
  // Reject anything that looks like a stack trace or exception dump.
  if (text.contains('Exception') ||
      text.contains('DioException') ||
      text.contains('#0') ||
      text.contains('package:') ||
      text.contains('StackTrace') ||
      text.contains('{') ||
      text.contains('[')) {
    return null;
  }
  return text;
}
