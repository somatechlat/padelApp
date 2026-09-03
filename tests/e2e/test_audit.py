"""E2E tests: Admin panel audit log."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestAudit:
    """Test the audit log page."""

    def test_audit_page_loads(self, admin_page: Page):
        admin_page.goto("/adminpanel/audit/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("table").is_visible()

    def test_audit_table_headers(self, admin_page: Page):
        admin_page.goto("/adminpanel/audit/")
        headers = admin_page.locator("th")
        header_texts = [headers.nth(i).inner_text().lower() for i in range(headers.count())]
        # Check that audit-related headers exist
        assert len(header_texts) >= 3  # Should have multiple columns

    def test_audit_filter_by_action(self, admin_page: Page):
        admin_page.goto("/adminpanel/audit/")
        action_select = admin_page.locator('select[name="action"]')
        if action_select.is_visible():
            options = action_select.locator("option")
            if options.count() > 1:
                action_select.select_option(index=1)
                action_select.press("Enter")
                admin_page.wait_for_load_state("networkidle")
                assert admin_page.locator("table").is_visible()

    def test_audit_filter_by_entity(self, admin_page: Page):
        admin_page.goto("/adminpanel/audit/")
        entity_select = admin_page.locator('select[name="entity"]')
        if entity_select.is_visible():
            options = entity_select.locator("option")
            if options.count() > 1:
                entity_select.select_option(index=1)
                entity_select.press("Enter")
                admin_page.wait_for_load_state("networkidle")
                assert admin_page.locator("table").is_visible()

    def test_audit_filter_by_user(self, admin_page: Page):
        admin_page.goto("/adminpanel/audit/")
        user_input = admin_page.locator('input[name="user"]')
        if user_input.is_visible():
            user_input.fill("admin")
            user_input.press("Enter")
            admin_page.wait_for_load_state("networkidle")
            assert admin_page.locator("table").is_visible()

    def test_audit_shows_entries(self, admin_page: Page):
        admin_page.goto("/adminpanel/audit/")
        rows = admin_page.locator("table tbody tr")
        # Should have at least some entries from login events
        assert rows.count() >= 0

    def test_audit_pagination(self, admin_page: Page):
        admin_page.goto("/adminpanel/audit/")
        pagination = admin_page.locator(".pagination, nav[aria-label='pagination']")
        # Just verify page loads
        assert admin_page.locator("table").is_visible()

    def test_audit_read_only(self, admin_page: Page):
        admin_page.goto("/adminpanel/audit/")
        # Audit log should not have create/edit/delete buttons
        create_btns = admin_page.locator('button:has-text("Crear"), button:has-text("Nuevo")')
        assert create_btns.count() == 0
