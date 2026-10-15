"""Host-derivation tests for the production allowlist.

The apps and the staff panel are served from ``app.<apex>`` while the apex and
``www`` are a different machine. If the allowlist only ever derived
``apex`` + ``www.apex``, every request the real origin makes would be
rejected as a bad Host header.

These exercise ``derive_prod_hosts`` directly rather than importing
``padel.settings.prod``: that module refuses to import without real production
secrets, which is intentional fail-closed behaviour and must not be relaxed
for a unit test.
"""

from django.conf import settings
from django.test import SimpleTestCase


class ValidateProductionHostTests(SimpleTestCase):
    def test_keeps_apex_bare(self):
        from padel.settings import _checks

        self.assertEqual(
            _checks.validate_production_host("andespadelclub.com"),
            "andespadelclub.com",
        )

    def test_strips_scheme_www_port_and_path(self):
        from padel.settings import _checks

        self.assertEqual(
            _checks.validate_production_host("https://www.andespadelclub.com:443/api/"),
            "andespadelclub.com",
        )

    def test_keeps_app_subdomain(self):
        from padel.settings import _checks

        # `app.` is the live app-facing name and must not be stripped — only
        # `www.` is a prefix we derive ourselves.
        self.assertEqual(
            _checks.validate_production_host("app.andespadelclub.com"),
            "app.andespadelclub.com",
        )

    def test_rejects_blank(self):
        from padel.settings import _checks

        with self.assertRaises(RuntimeError):
            _checks.validate_production_host("")
        with self.assertRaises(RuntimeError):
            _checks.validate_production_host("   ")

    def test_rejects_host_without_dot(self):
        from padel.settings import _checks

        with self.assertRaises(RuntimeError):
            _checks.validate_production_host("localhost")


class DeriveProdHostsTests(SimpleTestCase):
    def test_allowlist_is_apex_www_and_app(self):
        from padel.settings import _checks

        self.assertEqual(
            _checks.derive_prod_hosts("andespadelclub.com"),
            [
                "andespadelclub.com",
                "www.andespadelclub.com",
                "app.andespadelclub.com",
            ],
        )

    def test_allowlist_covers_app_subdomain(self):
        from padel.settings import _checks

        self.assertIn("app.andespadelclub.com", _checks.derive_prod_hosts("andespadelclub.com"))

    def test_accepts_a_pasted_url(self):
        from padel.settings import _checks

        self.assertEqual(
            _checks.derive_prod_hosts("https://www.andespadelclub.com/"),
            [
                "andespadelclub.com",
                "www.andespadelclub.com",
                "app.andespadelclub.com",
            ],
        )

    def test_never_produces_www_www(self):
        from padel.settings import _checks

        hosts = _checks.derive_prod_hosts("https://www.andespadelclub.com")
        self.assertNotIn("www.www.andespadelclub.com", hosts)

    def test_origins_shape_is_https_and_matches_hosts(self):
        from padel.settings import _checks

        hosts = _checks.derive_prod_hosts("andespadelclub.com")
        origins = [f"https://{host}" for host in hosts]
        self.assertIn("https://app.andespadelclub.com", origins)
        for origin in origins:
            self.assertTrue(origin.startswith("https://"), f"{origin} must be https")


class RunningStackConsistencyTests(SimpleTestCase):
    """The settings this container actually runs must agree with themselves.

    ``prod.py`` once rebound ``DB_NAME`` after ``base.py`` had already built
    the ``DATABASES`` dict out of it, so production booted and crash-looped
    asking Postgres for a database named ``padel`` while the volume held
    ``padel_prod`` — the same star-import trap as the ``SITE_BASE_URL``
    derivation in ``apps/users/emails.py``.

    This checks the live settings module, not a simulation of it: whatever
    module the container is running, the dict must match the scalars it was
    supposed to be built from. Fabricating secrets to import ``prod`` in a
    test would only prove the fabrication works; this catches the real bug in
    whichever environment actually runs.
    """

    def test_database_dict_matches_the_topology_scalars(self):
        # Django's setup_databases patches this very dict in place with the
        # test database's name (test_<name>), so the name check accepts both
        # forms — anything else means the dict and the scalar it was built
        # from have drifted, which is the production outage this guards.
        name = settings.DATABASES["default"]["NAME"]
        self.assertIn(name, {settings.DB_NAME, f"test_{settings.DB_NAME}"})
        self.assertEqual(settings.DATABASES["default"]["USER"], settings.DB_USER)
        self.assertEqual(settings.DATABASES["default"]["HOST"], settings.DB_HOST)
        self.assertEqual(str(settings.DATABASES["default"]["PORT"]), str(settings.DB_PORT))

    def test_database_is_the_real_postgres_not_a_substitute(self):
        self.assertIn("postgresql", settings.DATABASES["default"]["ENGINE"])

    def test_firebase_path_points_at_the_mounted_secret(self):
        # docker-compose.yml mounts this secret with target
        # firebase-service-account.json; rename either side alone and the
        # first push notification dies on FileNotFoundError.
        self.assertTrue(
            settings.FIREBASE_CREDENTIALS_PATH.startswith("/run/secrets/"),
            settings.FIREBASE_CREDENTIALS_PATH,
        )
