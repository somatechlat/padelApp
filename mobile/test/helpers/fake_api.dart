import 'package:dio/dio.dart';
import 'package:padel_app/core/api_client.dart';
import 'package:padel_app/core/storage.dart';

import 'test_storage.dart';

/// Typed fake profile for `POST /auth/login/` and `GET /auth/me/`.
class FakeUser {
  const FakeUser({
    this.email = 'cliente@andespadelclub.com',
    this.fullName = 'Cliente Test',
    this.role = 'cliente',
    this.status = 'active',
    this.emailVerified = true,
  });

  final String email;
  final String fullName;
  final String role;
  final String status;
  final bool emailVerified;

  Map<String, Object?> toJson() => <String, Object?>{
        'email': email,
        'full_name': fullName,
        'role': role,
        'status': status,
        'email_verified': emailVerified,
      };
}

/// Typed fake club settings for `GET /club/` (mirrors `ClubInfo.fromJson`).
class FakeClub {
  const FakeClub({
    this.name = 'Andes Padel',
    this.address = '',
    this.mapsUrl = '',
    this.mapsQuery = '',
    this.phone = '',
    this.email = '',
    this.whatsappNumber = '',
    this.whatsappMessage = '',
    this.instagramUrl = '',
    this.homeSectionTitle = '',
    this.homeGreetingTagline = '',
    this.logoUrl = '',
    this.bankName = '',
    this.bankAccountNumber = '',
    this.bankAccountHolder = '',
    this.bankAccountCode = '',
    this.bankExtra = '',
  });

  /// Club with every contact field empty (home hides the contact rows).
  const FakeClub.empty()
      : name = '',
        address = '',
        mapsUrl = '',
        mapsQuery = '',
        phone = '',
        email = '',
        whatsappNumber = '',
        whatsappMessage = '',
        instagramUrl = '',
        homeSectionTitle = '',
        homeGreetingTagline = '',
        logoUrl = '',
        bankName = '',
        bankAccountNumber = '',
        bankAccountHolder = '',
        bankAccountCode = '',
        bankExtra = '';

  final String name;
  final String address;
  final String mapsUrl;
  final String mapsQuery;
  final String phone;
  final String email;
  final String whatsappNumber;
  final String whatsappMessage;
  final String instagramUrl;
  final String homeSectionTitle;
  final String homeGreetingTagline;
  final String logoUrl;
  final String bankName;
  final String bankAccountNumber;
  final String bankAccountHolder;
  final String bankAccountCode;
  final String bankExtra;

  Map<String, Object?> toJson() => <String, Object?>{
        'name': name,
        'address': address,
        'maps_url': mapsUrl,
        'maps_query': mapsQuery,
        'phone': phone,
        'email': email,
        'whatsapp_number': whatsappNumber,
        'whatsapp_message': whatsappMessage,
        'instagram_url': instagramUrl,
        'home_section_title': homeSectionTitle,
        'home_greeting_tagline': homeGreetingTagline,
        'logo_url': logoUrl,
        'bank_name': bankName,
        'bank_account_number': bankAccountNumber,
        'bank_account_holder': bankAccountHolder,
        'bank_account_code': bankAccountCode,
        'bank_extra': bankExtra,
      };
}

/// Typed fake promo banner for `GET /banners/`.
class FakeBanner {
  const FakeBanner({
    this.id = 1,
    this.title = '',
    this.subtitle = '',
    this.image = 'https://example.com/banner.jpg',
    this.linkUrl = '',
    this.linkType = '',
    this.sortOrder = 0,
  });

  final int id;
  final String title;
  final String subtitle;
  final String image;
  final String linkUrl;
  final String linkType;
  final int sortOrder;

  Map<String, Object?> toJson() => <String, Object?>{
        'id': id,
        'title': title,
        'subtitle': subtitle,
        'image': image,
        'link_url': linkUrl,
        'link_type': linkType,
        'sort_order': sortOrder,
      };
}

/// Typed fake event for `GET /events/`.
class FakeEvent {
  const FakeEvent({
    this.id = 1,
    this.titleEs = 'Quedada de prueba',
    this.startAt = '2026-10-01T18:00:00Z',
  });

  final int id;
  final String titleEs;
  final String startAt;

  Map<String, Object?> toJson() => <String, Object?>{
        'id': id,
        'title_es': titleEs,
        'title': titleEs,
        'start_at': startAt,
      };
}

/// Hermetic stand-in for the Andes Padel REST API.
///
/// Extends [ApiClient] so production call sites type-check unchanged, but every
/// answer is served from memory — no sockets, no Docker, no network. Failures
/// are injected as real [DioException]s so `AuthState.lastError` carries the
/// same type it would against the live backend.
class FakeApi extends ApiClient {
  FakeApi._(this.tokenStorage) : super(storage: tokenStorage);

  factory FakeApi({TokenStorage? storage}) {
    final TokenStorage s = storage ?? InMemoryTokenStorage();
    return FakeApi._(s);
  }

  /// The storage [ApiClient] is wired to. Share it with `AuthState` to assert
  /// tokens actually land in (or are cleared from) persistence.
  final TokenStorage tokenStorage;

  // ── Fixtures ────────────────────────────────────────────────────────────
  /// Credentials accepted by `POST /auth/login/`. Anything else is a 401.
  String email = 'cliente@andespadelclub.com';
  String password = 'Andes12345!';

  /// Tokens returned by a successful login.
  String accessToken = 'fake-access';
  String refreshToken = 'fake-refresh';

  FakeUser user = const FakeUser();
  FakeClub club = const FakeClub();
  List<FakeBanner> banners = const <FakeBanner>[];
  List<FakeEvent> events = const <FakeEvent>[];

  /// When true every request fails with a connection-style [DioException],
  /// simulating the backend being unreachable.
  bool offline = false;

  // ── Call log (typed, for success-signal assertions) ─────────────────────
  /// Emails accepted by `POST /auth/register/`, in order.
  final List<String> registeredEmails = <String>[];

  /// Emails accepted by `POST /auth/password-reset/`, in order.
  final List<String> passwordResetEmails = <String>[];

  /// Refresh tokens received by `logout`.
  final List<String> logoutRefreshes = <String>[];

  /// True once `logout` has run.
  bool get loggedOut => logoutRefreshes.isNotEmpty;

  // ── Request surface ─────────────────────────────────────────────────────
  @override
  Future<Object?> get(String path, {Map<String, dynamic>? query}) async {
    if (offline) _throwOffline(path);
    switch (path) {
      case '/auth/me/':
        return user.toJson();
      case '/club/':
        return club.toJson();
      case '/banners/':
        return <String, Object?>{
          'results': <Object?>[for (final b in banners) b.toJson()],
        };
      case '/events/':
        return <String, Object?>{
          'results': <Object?>[for (final e in events) e.toJson()],
        };
      default:
        // Bookings, tournaments, notifications, news, courts… empty lists keep
        // the app shell from crashing while still being a typed success.
        return <String, Object?>{'results': <Object?>[]};
    }
  }

  @override
  Future<Object?> post(String path, {Object? data}) async {
    if (offline) _throwOffline(path);
    final Map<String, Object?> body = _asJsonMap(data);
    switch (path) {
      case '/auth/login/':
        return _login(path, body);
      case '/auth/register/':
        final String registered =
            (body['email'] as String? ?? '').trim().toLowerCase();
        registeredEmails.add(registered);
        return <String, Object?>{
          'email': registered,
          'detail': 'ok',
        };
      case '/auth/verify/':
        // No tokens: verify alone must not open a session.
        return <String, Object?>{'detail': 'Email verificado'};
      case '/auth/password-reset/':
        final String requested =
            (body['email'] as String? ?? '').trim().toLowerCase();
        passwordResetEmails.add(requested);
        return <String, Object?>{
          'detail': 'Si el email existe, recibira un codigo',
        };
      case '/auth/password-reset/confirm/':
        return <String, Object?>{'detail': 'Contrasena actualizada'};
      default:
        return <String, Object?>{'detail': 'ok'};
    }
  }

  @override
  Future<Object?> put(String path, {Object? data}) async {
    if (offline) _throwOffline(path);
    return <String, Object?>{'detail': 'ok'};
  }

  @override
  Future<Object?> patch(String path, {Object? data}) async {
    if (offline) _throwOffline(path);
    return <String, Object?>{'detail': 'ok'};
  }

  @override
  Future<Object?> delete(String path) async {
    if (offline) _throwOffline(path);
    return <String, Object?>{'detail': 'ok'};
  }

  @override
  Future<void> logout(String refresh) async {
    // Mirrors ApiClient.logout: never throw, always clear local tokens.
    logoutRefreshes.add(refresh);
    await tokenStorage.clearTokens();
  }

  // ── Internals ──────────────────────────────────────────────────────────
  Object? _login(String path, Map<String, Object?> body) {
    final String attemptedEmail =
        (body['email'] as String? ?? '').trim().toLowerCase();
    final String attemptedPassword = body['password'] as String? ?? '';
    if (attemptedEmail != email.toLowerCase() ||
        attemptedPassword != password) {
      _throwApi(path, 401, 'invalid_credentials', 'Credenciales invalidas');
    }
    return <String, Object?>{
      'access': accessToken,
      'refresh': refreshToken,
      'user': user.toJson(),
    };
  }

  static Map<String, Object?> _asJsonMap(Object? data) {
    if (data is Map) {
      return data.map(
        (key, value) => MapEntry<String, Object?>(key.toString(), value),
      );
    }
    return <String, Object?>{};
  }

  /// Same shape a live 4xx produces: [DioException] with a JSON body, so
  /// `friendlyErrorMessage` and `AuthState.lastError` behave identically.
  static Never _throwApi(
    String path,
    int status,
    String code,
    String detail,
  ) {
    final RequestOptions options = RequestOptions(path: path);
    throw DioException(
      requestOptions: options,
      type: DioExceptionType.badResponse,
      response: Response<dynamic>(
        requestOptions: options,
        statusCode: status,
        data: <String, Object?>{'code': code, 'detail': detail},
      ),
    );
  }

  static Never _throwOffline(String path) {
    throw DioException(
      requestOptions: RequestOptions(path: path),
      type: DioExceptionType.connectionError,
      error: 'Connection refused',
    );
  }
}
