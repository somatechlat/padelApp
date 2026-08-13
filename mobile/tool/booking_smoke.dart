import 'package:dio/dio.dart';

Future<void> main() async {
  final dio = Dio(
    BaseOptions(baseUrl: 'http://backend:8000/api', connectTimeout: const Duration(seconds: 10)),
  );

  final login = await dio.post('/auth/login/',
      data: {'email': 'smoke@andespadel.com', 'password': 'Smoke12345!'});
  print('login: ${login.statusCode}');
  final access = (login.data as Map)['access'] as String;
  final headers = {'Authorization': 'Bearer $access'};

  final courts = await dio.get('/courts/', options: Options(headers: headers));
  final court = ((courts.data as Map)['results'] as List).first as Map;
  final courtId = court['id'];
  print('court: $courtId ${court['name']} price=${court['price_base']}');

  final day = DateTime.now().add(const Duration(days: 2));
  final date = '${day.year.toString().padLeft(4, '0')}-${day.month.toString().padLeft(2, '0')}-${day.day.toString().padLeft(2, '0')}';
  final avail = await dio.get('/courts/$courtId/availability/',
      queryParameters: {'date': date}, options: Options(headers: headers));
  final slots = (avail.data as List).where((s) => (s as Map)['status'] == 'available').toList();
  print('availability: ${avail.statusCode} slots=${slots.length}');
  if (slots.isEmpty) {
    print('SKIP: no slots for $date');
    return;
  }
  final slot = slots.first as Map;
  final start = slot['start'].toString().substring(0, 5);

  final preview = await dio.post('/bookings/preview/',
      data: {'court': courtId, 'date': date, 'start_time': start, 'duration_minutes': 60},
      options: Options(headers: headers));
  print('preview: ${preview.statusCode} price=${preview.data}');

  final booking = await dio.post('/bookings/',
      data: {'court': courtId, 'date': date, 'start_time': start, 'duration_minutes': 60, 'players': 4},
      options: Options(headers: headers));
  final bookingId = (booking.data as Map)['id'];
  print('create: ${booking.statusCode} id=$bookingId status=${(booking.data as Map)['status']}');

  final confirm = await dio.post('/bookings/$bookingId/confirm/',
      options: Options(headers: headers));
  print('confirm: ${confirm.statusCode} status=${(confirm.data as Map)['status']}');

  final payment = await dio.post('/bookings/$bookingId/payments/',
      data: {'method': 'transfer', 'reference': 'SMOKE'},
      options: Options(headers: headers));
  print('payment: ${payment.statusCode} method=${(payment.data as Map)['method']} status=${(payment.data as Map)['status']}');

  final notifications = await dio.get('/notifications/', options: Options(headers: headers));
  final items = (notifications.data as Map)['results'] as List;
  final latest = items.first as Map;
  print('notifications: ${notifications.statusCode} count=${items.length} latest=${latest['event_type']}: ${latest['title']}');

  final read = await dio.post('/notifications/${latest['id']}/read/',
      options: Options(headers: headers));
  print('markRead: ${read.statusCode}');

  final prefs = await dio.get('/notifications/preferences/', options: Options(headers: headers));
  print('prefs: ${prefs.statusCode} count=${(prefs.data as List).length}');

  final putPrefs = await dio.put('/notifications/preferences/',
      data: [
        {'event_type': 'marketing', 'channel': 'push', 'enabled': false},
        {'event_type': 'marketing', 'channel': 'email', 'enabled': false},
        {'event_type': 'marketing', 'channel': 'inapp', 'enabled': true},
      ],
      options: Options(headers: headers));
  print('putPrefs: ${putPrefs.statusCode} count=${(putPrefs.data as List).length}');

  final lang = await dio.patch('/auth/me/', data: {'language_code': 'en'},
      options: Options(headers: headers));
  print('lang: ${lang.statusCode} code=${(lang.data as Map)['language_code']}');
  await dio.patch('/auth/me/', data: {'language_code': 'es'},
      options: Options(headers: headers));

  final cancel = await dio.post('/bookings/$bookingId/cancel/',
      options: Options(headers: headers));
  print('cancel: ${cancel.statusCode} status=${(cancel.data as Map)['status']}');

  print('BOOKING_SMOKE_OK');
}
