from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

pytestmark = pytest.mark.django_db


def _future_day():
    return timezone.localdate() + timedelta(days=3)


class TestBookingAPI:
    def test_preview_returns_price(self, client, scheduled_court):
        resp = client.post(
            "/api/bookings/preview/",
            {
                "court": scheduled_court.id,
                "date": _future_day().isoformat(),
                "start_time": "10:00",
                "duration_minutes": 60,
            },
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["price"] == "12.00"

    def test_create_booking(self, client, scheduled_court):
        resp = client.post(
            "/api/bookings/",
            {
                "court": scheduled_court.id,
                "date": _future_day().isoformat(),
                "start_time": "10:00",
                "duration_minutes": 60,
                "players": 4,
            },
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["status"] == "pending_payment"

    def test_confirm_booking(self, client, scheduled_court):
        created = client.post(
            "/api/bookings/",
            {
                "court": scheduled_court.id,
                "date": _future_day().isoformat(),
                "start_time": "10:00",
                "duration_minutes": 60,
            },
        ).data
        resp = client.post(f"/api/bookings/{created['id']}/confirm/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "confirmed"

    def test_cancel_booking(self, client, scheduled_court):
        created = client.post(
            "/api/bookings/",
            {
                "court": scheduled_court.id,
                "date": _future_day().isoformat(),
                "start_time": "10:00",
                "duration_minutes": 60,
            },
        ).data
        resp = client.post(f"/api/bookings/{created['id']}/cancel/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "cancelled"

    def test_list_my_bookings(self, client, scheduled_court):
        client.post(
            "/api/bookings/",
            {
                "court": scheduled_court.id,
                "date": _future_day().isoformat(),
                "start_time": "10:00",
                "duration_minutes": 60,
            },
        )
        resp = client.get("/api/bookings/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1

    def test_other_user_cannot_access_booking(self, client, scheduled_court):
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.tokens import RefreshToken

        created = client.post(
            "/api/bookings/",
            {
                "court": scheduled_court.id,
                "date": _future_day().isoformat(),
                "start_time": "10:00",
                "duration_minutes": 60,
            },
        ).data
        other = get_user_model().objects.create_user(email="o@test.com", password="pass12345")
        from rest_framework.test import APIClient

        oc = APIClient()
        oc.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other).access_token}")
        resp = oc.get(f"/api/bookings/{created['id']}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_booking_requires_auth(self, api_client, scheduled_court):
        resp = api_client.post(
            "/api/bookings/",
            {
                "court": scheduled_court.id,
                "date": _future_day().isoformat(),
                "start_time": "10:00",
                "duration_minutes": 60,
            },
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
