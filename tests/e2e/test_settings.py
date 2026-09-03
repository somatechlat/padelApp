"""E2E tests: Admin panel settings."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestSettings:
    """Test the settings page."""

    def test_settings_page_loads(self, admin_page: Page):
        admin_page.goto("/adminpanel/settings/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("table, .card, .section-title").count() >= 1

    def test_settings_shows_cancellation_policies(self, admin_page: Page):
        admin_page.goto("/adminpanel/settings/")
        content = admin_page.content()
        assert "cancelaci" in content.lower() or "política" in content.lower() or "policy" in content.lower()

    def test_settings_shows_price_rules(self, admin_page: Page):
        admin_page.goto("/adminpanel/settings/")
        content = admin_page.content()
        assert "precio" in content.lower() or "price" in content.lower() or "tarifa" in content.lower()

    def test_settings_read_only(self, admin_page: Page):
        admin_page.goto("/adminpanel/settings/")
        # Settings page should not have form submissions (read-only)
        forms = admin_page.locator('form:has(button[type="submit"])')
        # Should have 0 or very few submit buttons
        assert forms.count() <= 1

    def test_settings_gerente_access(self, gerente_page: Page):
        gerente_page.goto("/adminpanel/settings/")
        gerente_page.wait_for_load_state("networkidle")
        assert gerente_page.locator("table, .card").count() >= 1
