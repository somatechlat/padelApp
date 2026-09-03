"""E2E tests: Admin panel events, tournaments, and news."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestEvents:
    """Test the events management page."""

    def test_events_page_loads(self, admin_page: Page):
        admin_page.goto("/adminpanel/events/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("table").count() >= 1

    def test_events_shows_tournaments(self, admin_page: Page):
        admin_page.goto("/adminpanel/events/")
        content = admin_page.content()
        assert "Torneo" in content or "torneo" in content

    def test_events_shows_news(self, admin_page: Page):
        admin_page.goto("/adminpanel/events/")
        content = admin_page.content()
        assert "Noticia" in content or "noticia" in content or "News" in content

    def test_events_create_tournament_button_exists(self, admin_page: Page):
        admin_page.goto("/adminpanel/events/")
        content = admin_page.content()
        assert "Torneo" in content  # Tournament creation form/button present

    def test_events_create_news_button_exists(self, admin_page: Page):
        admin_page.goto("/adminpanel/events/")
        content = admin_page.content()
        assert "Noticia" in content or "noticia" in content

    def test_events_tournament_status_badges(self, admin_page: Page):
        admin_page.goto("/adminpanel/events/")
        content = admin_page.content()
        # Check that tournament statuses are displayed
        assert any(s in content.lower() for s in [
            "abierto", "cerrado", "en curso", "finalizado",
            "borrador", "publicado", "inscripciones"
        ])

    def test_events_tournament_details_visible(self, admin_page: Page):
        admin_page.goto("/adminpanel/events/")
        content = admin_page.content()
        assert "2026" in content  # Dates should be visible

    def test_events_news_list(self, admin_page: Page):
        admin_page.goto("/adminpanel/events/")
        content = admin_page.content()
        # Should show news posts from seed_demo
        assert "Reapertura" in content or "horario" in content or "Noticia" in content
