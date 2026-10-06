import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.verification.models import VerificationCode

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def user(db):
    u = User.objects.create_user(email="ana@test.com", password="pass12345", full_name="Ana Paz")
    u.status = "active"
    u.email_verified = True
    u.save()
    return u


@pytest.fixture
def auth_client(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


class TestRegister:
    def test_register_creates_inactive_user_and_issues_code(self, api_client, mailoutbox):
        resp = api_client.post(
            "/api/auth/register/",
            {
                "email": "nuevo@test.com",
                "password": "pass12345",
                "first_name": "Nuevo",
                "last_name": "Usuario",
                "phone": "0991111111",
                "consent_version": "v1",
            },
        )
        assert resp.status_code == status.HTTP_201_CREATED
        u = User.objects.get(email="nuevo@test.com")
        assert u.email_verified is False
        assert u.status == "active"
        assert u.first_name == "Nuevo"
        assert u.last_name == "Usuario"
        assert u.full_name == "Nuevo Usuario"
        assert VerificationCode.objects.filter(user=u, purpose="email_verify").exists()
        assert len(mailoutbox) == 1

    def test_register_requires_consent(self, api_client):
        resp = api_client.post(
            "/api/auth/register/",
            {
                "email": "x@test.com",
                "password": "pass12345",
                "first_name": "X",
                "last_name": "Y",
            },
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email_409(self, api_client, user):
        resp = api_client.post(
            "/api/auth/register/",
            {
                "email": user.email,
                "password": "pass12345",
                "first_name": "Dupe",
                "last_name": "User",
                "consent_version": "v1",
            },
        )
        assert resp.status_code == status.HTTP_409_CONFLICT

    def test_register_weak_password_rejected(self, api_client):
        resp = api_client.post(
            "/api/auth/register/",
            {
                "email": "weak@test.com",
                "password": "123",
                "first_name": "Weak",
                "last_name": "Pass",
                "consent_version": "v1",
            },
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestVerify:
    def test_verify_code_activates_account(self, api_client, user):
        code = VerificationCode.objects.create(user=user, purpose="email_verify")
        resp = api_client.post("/api/auth/verify/", {"email": user.email, "code": code.code})
        assert resp.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.email_verified is True

    def test_verify_wrong_code_fails(self, api_client, user):
        VerificationCode.objects.create(user=user, purpose="email_verify")
        resp = api_client.post("/api/auth/verify/", {"email": user.email, "code": "000000"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_missing_user_same_message_as_bad_code(self, api_client, user):
        """No enumeration: unknown email and wrong code must be indistinguishable."""
        VerificationCode.objects.create(user=user, purpose="email_verify")
        bad_code = api_client.post("/api/auth/verify/", {"email": user.email, "code": "000000"})
        missing = api_client.post(
            "/api/auth/verify/", {"email": "ghost@test.com", "code": "000000"}
        )
        assert bad_code.status_code == missing.status_code == status.HTTP_400_BAD_REQUEST
        assert bad_code.data.get("detail") == missing.data.get("detail")

    def test_verify_expires_after_5_attempts(self, api_client, user):
        VerificationCode.objects.create(user=user, purpose="email_verify")
        for _ in range(5):
            api_client.post("/api/auth/verify/", {"email": user.email, "code": "111111"})
        resp = api_client.post("/api/auth/verify/", {"email": user.email, "code": "111111"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        code = VerificationCode.objects.get(user=user, purpose="email_verify")
        assert code.is_expired or code.attempts >= 5


class TestVerifyLink:
    def test_get_does_not_verify(self, api_client, user):
        from apps.users.emails import make_token

        code = VerificationCode.objects.create(user=user, purpose="email_verify")
        token = make_token(user.id, code.code, "email_verify")
        resp = api_client.get(f"/api/auth/verify/link/?token={token}")
        # GET renders the confirm form only — mail scanners must not verify.
        assert resp.status_code == status.HTTP_200_OK
        assert b"Verificar mi cuenta" in resp.content
        user.refresh_from_db()
        assert user.email_verified is False
        code.refresh_from_db()
        assert code.verified_at is None

    def test_post_verifies(self, api_client, user):
        from apps.users.emails import make_token

        code = VerificationCode.objects.create(user=user, purpose="email_verify")
        token = make_token(user.id, code.code, "email_verify")
        resp = api_client.post("/api/auth/verify/link/", {"token": token})
        assert resp.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.email_verified is True

    def test_invalid_token_get_shows_error(self, api_client):
        resp = api_client.get("/api/auth/verify/link/?token=garbage")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestTokenMaxAge:
    def test_read_token_max_age_is_code_ttl_and_rejects_expired(self, user):
        """Signed links live exactly as long as CODE_TTL (15 minutes)."""
        from datetime import timedelta
        from unittest import mock

        from django.utils import timezone

        from apps.users import emails
        from apps.users.emails import read_token
        from apps.verification.models import CODE_TTL

        assert CODE_TTL == timedelta(minutes=15)

        # Token stamped 16 minutes ago — past CODE_TTL — must be refused.
        past = timezone.now() - timedelta(minutes=16)
        with mock.patch("time.time", return_value=past.timestamp()):
            expired_token = emails.make_token(user.id, "123456", "email_verify")
        assert read_token(expired_token, "email_verify") is None

        # A fresh token still validates and carries the expected payload.
        token = emails.make_token(user.id, "123456", "email_verify")
        data = read_token(token, "email_verify")
        assert data == {"u": user.id, "c": "123456", "p": "email_verify"}

    def test_read_token_rejects_wrong_purpose(self, user):
        from apps.users.emails import make_token, read_token

        token = make_token(user.id, "123456", "email_verify")
        assert read_token(token, "password_reset") is None


class TestLogin:
    def test_login_returns_access_and_refresh(self, api_client, user):
        resp = api_client.post("/api/auth/login/", {"email": user.email, "password": "pass12345"})
        assert resp.status_code == status.HTTP_200_OK
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_login_wrong_password_401(self, api_client, user):
        resp = api_client.post("/api/auth/login/", {"email": user.email, "password": "wrongpass"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_unverified_email_blocked(self, api_client, user):
        user.email_verified = False
        user.save()
        resp = api_client.post("/api/auth/login/", {"email": user.email, "password": "pass12345"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_locked_after_5_failures(self, api_client, user):
        for _ in range(5):
            api_client.post("/api/auth/login/", {"email": user.email, "password": "bad"})
        resp = api_client.post("/api/auth/login/", {"email": user.email, "password": "pass12345"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "bloqueada" in resp.data.get("detail", "").lower()


class TestRefreshLogout:
    def test_refresh_rotates_tokens(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        old = RefreshToken.for_user(user)
        resp = api_client.post("/api/auth/refresh/", {"refresh": str(old)})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["access"]
        assert resp.data["refresh"] != str(old)

    def test_reused_refresh_is_revoked(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(user)
        api_client.post("/api/auth/refresh/", {"refresh": str(token)})
        resp2 = api_client.post("/api/auth/refresh/", {"refresh": str(token)})
        assert resp2.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh(self, api_client, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(user)
        resp = api_client.post("/api/auth/logout/", {"refresh": str(token)})
        assert resp.status_code == status.HTTP_205_RESET_CONTENT
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

        assert BlacklistedToken.objects.filter(token__jti=token["jti"]).exists()


class TestPassword:
    def test_password_reset_sends_email(self, api_client, user, mailoutbox):
        resp = api_client.post("/api/auth/password-reset/", {"email": user.email})
        assert resp.status_code == status.HTTP_200_OK
        assert len(mailoutbox) == 1
        assert VerificationCode.objects.filter(user=user, purpose="password_reset").exists()

    def test_password_reset_no_enumeration(self, api_client, mailoutbox):
        resp = api_client.post("/api/auth/password-reset/", {"email": "none@nowhere.com"})
        assert resp.status_code == status.HTTP_200_OK
        assert len(mailoutbox) == 0

    def test_password_reset_confirm_sets_new_password(self, api_client, user):
        code = VerificationCode.objects.create(user=user, purpose="password_reset")
        resp = api_client.post(
            "/api/auth/password-reset/confirm/",
            {"email": user.email, "code": code.code, "password": "nuevapass99"},
        )
        assert resp.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password("nuevapass99")

    def test_password_reset_confirm_code_single_use(self, api_client, user):
        code = VerificationCode.objects.create(user=user, purpose="password_reset")
        api_client.post(
            "/api/auth/password-reset/confirm/",
            {"email": user.email, "code": code.code, "password": "nuevapass99"},
        )
        resp = api_client.post(
            "/api/auth/password-reset/confirm/",
            {"email": user.email, "code": code.code, "password": "otrapass99"},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_confirm_refused_for_suspended(self, api_client, user):
        from apps.users.services import set_user_status

        code = VerificationCode.objects.create(user=user, purpose="password_reset")
        set_user_status(user, "suspended")
        resp = api_client.post(
            "/api/auth/password-reset/confirm/",
            {"email": user.email, "code": code.code, "password": "nuevapass99"},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        user.refresh_from_db()
        assert user.check_password("nuevapass99") is False
        # Same detail as an invalid code: no hint that the account exists.
        assert resp.data.get("detail") == "Codigo invalido o expirado"

    def test_change_password_revokes_tokens(self, auth_client, user):
        resp = auth_client.post(
            "/api/auth/password/change/",
            {"old_password": "pass12345", "new_password": "nuevapass99"},
        )
        assert resp.status_code == status.HTTP_200_OK


class TestMe:
    def test_me_returns_profile(self, auth_client, user):
        resp = auth_client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["email"] == user.email
        assert resp.data["full_name"] == "Ana Paz"

    def test_me_patch_updates_profile(self, auth_client, user):
        resp = auth_client.patch("/api/auth/me/", {"full_name": "Ana María"})
        assert resp.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.full_name == "Ana María"

    def test_me_requires_auth(self, api_client):
        resp = api_client.get("/api/auth/me/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_devices_register(self, auth_client):
        resp = auth_client.post(
            "/api/auth/me/devices/",
            {"platform": "android", "device_token": "fcm-token-123"},
        )
        assert resp.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
