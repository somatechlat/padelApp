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
