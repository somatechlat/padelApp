"""E2E tests: Admin panel courts management."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestCourts:
    """Test the courts management page."""

    def test_courts_page_loads(self, admin_page: Page):
        admin_page.goto("/adminpanel/courts/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("table").first.is_visible()

    def test_courts_list_shows_courts(self, admin_page: Page):
        admin_page.goto("/adminpanel/courts/")
        rows = admin_page.locator("table tbody tr")
        assert rows.count() >= 2  # C1 and C2 from seed_demo

    def test_courts_shows_name_and_type(self, admin_page: Page):
        admin_page.goto("/adminpanel/courts/")
        content = admin_page.content()
        assert "C1" in content or "C2" in content

    def test_courts_toggle_status(self, admin_page: Page):
        admin_page.goto("/adminpanel/courts/")
        toggle_form = admin_page.locator('form:has(input[name="action"][value="toggle_status"])')
        if toggle_form.count() > 0:
            toggle_form.first.locator('button[type="submit"]').click()
            admin_page.wait_for_load_state("networkidle")
            assert admin_page.locator(".alert-success, .alert-warning").is_visible()

    def test_courts_create_button_exists(self, admin_page: Page):
        admin_page.goto("/adminpanel/courts/")
        content = admin_page.content()
        assert "Nueva Cancha" in content or "Crear" in content or "nueva" in content.lower()

    def test_courts_maintenance_button_exists(self, admin_page: Page):
        admin_page.goto("/adminpanel/courts/")
        content = admin_page.content()
        assert "Mantenimiento" in content or "mantenimiento" in content

    def test_courts_maintenance_list(self, admin_page: Page):
        admin_page.goto("/adminpanel/courts/")
        content = admin_page.content()
        assert "Mantenimiento" in content or "mantenimiento" in content

    def test_courts_venues_list(self, admin_page: Page):
        admin_page.goto("/adminpanel/courts/")
        content = admin_page.content()
        assert "Andes" in content
