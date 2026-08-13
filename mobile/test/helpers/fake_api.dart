import 'package:padel_app/core/api_client.dart';
import 'package:padel_app/core/storage.dart';

class FakeApi extends ApiClient {
  FakeApi() : super(storage: InMemoryTokenStorage());

  bool logouted = false;
  Map<String, dynamic> loginResponse = {
    'access': 'fake-access',
    'refresh': 'fake-refresh',
    'user': {
      'email': 'cliente@andespadel.com',
      'full_name': 'Cliente Test',
      'role': 'cliente',
      'status': 'active',
      'email_verified': true,
    },
  };

  @override
  Future<dynamic> post(String path, {Object? data}) async {
    switch (path) {
      case '/auth/login/':
        return loginResponse;
      case '/auth/register/':
        return {'email': 'x@test.com', 'detail': 'ok'};
      case '/auth/verify/':
        return {'detail': 'Email verificado'};
      case '/auth/password-reset/':
        return {'detail': 'Si el email existe, recibira un codigo'};
      case '/auth/password-reset/confirm/':
        return {'detail': 'Contrasena actualizada'};
      default:
        return {'detail': 'ok'};
    }
  }

  @override
  Future<dynamic> get(String path, {Map<String, dynamic>? query}) async {
    switch (path) {
      case '/auth/me/':
        return {
          'email': 'cliente@andespadel.com',
          'full_name': 'Cliente Test',
          'role': 'cliente',
          'status': 'active',
          'email_verified': true,
        };
      case '/bookings/':
        return {'results': []};
      case '/tournaments/':
        return {'results': []};
      case '/notifications/':
        return {'results': []};
      default:
        return {'results': []};
    }
  }

  @override
  Future<void> logout(String refresh) async {
    logouted = true;
  }
}
