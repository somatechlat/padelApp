"""E2E tests: Admin panel settings (club info, bank, i18n titles, policies)."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


def _named(page: Page, name: str):
    return page.locator(
        f'input[name="{name}"], textarea[name="{name}"], select[name="{name}"]'
    )


def _require(page: Page, *names: str):
    missing = [n for n in names if _named(page, n).count() == 0]
    assert not missing, f"Missing form fields: {missing}"


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
        """Settings is editable: club contact form fields must exist as inputs.

        Replaces the old read-only assertion (forms.count() <= 1).
        """
        admin_page.goto("/adminpanel/settings/")
        admin_page.wait_for_load_state("networkidle")
        address = _named(admin_page, "address")
        assert address.count() > 0, "Club address field missing on settings"
        assert address.first.is_visible()
        forms = admin_page.locator('form:has(button[type="submit"])')
        assert forms.count() >= 1

    def test_settings_club_contact_fields(self, admin_page: Page):
        """Club contact form fields (names match settings.html update_club form)."""
        admin_page.goto("/adminpanel/settings/")
        admin_page.wait_for_load_state("networkidle")
        _require(
            admin_page,
            "address",
            "phone",
            "whatsapp_number",
            "email",
            "instagram_url",
        )
        # Labels used in adminpanel/settings.html
        content = admin_page.content().upper()
        assert "DIRECCION" in content or "DIRECCIÓN" in content
        assert "WHATSAPP" in content
        assert "INSTAGRAM" in content

    def test_settings_bank_fields(self, admin_page: Page):
        """Bank transfer fields (names match settings.html bank section)."""
        admin_page.goto("/adminpanel/settings/")
        admin_page.wait_for_load_state("networkidle")
        _require(
            admin_page,
            "bank_name",
            "bank_account_number",
            "bank_account_holder",
            "bank_account_code",
            "bank_extra",
        )
        content = admin_page.content().upper()
        assert "BANCO" in content or "DATOS BANCARIOS" in content

    def test_settings_multilingual_home_titles(self, admin_page: Page):
        """Multilingual home section titles + greeting taglines (es/en/pt/ca)."""
        admin_page.goto("/adminpanel/settings/")
        admin_page.wait_for_load_state("networkidle")
        _require(
            admin_page,
            "home_section_title_es",
            "home_section_title_en",
            "home_section_title_pt",
            "home_section_title_ca",
            "home_greeting_tagline_es",
            "home_greeting_tagline_en",
            "home_greeting_tagline_pt",
            "home_greeting_tagline_ca",
        )

    def test_settings_club_form_multipart_and_logo(self, admin_page: Page):
        """Club form supports logo upload (multipart) — nothing hardcoded in app."""
        admin_page.goto("/adminpanel/settings/")
        admin_page.wait_for_load_state("networkidle")
        form = admin_page.locator('form:has(input[name="action"][value="update_club"])')
        assert form.count() >= 1
        assert form.first.get_attribute("enctype") == "multipart/form-data"
        assert form.locator('input[type="file"][name="logo"]').count() >= 1
        assert form.locator('input[name="remove_logo"]').count() >= 1

    def test_settings_gerente_access(self, gerente_page: Page):
        gerente_page.goto("/adminpanel/settings/")
        gerente_page.wait_for_load_state("networkidle")
        assert gerente_page.locator("table, .card").count() >= 1
