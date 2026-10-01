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
