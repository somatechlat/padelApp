"""E2E tests: Admin panel navigation and RBAC."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestNavigation:
    """Test sidebar navigation and role-based access."""

    # ── Sidebar links ──

    def test_sidebar_has_all_nav_links(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        nav = admin_page.locator("aside nav")
        links = nav.locator("a")
        link_texts = [links.nth(i).inner_text().strip() for i in range(links.count())]
        assert any("Panel" in t for t in link_texts)
        assert any("Calendario" in t for t in link_texts)
        assert any("Canchas" in t for t in link_texts)
        assert any("Usuarios" in t for t in link_texts)
        assert any("Pagos" in t for t in link_texts)
        assert any("Eventos" in t for t in link_texts)
        assert any("Reportes" in t for t in link_texts)
        assert any("Ajustes" in t for t in link_texts)
        assert any("Auditor" in t for t in link_texts)

    def test_navigate_to_calendar(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.click('aside a:has-text("Calendario")')
        admin_page.wait_for_load_state("networkidle")
        assert "/adminpanel/calendar/" in admin_page.url

    def test_navigate_to_courts(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.click('aside a:has-text("Canchas")')
        admin_page.wait_for_load_state("networkidle")
        assert "/adminpanel/courts/" in admin_page.url

    def test_navigate_to_users(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.click('aside a:has-text("Usuarios")')
        admin_page.wait_for_load_state("networkidle")
        assert "/adminpanel/users/" in admin_page.url

    def test_navigate_to_payments(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.click('aside a:has-text("Pagos")')
        admin_page.wait_for_load_state("networkidle")
        assert "/adminpanel/payments/" in admin_page.url

    def test_navigate_to_events(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.click('aside a:has-text("Eventos")')
        admin_page.wait_for_load_state("networkidle")
        assert "/adminpanel/events/" in admin_page.url

    def test_navigate_to_reports(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.click('aside a:has-text("Reportes")')
        admin_page.wait_for_load_state("networkidle")
        assert "/adminpanel/reports/" in admin_page.url

    def test_navigate_to_settings(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.click('aside a:has-text("Ajustes")')
        admin_page.wait_for_load_state("networkidle")
        assert "/adminpanel/settings/" in admin_page.url

    def test_navigate_to_audit(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.click('aside a:has-text("Auditor")')
        admin_page.wait_for_load_state("networkidle")
        assert "/adminpanel/audit/" in admin_page.url

    # ── Active link highlighting ──

    def test_active_link_highlighted(self, admin_page: Page):
        admin_page.goto("/adminpanel/calendar/")
        active_link = admin_page.locator('aside nav a.active')
        assert active_link.is_visible()
        assert "Calendario" in active_link.inner_text()

    # ── RBAC: cliente cannot access admin panel ──

    def test_cliente_redirected_from_dashboard(self, page: Page):
        page.goto("/adminpanel/login/")
        page.fill('input[name="email"]', "cliente@andespadel.com")
        page.fill('input[name="password"]', "Andes12345!")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        # Should stay on login with error
        assert page.locator(".alert-error").is_visible()

    def test_unauthenticated_redirected_to_login(self, page: Page):
        page.goto("/adminpanel/dashboard/")
        page.wait_for_load_state("networkidle")
        assert "/adminpanel/login/" in page.url

    def test_unauthenticated_redirected_from_calendar(self, page: Page):
        page.goto("/adminpanel/calendar/")
        page.wait_for_load_state("networkidle")
        assert "/adminpanel/login/" in page.url

    def test_unauthenticated_redirected_from_users(self, page: Page):
        page.goto("/adminpanel/users/")
        page.wait_for_load_state("networkidle")
        assert "/adminpanel/login/" in page.url

    # ── RBAC: recepcionista can access but limited ──

    def test_recepcionista_can_access_dashboard(self, recepcion_page: Page):
        recepcion_page.goto("/adminpanel/dashboard/")
        recepcion_page.wait_for_load_state("networkidle")
        assert recepcion_page.locator(".card").count() >= 1

    def test_recepcionista_can_access_calendar(self, recepcion_page: Page):
        recepcion_page.goto("/adminpanel/calendar/")
        recepcion_page.wait_for_load_state("networkidle")
        assert recepcion_page.locator("table").is_visible()

    # ── RBAC: gerente has full access ──

    def test_gerente_can_access_all_pages(self, gerente_page: Page):
        pages = [
            "/adminpanel/dashboard/",
            "/adminpanel/calendar/",
            "/adminpanel/courts/",
            "/adminpanel/users/",
            "/adminpanel/payments/",
            "/adminpanel/events/",
            "/adminpanel/reports/",
            "/adminpanel/settings/",
            "/adminpanel/audit/",
        ]
        for url in pages:
            gerente_page.goto(url)
            gerente_page.wait_for_load_state("networkidle")
            assert gerente_page.locator("table, .card, aside").count() >= 1

    # ── Brand consistency ──

    def test_brand_badge_visible(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        badge = admin_page.locator(".brand-badge")
        assert badge.is_visible()
        assert "PRO" in badge.inner_text()

    def test_brand_title_visible(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        title = admin_page.locator(".brand-title")
        assert title.is_visible()
        assert "andes" in title.inner_text().lower()

    def test_footer_visible(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        footer = admin_page.locator(".sidebar-footer")
        assert footer.is_visible()
        assert "Andes" in footer.inner_text()
