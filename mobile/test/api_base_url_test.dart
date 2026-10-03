import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/core/api_client.dart';

/// The release guard cannot be exercised by shipping, so it is exercised here.
///
/// Every loopback case below produced a real published build at some point: the
/// shipped binary resolved its API to the phone itself and every request was a
/// connection error that only the person holding the phone could see.
void main() {
  group('release builds must name a real host', () {
    const loopback = [
      'http://127.0.0.1:28002/api',
      'http://localhost:28002/api',
      'http://[::1]:28002/api',
      'http://10.0.2.2:28002/api',
    ];

    for (final url in loopback) {
      test('refuses $url', () {
        expect(
          () => baseUrlFor(url, isRelease: true),
          throwsStateError,
          reason: '$url resolves to the device, not to an API',
        );
      });
    }

    test('refuses an unset value', () {
      expect(() => baseUrlFor('', isRelease: true), throwsStateError);
    });

    test('refuses a value that is not a URL at all', () {
      expect(() => baseUrlFor('not a url', isRelease: true), throwsStateError);
    });

    test('accepts the production API', () {
      expect(
        baseUrlFor('https://app.andespadelclub.com/api', isRelease: true),
        'https://app.andespadelclub.com/api',
      );
    });

    test('accepts any other real host, so staging still works', () {
      expect(
        baseUrlFor('https://staging.example.com/api', isRelease: true),
        'https://staging.example.com/api',
      );
    });
  });

  group('debug builds keep the dev stack', () {
    test('falls back to the dev compose cluster', () {
      expect(baseUrlFor('', isRelease: false), 'http://127.0.0.1:28002/api');
    });

    test('honours an explicit override', () {
      expect(
        baseUrlFor('http://127.0.0.1:29002/api', isRelease: false),
        'http://127.0.0.1:29002/api',
      );
    });

    test('loopback is allowed in debug, which is the whole point', () {
      expect(
        baseUrlFor('http://127.0.0.1:28002/api', isRelease: false),
        'http://127.0.0.1:28002/api',
      );
    });
  });
}
