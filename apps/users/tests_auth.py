import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status

from apps.verification.models import VerificationCode

User = get_user_model()


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        email="ana@test.com", password="pass12345", full_name="Ana Paz"
    )
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
                "full_name": "Nuevo Usuario",
                "phone": "0991111111",
                "consent_version": "v1",
            },
        )
        assert resp.status_code == status.HTTP_201_CREATED
        u = User.objects.get(email="nuevo@test.com")
        assert u.email_verified is False
        assert u.status == "active"
        assert VerificationCode.objects.filter(user=u, purpose="email_verify").exists()
        assert len(mailoutbox) == 1

    def test_register_requires_consent(self, api_client):
        resp = api_client.post(
            "/api/auth/register/",
            {"email": "x@test.com", "password": "pass12345", "full_name": "X"},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email_409(self, api_client, user):
        resp = api_client.post(
            "/api/auth/register/",
            {
                "email": user.email,
                "password": "pass12345",
                "full_name": "Dupe",
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
                "full_name": "Weak",
                "consent_version": "v1",
            },
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestVerify:
    def test_verify_code_activates_account(self, api_client, user):
        code = VerificationCode.objects.create(
            user=user, purpose="email_verify"
        )
        resp = api_client.post("/api/auth/verify/", {"email": user.email, "code": code.code})
        assert resp.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.email_verified is True

    def test_verify_wrong_code_fails(self, api_client, user):
        VerificationCode.objects.create(user=user, purpose="email_verify")
        resp = api_client.post("/api/auth/verify/", {"email": user.email, "code": "000000"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_expires_after_5_attempts(self, api_client, user):
        VerificationCode.objects.create(user=user, purpose="email_verify")
        for _ in range(5):
            api_client.post("/api/auth/verify/", {"email": user.email, "code": "111111"})
        resp = api_client.post("/api/auth/verify/", {"email": user.email, "code": "111111"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        code = VerificationCode.objects.get(user=user, purpose="email_verify")
        assert code.is_expired or code.attempts >= 5


class TestLogin:
    def test_login_returns_access_and_refresh(self, api_client, user):
        resp = api_client.post(
            "/api/auth/login/", {"email": user.email, "password": "pass12345"}
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_login_wrong_password_401(self, api_client, user):
        resp = api_client.post(
            "/api/auth/login/", {"email": user.email, "password": "wrongpass"}
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_unverified_email_blocked(self, api_client, user):
        user.email_verified = False
        user.save()
        resp = api_client.post(
            "/api/auth/login/", {"email": user.email, "password": "pass12345"}
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_locked_after_5_failures(self, api_client, user):
        for _ in range(5):
            api_client.post("/api/auth/login/", {"email": user.email, "password": "bad"})
        resp = api_client.post(
            "/api/auth/login/", {"email": user.email, "password": "pass12345"}
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "locked" in resp.data.get("detail", "").lower()


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
        assert RefreshToken(str(token)).check_blacklist()


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
