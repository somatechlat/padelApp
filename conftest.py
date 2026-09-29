"""Shared pytest fixtures for the Django suite.

Fixtures here are intentionally thin object factories used across several
apps' tests. Per-app fixtures that need different fields (rich club profile,
confirmed bookings on a particular day, cancellation policies, …) stay in
their own test modules and override these by name.
"""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def _isolated_cache():
    """Throttle/lockout counters share the process LocMemCache across tests."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


# --- Domain objects -------------------------------------------------------


@pytest.fixture
def venue():
    from apps.courts.models import Venue

    return Venue.objects.create(name="Andes Padel", timezone="America/Guayaquil", currency="USD")


@pytest.fixture
def court(venue):
    from apps.courts.models import Court

    return Court.objects.create(
        venue=venue, name="Cancha 1", court_type="techada", price_base="12.00"
    )


@pytest.fixture
def scheduled_court(court):
    from apps.courts.models import CourtSchedule

    for wd in range(7):
        CourtSchedule.objects.create(court=court, weekday=wd, open_time="08:00", close_time="22:00")
    return court


@pytest.fixture
def schedule(scheduled_court):
    """Alias used by the scheduling tests; same object as `scheduled_court`."""
    return scheduled_court


# --- Users / auth clients -------------------------------------------------


@pytest.fixture
def user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(email="u@test.com", password="pass12345")


@pytest.fixture
def client_user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(email="c@test.com", password="pass12345")


@pytest.fixture
def client(api_client, client_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(client_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


@pytest.fixture
def staff_user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="staff@test.com", password="pass12345", role="recepcionista"
    )


@pytest.fixture
def staff_client(api_client, staff_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(staff_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client
