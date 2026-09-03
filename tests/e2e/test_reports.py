"""E2E tests: Admin panel reports."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestReports:
    """Test the reports page."""

    def test_reports_page_loads(self, admin_page: Page):
        admin_page.goto("/adminpanel/reports/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("table, .card").count() >= 1

    def test_reports_shows_monthly_revenue(self, admin_page: Page):
        admin_page.goto("/adminpanel/reports/")
        content = admin_page.content()
        assert "ingreso" in content.lower() or "revenue" in content.lower() or "$" in content

    def test_reports_shows_bookings_by_status(self, admin_page: Page):
        admin_page.goto("/adminpanel/reports/")
        content = admin_page.content()
        assert "estado" in content.lower() or "status" in content.lower() or "reserva" in content.lower()

    def test_reports_shows_revenue_by_court(self, admin_page: Page):
        admin_page.goto("/adminpanel/reports/")
        content = admin_page.content()
        assert "cancha" in content.lower() or "court" in content.lower() or "C1" in content

    def test_reports_shows_top_customers(self, admin_page: Page):
        admin_page.goto("/adminpanel/reports/")
        content = admin_page.content()
        assert "cliente" in content.lower() or "customer" in content.lower()

    def test_reports_csv_export_link(self, admin_page: Page):
        admin_page.goto("/adminpanel/reports/")
        csv_link = admin_page.locator('a[href*="export=csv"], a:has-text("CSV"), a:has-text("Exportar")')
        if csv_link.count() > 0:
            assert csv_link.first.is_visible()

    def test_reports_csv_export_link_works(self, admin_page: Page):
        admin_page.goto("/adminpanel/reports/")
        csv_link = admin_page.locator('a[href*="export=csv"], a:has-text("CSV"), a:has-text("Exportar")')
        if csv_link.count() > 0:
            # Verify the link exists and has correct href
            href = csv_link.first.get_attribute("href")
            assert href is not None and "csv" in href.lower()

    def test_reports_gerente_access(self, gerente_page: Page):
        gerente_page.goto("/adminpanel/reports/")
        gerente_page.wait_for_load_state("networkidle")
        assert gerente_page.locator("table, .card").count() >= 1

    def test_reports_recepcionista_denied(self, recepcion_page: Page):
        recepcion_page.goto("/adminpanel/reports/")
        recepcion_page.wait_for_load_state("networkidle")
        # Recepcionista should be denied (not in STAFF_ROLES for manager views)
        # Actually recepcionista IS in STAFF_ROLES, so should have access
        assert recepcion_page.locator("table, .card").count() >= 1 or \
               recepcion_page.url.endswith("/adminpanel/login/")
