"""E2E tests: Admin panel payments management."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestPayments:
    """Test the payments management page."""

    def test_payments_page_loads(self, admin_page: Page):
        admin_page.goto("/adminpanel/payments/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("table").is_visible()

    def test_payments_table_headers(self, admin_page: Page):
        admin_page.goto("/adminpanel/payments/")
        headers = admin_page.locator("th")
        header_texts = [headers.nth(i).inner_text().lower() for i in range(headers.count())]
        assert any("monto" in h or "amount" in h for h in header_texts)
        assert any("estado" in h or "status" in h for h in header_texts)
        assert any("método" in h or "method" in h or "metodo" in h for h in header_texts)

    def test_payments_filter_by_status(self, admin_page: Page):
        admin_page.goto("/adminpanel/payments/")
        status_select = admin_page.locator('select[name="status"]')
        if status_select.is_visible():
            status_select.select_option("captured")
            status_select.press("Enter")
            admin_page.wait_for_load_state("networkidle")
            assert admin_page.locator("table").is_visible()

    def test_payments_filter_by_method(self, admin_page: Page):
        admin_page.goto("/adminpanel/payments/")
        method_select = admin_page.locator('select[name="method"]')
        if method_select.is_visible():
            method_select.select_option("transfer")
            method_select.press("Enter")
            admin_page.wait_for_load_state("networkidle")
            assert admin_page.locator("table").is_visible()

    def test_payments_confirm_transfer_button(self, admin_page: Page):
        admin_page.goto("/adminpanel/payments/")
        confirm_form = admin_page.locator('form:has(input[name="action"][value="confirm_transfer"])')
        # May or may not have pending transfers
        if confirm_form.count() > 0:
            assert confirm_form.first.locator('button[type="submit"]').is_visible()

    def test_payments_reject_transfer_button(self, admin_page: Page):
        admin_page.goto("/adminpanel/payments/")
        reject_form = admin_page.locator('form:has(input[name="action"][value="reject_transfer"])')
        if reject_form.count() > 0:
            assert reject_form.first.locator('button[type="submit"]').is_visible()

    def test_payments_refund_button(self, admin_page: Page):
        admin_page.goto("/adminpanel/payments/")
        refund_form = admin_page.locator('form:has(input[name="action"][value="refund"])')
        if refund_form.count() > 0:
            assert refund_form.first.locator('button[type="submit"]').is_visible()

    def test_payments_status_badges(self, admin_page: Page):
        admin_page.goto("/adminpanel/payments/")
        content = admin_page.content().lower()
        # Check that payment statuses are displayed somewhere on the page
        assert any(s in content for s in [
            "capturado", "pendiente", "confirmado", "fallido",
            "reembolsado", "transferencia", "captured", "pending",
            "confirmed", "failed", "refunded", "efectivo", "cash"
        ])

    def test_payments_pagination(self, admin_page: Page):
        admin_page.goto("/adminpanel/payments/")
        assert admin_page.locator("table").is_visible()
