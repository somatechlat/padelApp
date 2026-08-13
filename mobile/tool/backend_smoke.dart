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

  final me = await dio.get('/auth/me/', options: Options(headers: headers));
  print('me: ${me.statusCode} ${me.data}');

  final courts = await dio.get('/courts/', options: Options(headers: headers));
  print('courts: ${courts.statusCode} count=${(courts.data as Map)['count']}');

  final bookings = await dio.get('/bookings/', options: Options(headers: headers));
  print('bookings: ${bookings.statusCode}');

  final tournaments = await dio.get('/tournaments/', options: Options(headers: headers));
  print('tournaments: ${tournaments.statusCode}');

  final notifications = await dio.get('/notifications/', options: Options(headers: headers));
  print('notifications: ${notifications.statusCode}');

  print('SMOKE_OK');
}
