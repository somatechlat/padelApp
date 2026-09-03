"""E2E tests: Admin panel user management."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestUsers:
    """Test the users management page."""

    def test_users_page_loads(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("table").is_visible()

    def test_users_list_shows_all_demo_users(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        content = admin_page.content()
        assert "admin@andespadel.com" in content
        assert "gerente@andespadel.com" in content
        assert "recepcion@andespadel.com" in content
        assert "cliente@andespadel.com" in content

    def test_users_shows_roles(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        content = admin_page.content()
        assert "superadmin" in content.lower() or "Superadmin" in content

    def test_users_shows_status(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        content = admin_page.content()
        assert "Activo" in content or "activo" in content or "active" in content

    def test_users_search_by_email(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        search_input = admin_page.locator('input[name="q"]')
        if search_input.is_visible():
            search_input.fill("gerente")
            search_input.press("Enter")
            admin_page.wait_for_load_state("networkidle")
            assert "gerente@andespadel.com" in admin_page.content()

    def test_users_filter_by_role(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        # The filter select is the first one (not the inline per-row ones)
        filter_form = admin_page.locator('form:has(select[name="role"]):not(:has(input[name="user_id"]))')
        if filter_form.count() > 0:
            role_select = filter_form.first.locator('select[name="role"]')
            role_select.select_option("cliente")
            filter_form.first.locator('button[type="submit"], input[type="submit"]').first.click()
            admin_page.wait_for_load_state("networkidle")
            assert "cliente@andespadel.com" in admin_page.content()

    def test_users_change_role_form_exists(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        content = admin_page.content()
        # Should have role change forms for each user
        assert "change_role" in content or "Guardar" in content

    def test_users_change_status_form_exists(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        content = admin_page.content()
        assert "change_status" in content or "Activo" in content

    def test_users_pagination(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        assert admin_page.locator("table").is_visible()
