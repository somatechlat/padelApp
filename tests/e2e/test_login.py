"""E2E tests: Admin panel login flow."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestLogin:
    """Test the admin panel login page."""

    def test_login_page_renders(self, page: Page):
        page.goto("/adminpanel/login/")
        assert page.locator("h1").inner_text() == "Andes Pádel"
        assert page.locator('input[name="email"]').is_visible()
        assert page.locator('input[name="password"]').is_visible()
        assert page.locator('button[type="submit"]').is_visible()

    def test_login_success_admin(self, page: Page):
        page.goto("/adminpanel/login/")
        page.fill('input[name="email"]', "admin@andespadel.com")
        page.fill('input[name="password"]', "Andes12345!")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert "/adminpanel/dashboard/" in page.url or "/adminpanel/" in page.url
        assert page.locator(".alert-success").is_visible()

    def test_login_success_gerente(self, page: Page):
        page.goto("/adminpanel/login/")
        page.fill('input[name="email"]', "gerente@andespadel.com")
        page.fill('input[name="password"]', "Andes12345!")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert "/adminpanel/" in page.url

    def test_login_success_recepcionista(self, page: Page):
        page.goto("/adminpanel/login/")
        page.fill('input[name="email"]', "recepcion@andespadel.com")
        page.fill('input[name="password"]', "Andes12345!")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert "/adminpanel/" in page.url

    def test_login_invalid_password(self, page: Page):
        page.goto("/adminpanel/login/")
        page.fill('input[name="email"]', "admin@andespadel.com")
        page.fill('input[name="password"]', "wrongpassword")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert page.locator(".alert-error").is_visible()
        assert "invalidas" in page.locator(".alert-error").inner_text().lower()

    def test_login_cliente_denied(self, page: Page):
        page.goto("/adminpanel/login/")
        page.fill('input[name="email"]', "cliente@andespadel.com")
        page.fill('input[name="password"]', "Andes12345!")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        assert page.locator(".alert-error").is_visible()
        assert "denegado" in page.locator(".alert-error").inner_text().lower()

    def test_login_empty_fields(self, page: Page):
        page.goto("/adminpanel/login/")
        page.click('button[type="submit"]')
        # HTML5 validation prevents submit -- page stays on login
        assert "/adminpanel/login/" in page.url

    def test_logout(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.click('a:has-text("Salir")')
        admin_page.wait_for_load_state("networkidle")
        assert "/adminpanel/login/" in admin_page.url

    def test_login_redirects_if_already_authenticated(self, admin_page: Page):
        admin_page.goto("/adminpanel/login/")
        admin_page.wait_for_load_state("networkidle")
        assert "/adminpanel/dashboard/" in admin_page.url or "/adminpanel/" in admin_page.url
