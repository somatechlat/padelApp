import 'dart:io';

import 'package:dio/dio.dart';

/// Comprehensive E2E smoke test for Andes Pádel system.
///
/// Tests every API module: Auth → Courts → Availability → Bookings →
/// Payments → Notifications → Events → Tournaments → News → Profile → GDPR
///
/// Usage: docker compose run --rm flutter dart run /mobile/tool/smoke_test.dart
const _base = 'http://backend:8000/api';
const _adminEmail = 'admin@andespadel.com';
const _clientEmail = 'cliente@andespadel.com';
const _password = 'Andes12345!';
int _passed = 0;
int _failed = 0;

Future<void> main() async {
  final dio = Dio(BaseOptions(
    baseUrl: _base,
    connectTimeout: const Duration(seconds: 10),
    validateStatus: (_) => true,
  ));

  print('=== Andes Padel — Full System Smoke Test ===\n');

  // ── 1. Auth ──
  String adminAccess = '';
  String clientAccess = '';

  await _section('AUTH', () async {
    final adminLogin = await _post(dio, '/auth/login/', {
      'email': _adminEmail,
      'password': _password,
    });
    _assert('admin login 200', adminLogin.statusCode == 200);
    adminAccess = (adminLogin.data as Map)['access'] as String;

    final clientLogin = await _post(dio, '/auth/login/', {
      'email': _clientEmail,
      'password': _password,
    });
    _assert('client login 200', clientLogin.statusCode == 200);
    clientAccess = (clientLogin.data as Map)['access'] as String;

    final me = await _get(dio, '/auth/me/', adminAccess);
    _assert('admin me role=superadmin', me.data['role'] == 'superadmin');
  });

  if (adminAccess.isEmpty || clientAccess.isEmpty) {
    _printSummary();
    exit(1);
  }

  // ── 2. Courts ──
  int courtId = 0;
  await _section('COURTS', () async {
    final resp = await _get(dio, '/courts/', adminAccess);
    final results = _list(resp.data);
    _assert('courts exist', results.isNotEmpty);
    for (final c in results) {
      _assert('court has name', c['name'] != null);
      _assert('court has type', c['court_type'] != null);
      _assert('court has price', c['price_base'] != null);
    }
    courtId = (results.first as Map)['id'] as int;
    print('  courts: ${results.length} found, first id=$courtId');
  });

  // ── 3. Availability ──
  await _section('AVAILABILITY', () async {
    final tomorrow = DateTime.now().add(const Duration(days: 2));
    final date = _fmtDate(tomorrow);
    final resp = await _get(
        dio, '/courts/$courtId/availability/?date=$date', clientAccess);
    final slots = _list(resp.data);
    final available = slots.where((s) => s['status'] == 'available').toList();
    _assert('slots generated', slots.isNotEmpty);
    _assert('available slots', available.isNotEmpty);
    print('  date=$date total=${slots.length} available=${available.length}');
  });

  // ── 4. Booking flow ──
  int bookingId = 0;
  await _section('BOOKING', () async {
    final tomorrow = DateTime.now().add(const Duration(days: 3));
    final date = _fmtDate(tomorrow);
    final availResp = await _get(
        dio, '/courts/$courtId/availability/?date=$date', clientAccess);
    final available =
        _list(availResp.data).where((s) => s['status'] == 'available').toList();
    if (available.isEmpty) {
      print('  SKIP: no available slots for $date');
      return;
    }
    final slot = available.first;
    final startTime = slot['start'].toString().substring(0, 5);

    final preview = await _post(dio, '/bookings/preview/', {
      'court': courtId,
      'date': date,
      'start_time': startTime,
      'duration_minutes': 60,
    }, clientAccess);
    _assert('preview has price', preview.data['price'] != null);
    print('  preview: \$${preview.data['price']}');

    final booking = await _post(dio, '/bookings/', {
      'court': courtId,
      'date': date,
      'start_time': startTime,
      'duration_minutes': 60,
      'players': 4,
    }, clientAccess);
    bookingId = booking.data['id'] as int;
    _assert('booking created', bookingId > 0);
    _assert('booking status pending_payment', booking.data['status'] == 'pending_payment');
    print('  booking id=$bookingId status=${booking.data['status']}');

    final confirm =
        await _post(dio, '/bookings/$bookingId/confirm/', null, clientAccess);
    _assert('booking confirmed', confirm.data['status'] == 'confirmed');
    print('  confirmed: status=${confirm.data['status']}');
  });

  // ── 5. Payments ──
  await _section('PAYMENTS', () async {
    if (bookingId == 0) {
      print('  SKIP: no booking');
      return;
    }
    final payment = await _post(dio, '/bookings/$bookingId/payments/', {
      'method': 'transfer',
      'reference': 'SMOKE-${DateTime.now().millisecondsSinceEpoch}',
    }, clientAccess);
    _assert('payment created', payment.data['id'] != null);
    _assert('payment pending_transfer',
        payment.data['status'] == 'pending_transfer');
    print(
        '  payment id=${payment.data['id']} status=${payment.data['status']}');
  });

  // ── 6. Notifications ──
  await _section('NOTIFICATIONS', () async {
    final resp = await _get(dio, '/notifications/', clientAccess);
    final items = _list(resp.data);
    _assert('notifications exist', items.isNotEmpty);
    print('  count=${items.length}');

    if (items.isNotEmpty) {
      final latest = items.first;
      final readResp = await _post(
          dio, '/notifications/${latest['id']}/read/', null, clientAccess);
      _assert('mark read ok', readResp.statusCode == 200);
    }

    final prefsResp =
        await _get(dio, '/notifications/preferences/', clientAccess);
    final prefList = _list(prefsResp.data);
    _assert('preferences exist', prefList.isNotEmpty);
    print('  preferences=${prefList.length}');
  });

  // ── 7. Events ──
  await _section('EVENTS', () async {
    final resp = await _get(dio, '/events/', clientAccess);
    final items = _list(resp.data);
    _assert('events exist', items.isNotEmpty);
    for (final e in items) {
      _assert('event has title', e['title_localized'] != null);
    }
    print('  count=${items.length}');
  });

  // ── 8. Tournaments ──
  await _section('TOURNAMENTS', () async {
    final resp = await _get(dio, '/tournaments/', clientAccess);
    final items = _list(resp.data);
    _assert('tournaments exist', items.isNotEmpty);
    for (final t in items) {
      _assert('tournament has name', t['name_localized'] != null);
      _assert('tournament has status', t['status'] != null);
      _assert('tournament has capacity', t['capacity'] != null);
    }
    print('  count=${items.length}');
  });

  // ── 9. News ──
  await _section('NEWS', () async {
    final resp = await _get(dio, '/news/', clientAccess);
    final items = _list(resp.data);
    _assert('news exist', items.isNotEmpty);
    print('  count=${items.length}');
  });

  // ── 10. Profile / Me ──
  await _section('PROFILE', () async {
    final meResp = await _get(dio, '/auth/me/', clientAccess);
    final me = meResp.data as Map<String, dynamic>;
    _assert('has email', me['email'] == _clientEmail);
    _assert('has full_name', me['full_name'] != null);
    _assert('has role', me['role'] != null);

    final patched =
        await _patch(dio, '/auth/me/', {'language_code': 'en'}, clientAccess);
    _assert('lang updated', patched.data['language_code'] == 'en');

    await _patch(dio, '/auth/me/', {'language_code': 'es'}, clientAccess);
  });

  // ── 11. GDPR ──
  await _section('GDPR', () async {
    final consent = await _post(dio, '/auth/me/consent/', {
      'version': '1.0',
      'granted': true,
    }, clientAccess);
    _assert('consent recorded', consent.statusCode == 201);

    final exportResp = await _get(dio, '/auth/me/export/', clientAccess);
    final export = exportResp.data as Map<String, dynamic>;
    _assert('export has profile', export['profile'] != null);
    _assert('export has bookings', export['bookings'] != null);
  });

  // ── 12. Cancel booking (cleanup) ──
  await _section('CANCEL', () async {
    if (bookingId == 0) {
      print('  SKIP: no booking to cancel');
      return;
    }
    final cancel =
        await _post(dio, '/bookings/$bookingId/cancel/', null, clientAccess);
    _assert('booking cancelled', cancel.data['status'] == 'cancelled');
    print('  status=${cancel.data['status']}');
  });

  // ── 13. Logout ──
  await _section('LOGOUT', () async {
    final loginResp = await _post(dio, '/auth/login/', {
      'email': _clientEmail,
      'password': _password,
    });
    final refresh = (loginResp.data as Map)['refresh'] as String;
    final logout = await _post(dio, '/auth/logout/', {'refresh': refresh});
    _assert('logout ok', logout.statusCode == 205);
  });

  _printSummary();
}

// ── Helpers ──

String _fmtDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

Future<Response> _get(Dio dio, String path, String token) async {
  return dio.get(path, options: _auth(token));
}

Future<Response> _post(Dio dio, String path, Object? data,
    [String? token]) async {
  return dio.post(path,
      data: data, options: token != null ? _auth(token) : null);
}

Future<Response> _patch(
    Dio dio, String path, Map<String, dynamic> data, String token) async {
  return dio.patch(path, data: data, options: _auth(token));
}

Options _auth(String token) =>
    Options(headers: {'Authorization': 'Bearer $token'});

List<dynamic> _list(dynamic data) {
  if (data is Map && data.containsKey('results')) {
    return data['results'] as List;
  }
  if (data is List) return data;
  return [];
}

void _assert(String label, bool condition) {
  if (condition) {
    _passed++;
    print('  \u2713 $label');
  } else {
    _failed++;
    print('  \u2717 FAIL: $label');
  }
}

Future<void> _section(String name, Future<void> Function() fn) async {
  print('-- $name --');
  try {
    await fn();
  } catch (e) {
    _failed++;
    print('  \u2717 EXCEPTION: $e');
  }
  print('');
}

void _printSummary() {
  print('================================');
  print('  PASSED: $_passed  FAILED: $_failed');
  if (_failed == 0) {
    print('  SMOKE_TEST_OK');
  } else {
    print('  SMOKE_TEST_FAILED');
  }
  print('================================');
}
