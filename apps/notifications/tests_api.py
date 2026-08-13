import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(email="c@test.com", password="pass12345")


@pytest.fixture
def client(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


class TestNotificationAPI:
    def test_list_my_notifications(self, client, user):
        from apps.notifications.services import NotificationService

        NotificationService.notify(user, "booking_confirmed", "Titulo", "Cuerpo")
        resp = client.get("/api/notifications/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1
        assert resp.data["results"][0]["title"] == "Titulo"

    def test_mark_read(self, client, user):
        from apps.notifications.models import Notification
        from apps.notifications.services import NotificationService

        NotificationService.notify(user, "booking_confirmed", "T", "B")
        n = Notification.objects.get(user=user)
        resp = client.post(f"/api/notifications/{n.id}/read/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["read_at"] is not None

    def test_update_preferences(self, client, user):
        resp = client.put(
            "/api/notifications/preferences/",
            [{"event_type": "marketing", "channel": "push", "enabled": False}],
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        from apps.notifications.models import NotificationPreference

        pref = NotificationPreference.objects.get(user=user, event_type="marketing", channel="push")
        assert pref.enabled is False

    def test_requires_auth(self, api_client):
        resp = api_client.get("/api/notifications/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
