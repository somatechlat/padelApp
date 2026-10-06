import pytest
from django.contrib.auth import get_user_model

from apps.gdpr.models import ConsentRecord
from apps.gdpr.services import erase_user, export_user_data, record_consent
from apps.security.models import AuditLog
from apps.users.models import Status as UserStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return get_user_model().objects.create_user(email="me@test.com", password="pass12345")


class TestConsent:
    def test_record_consent_creates_entry_and_stamps_user(self, user):
        record_consent(user, "v1", True, source="mobile")
        assert ConsentRecord.objects.filter(user=user).count() == 1
        user.refresh_from_db()
        assert user.consent_version == "v1"
        assert user.consent_ts is not None


class TestExport:
    def test_export_contains_profile_and_related(self, user):
        data = export_user_data(user)
        assert data["profile"]["email"] == "me@test.com"
        assert "bookings" in data
        assert "payments" in data
        assert "notifications" in data
        assert "consent_records" in data


class TestErase:
    def test_erase_anonymizes_user(self, user):
        erase_user(user)
        user.refresh_from_db()
        assert user.email.startswith("erased-")
        assert user.full_name == "Usuario eliminado"
        assert user.status == UserStatus.DELETED
        assert user.is_active is False
        assert "me@test.com" not in user.email

    def test_erase_scrubs_names_and_birth_date(self, user):
        from datetime import date

        from apps.users.models import SkillLevel

        skill = SkillLevel.objects.create(name="Intermedio", order=1)
        user.first_name = "Ana"
        user.last_name = "Paz"
        user.full_name = "Ana Paz"
        user.birth_date = date(1990, 5, 4)
        user.skill_level = skill
        user.phone = "0991112222"
        user.save()
        erase_user(user)
        user.refresh_from_db()
        assert user.first_name == ""
        assert user.last_name == ""
        assert user.full_name == "Usuario eliminado"
        assert user.birth_date is None
        assert user.skill_level is None
        assert user.phone == ""
        assert user.consent_version is None
        assert user.consent_ts is None

    def test_erase_deletes_avatar_file(self, user, tmp_path, settings):
        from django.core.files.base import ContentFile

        settings.MEDIA_ROOT = tmp_path
        user.avatar.save("me.png", ContentFile(b"fake-image-bytes"), save=True)
        avatar_path = user.avatar.path
        assert avatar_path
        from pathlib import Path

        assert Path(avatar_path).exists()
        erase_user(user)
        user.refresh_from_db()
        assert not user.avatar
        assert not Path(avatar_path).exists()

    def test_erase_logs_audit_event(self, user):
        erase_user(user)
        assert AuditLog.objects.filter(action="gdpr.erase", user=user).exists()


class TestGdprAPI:
    def test_consent_endpoint(self, api_client, user):
        api_client.force_authenticate(user)
        resp = api_client.post(
            "/api/auth/me/consent/",
            {"version": "v1", "granted": True, "source": "mobile"},
            format="json",
        )
        assert resp.status_code == 201

    def test_export_endpoint(self, api_client, user):
        api_client.force_authenticate(user)
        resp = api_client.get("/api/auth/me/export/")
        assert resp.status_code == 200
        assert resp.data["profile"]["email"] == "me@test.com"

    def test_erase_endpoint_requires_auth(self, api_client):
        resp = api_client.post("/api/auth/me/erase/")
        assert resp.status_code == 401

    def test_erase_endpoint(self, api_client, user):
        api_client.force_authenticate(user)
        resp = api_client.post("/api/auth/me/erase/")
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.status == UserStatus.DELETED
