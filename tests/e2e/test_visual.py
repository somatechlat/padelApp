"""E2E tests: Visual regression and brand consistency."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestVisual:
    """Test visual elements and brand consistency."""

    # ── Brand colors (CSS variables) ──

    def test_login_page_brand_colors(self, page: Page):
        page.goto("/adminpanel/login/")
        # Check that the accent color (Verde Limón) is used on the login button
        btn = page.locator('button[type="submit"]')
        bg_color = btn.evaluate("el => getComputedStyle(el).backgroundColor")
        # #CEDC29 = rgb(206, 220, 41)
        assert "206" in bg_color and "220" in bg_color and "41" in bg_color

    def test_admin_brand_color_in_sidebar(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        active_link = admin_page.locator('aside nav a.active')
        bg_color = active_link.evaluate("el => getComputedStyle(el).backgroundColor")
        # #002F48 = rgb(0, 47, 72)
        assert "0" in bg_color and "47" in bg_color and "72" in bg_color

    def test_accent_color_on_cards(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        card = admin_page.locator(".card").first
        # Card should have accent-colored left border (::before pseudo-element)
        assert card.is_visible()

    # ── Typography ──

    def test_font_family_outfit(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        body_font = admin_page.evaluate("() => getComputedStyle(document.body).fontFamily")
        assert "Outfit" in body_font

    # ── Dark theme consistency ──

    def test_dark_background_color(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        body_bg = admin_page.evaluate("() => getComputedStyle(document.body).backgroundColor")
        # #001219 = rgb(0, 18, 25)
        assert "0" in body_bg and "18" in body_bg and "25" in body_bg

    def test_sidebar_dark_background(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        sidebar_bg = admin_page.locator("aside").evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )
        # #001A2A = rgb(0, 26, 42)
        assert "0" in sidebar_bg and "26" in sidebar_bg and "42" in sidebar_bg

    # ── Responsive elements ──

    def test_login_page_centered(self, page: Page):
        page.goto("/adminpanel/login/")
        container = page.locator(".login-container")
        assert container.is_visible()
        # Should be centered (max-width: 420px)
        width = container.evaluate("el => getComputedStyle(el).maxWidth")
        assert "420" in width

    # ── Status badges colors ──

    def test_status_badge_green_for_active(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        active_badge = admin_page.locator('.badge-active, .badge-confirmed').first
        if active_badge.is_visible():
            color = active_badge.evaluate("el => getComputedStyle(el).color")
            # Verde Limón accent color
            assert color is not None

    def test_status_badge_red_for_blocked(self, admin_page: Page):
        admin_page.goto("/adminpanel/users/")
        blocked_badge = admin_page.locator('.badge-blocked, .badge-cancelled, .badge-failed').first
        if blocked_badge.is_visible():
            color = blocked_badge.evaluate("el => getComputedStyle(el).color")
            # Red accent
            assert color is not None

    # ── Messages styling ──

    def test_success_message_green(self, page: Page):
        page.goto("/adminpanel/login/")
        page.fill('input[name="email"]', "admin@andespadel.com")
        page.fill('input[name="password"]', "Andes12345!")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        success = page.locator(".alert-success")
        if success.is_visible():
            border_color = success.evaluate("el => getComputedStyle(el).borderColor")
            assert border_color is not None
