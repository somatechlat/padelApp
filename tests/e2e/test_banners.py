"""E2E tests: Admin-managed promo banners CRUD (create/edit/toggle/delete).

Field names and actions match apps/adminpanel/templates/adminpanel/banners.html
and BannersAdminView POST handlers (create_banner / edit_banner / toggle_banner /
move_banner / delete_banner).
"""

from pathlib import Path

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e

BANNERS_PATH = "/adminpanel/banners/"

# 1x1 PNG for upload tests
MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _named(page: Page, name: str):
    return page.locator(
        f'input[name="{name}"], textarea[name="{name}"], select[name="{name}"]'
    )


@pytest.fixture
def png_upload(tmp_path: Path):
    p = tmp_path / "banner-e2e.png"
    p.write_bytes(MINIMAL_PNG)
    return str(p)


class TestPromoBanners:
    """Promo banner admin management page."""

    def test_banners_page_loads(self, admin_page: Page):
        admin_page.goto(BANNERS_PATH)
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("table, .card, .section-title").count() >= 1
        content = admin_page.content()
        assert "Banner" in content

    def test_banner_create_button_exists(self, admin_page: Page):
        admin_page.goto(BANNERS_PATH)
        assert admin_page.locator('button:has-text("Nuevo Banner")').count() >= 1

    def test_banner_create_ui_exists(self, admin_page: Page):
        """Create form with required image file upload (multipart)."""
        admin_page.goto(BANNERS_PATH)
        form = admin_page.locator('form:has(input[name="action"][value="create_banner"])')
        assert form.count() >= 1
        assert form.first.get_attribute("enctype") == "multipart/form-data"
        file_input = form.locator('input[type="file"][name="image"]')
        assert file_input.count() >= 1
        assert file_input.first.get_attribute("accept") == "image/*"
        # Required image validation on the client side as well
        assert file_input.first.get_attribute("required") is not None

    def test_banner_create_form_fields(self, admin_page: Page):
        admin_page.goto(BANNERS_PATH)
        form = admin_page.locator('form:has(input[name="action"][value="create_banner"])')
        for name in (
            "title_es",
            "title_en",
            "title_pt",
            "title_ca",
            "subtitle_es",
            "subtitle_en",
            "subtitle_pt",
            "subtitle_ca",
            "link_type",
            "link_url",
            "sort_order",
            "starts_at",
            "ends_at",
            "active",
        ):
            assert form.locator(f'[name="{name}"]').count() >= 1, f"missing {name}"

    def test_banner_list_table(self, admin_page: Page):
        admin_page.goto(BANNERS_PATH)
        table = admin_page.locator("table").first
        assert table.is_visible()
        content = admin_page.content()
        for col in ("Imagen", "Titulo", "Subtitulo", "Enlace", "Orden", "Estado", "Acciones"):
            assert col in content

    def test_banner_edit_ui_exists(self, admin_page: Page):
        admin_page.goto(BANNERS_PATH)
        form = admin_page.locator('form:has(input[name="action"][value="edit_banner"])')
        assert form.count() >= 1
        assert form.first.get_attribute("enctype") == "multipart/form-data"
        assert form.locator('input[type="file"][name="image"]').count() >= 1
        assert form.locator('input[name="remove_image"]').count() >= 1
        assert admin_page.locator('button:has-text("Editar")').count() >= 1

    def test_banner_toggle_delete_move_forms(self, admin_page: Page):
        admin_page.goto(BANNERS_PATH)
        # Create + edit forms always present; row actions appear when banners exist
        content = admin_page.content()
        if 'value="toggle_banner"' in content or "Desactivar" in content or "Activar" in content:
            assert admin_page.locator(
                'form:has(input[name="action"][value="toggle_banner"])'
            ).count() >= 1
            assert admin_page.locator(
                'form:has(input[name="action"][value="delete_banner"])'
            ).count() >= 1
            assert admin_page.locator(
                'form:has(input[name="action"][value="move_banner"])'
            ).count() >= 1
        else:
            # Empty state still shows create UI
            assert admin_page.locator(
                'form:has(input[name="action"][value="create_banner"])'
            ).count() >= 1

    def test_banner_create_toggle_delete_flow(self, admin_page: Page, png_upload: str):
        """Full admin CRUD cycle with image upload, then cleanup."""
        admin_page.goto(BANNERS_PATH)
        admin_page.wait_for_load_state("networkidle")

        admin_page.click('button:has-text("Nuevo Banner")')
        form = admin_page.locator('form:has(input[name="action"][value="create_banner"])')
        form.locator('input[type="file"][name="image"]').set_input_files(png_upload)
        form.locator('input[name="title_es"]').fill("E2E Banner Temporal")
        form.locator('input[name="title_en"]').fill("E2E Temp Banner")
        form.locator('select[name="link_type"]').select_option("none")
        form.locator('input[name="sort_order"]').fill("99")
        form.locator('button[type="submit"]').click()
        admin_page.wait_for_load_state("networkidle")

        row = admin_page.locator("table tbody tr", has_text="E2E Banner Temporal")
        assert row.count() >= 1, "Created banner not listed"

        # Toggle active
        toggle = row.locator('form:has(input[name="action"][value="toggle_banner"])')
        assert toggle.count() >= 1
        toggle.locator('button[type="submit"]').click()
        admin_page.wait_for_load_state("networkidle")

        # Delete (confirm dialog)
        row = admin_page.locator("table tbody tr", has_text="E2E Banner Temporal")
        delete = row.locator('form:has(input[name="action"][value="delete_banner"])')
        assert delete.count() >= 1
        admin_page.once("dialog", lambda d: d.accept())
        delete.locator('button[type="submit"]').click()
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("table tbody tr", has_text="E2E Banner Temporal").count() == 0

    def test_banners_nav_link(self, admin_page: Page):
        admin_page.goto("/adminpanel/dashboard/")
        admin_page.wait_for_load_state("networkidle")
        nav = admin_page.locator("aside nav")
        link_texts = [nav.locator("a").nth(i).inner_text().strip() for i in range(nav.locator("a").count())]
        assert any("Banner" in t for t in link_texts)


class TestClubContactOnSettings:
    """Club contact / bank / home titles required on settings (admin-managed)."""

    def test_settings_club_contact_fields_present(self, admin_page: Page):
        admin_page.goto("/adminpanel/settings/")
        admin_page.wait_for_load_state("networkidle")
        for name in ("address", "phone", "whatsapp_number", "email", "instagram_url"):
            assert _named(admin_page, name).count() >= 1, f"missing {name}"

    def test_settings_bank_fields_present(self, admin_page: Page):
        admin_page.goto("/adminpanel/settings/")
        admin_page.wait_for_load_state("networkidle")
        for name in (
            "bank_name",
            "bank_account_number",
            "bank_account_holder",
            "bank_account_code",
            "bank_extra",
        ):
            assert _named(admin_page, name).count() >= 1, f"missing {name}"
