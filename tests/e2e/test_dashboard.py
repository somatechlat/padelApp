"""E2E tests: Admin panel dashboard."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestDashboard:
    """Test the admin dashboard page."""

    def test_dashboard_loads(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator(".card").count() >= 4

    def test_dashboard_shows_kpi_cards(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        cards = admin_page.locator(".card-label")
        labels = [cards.nth(i).inner_text() for i in range(cards.count())]
        assert any("reserva" in l.lower() for l in labels)
        assert any("ocupaci" in l.lower() for l in labels)
        assert any("ingreso" in l.lower() for l in labels)

    def test_dashboard_shows_bookings_table(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        table = admin_page.locator("table")
        assert table.is_visible()

    def test_dashboard_shows_alerts(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        # Alerts section should exist (even if empty)
        assert admin_page.locator("text=Alertas").is_visible() or \
               admin_page.locator("text=alertas").is_visible() or \
               admin_page.locator("text=Mantenimiento").is_visible()

    def test_dashboard_shows_recent_payments(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        assert admin_page.locator("text=Pagos recientes").is_visible() or \
               admin_page.locator("text=pagos").is_visible()

    def test_dashboard_sidebar_visible(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        assert admin_page.locator("aside").is_visible()
        assert admin_page.locator("text=Andes Pádel").first.is_visible()

    def test_dashboard_header_shows_role(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        role_pill = admin_page.locator(".role-pill")
        assert role_pill.is_visible()
        role_text = role_pill.inner_text().lower()
        assert role_text in ("superadmin", "gerente", "recepcionista", "dueño", "dueno")

    def test_dashboard_header_shows_email(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        header = admin_page.locator("header")
        assert "admin@andespadel.com" in header.inner_text()
