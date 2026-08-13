import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        email="sec@test.com", password="pass12345", email_verified=True
    )


class TestRateLimit:
    def test_login_rate_limited_429(self, api_client, user):
        from django.core.cache import cache

        cache.clear()
        try:
            for _ in range(10):
                resp = api_client.post(
                    "/api/auth/login/",
                    {"email": user.email, "password": "wrong"},
                )
                assert resp.status_code == 401
            resp = api_client.post(
                "/api/auth/login/", {"email": user.email, "password": "wrong"}
            )
            assert resp.status_code == 429
        finally:
            cache.clear()


class TestTokenRevocation:
    def test_logout_blacklists_refresh(self, api_client, user):
        resp = api_client.post(
            "/api/auth/login/", {"email": user.email, "password": "pass12345"}
        )
        assert resp.status_code == 200
        refresh = resp.data["refresh"]
        api_client.post("/api/auth/logout/", {"refresh": refresh}, format="json")
        resp = api_client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        assert resp.status_code == 401


class TestSecretBootCheck:
    def test_missing_secret_raises(self):
        from padel.settings._checks import validate_production_secrets

        with pytest.raises(RuntimeError):
            validate_production_secrets({"SECRET_KEY": "x"})

    def test_dev_secret_rejected(self):
        from padel.settings._checks import validate_production_secrets

        with pytest.raises(RuntimeError):
            validate_production_secrets({"SECRET_KEY": "dev-only-x"})

    def test_valid_secrets_pass(self):
        from padel.settings._checks import validate_production_secrets

        values = {
            "SECRET_KEY": "prod-key",
            "DB_NAME": "db",
            "DB_USER": "u",
            "DB_PASSWORD": "p",
            "DB_HOST": "h",
            "REDIS_URL": "redis://x",
            "EMAIL_HOST": "smtp",
            "EMAIL_HOST_USER": "u",
            "EMAIL_HOST_PASSWORD": "p",
        }
        validate_production_secrets(values)


class TestAuditTrail:
    def test_login_and_failure_logged(self, api_client, user):
        from apps.security.models import AuditLog

        api_client.post("/api/auth/login/", {"email": user.email, "password": "wrong"})
        assert AuditLog.objects.filter(action="auth.login_failed").exists()

    def test_booking_hold_logged(self, api_client, user):
        from django.utils import timezone

        from apps.courts.models import Court, CourtSchedule, Venue
        from apps.security.models import AuditLog

        venue = Venue.objects.create(name="V")
        court = Court.objects.create(venue=venue, name="C1", price_base="10.00")
        day = timezone.localdate() + timezone.timedelta(days=1)
        wd = day.weekday()
        CourtSchedule.objects.create(
            court=court, weekday=wd, open_time="08:00", close_time="22:00"
        )
        api_client.force_authenticate(user)
        resp = api_client.post(
            "/api/bookings/",
            {"court": court.id, "date": day.isoformat(), "start_time": "10:00",
             "duration_minutes": 60},
            format="json",
        )
        assert resp.status_code == 201
        assert AuditLog.objects.filter(action="booking.hold").exists()
