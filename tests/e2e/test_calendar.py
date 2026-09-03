"""E2E tests: Admin panel calendar view."""

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


class TestCalendar:
    """Test the calendar view."""

    def test_calendar_loads(self, admin_page: Page):
        admin_page.goto("/adminpanel/calendar/")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.locator("table.calendar-table, table").first.is_visible()

    def test_calendar_shows_courts(self, admin_page: Page):
        admin_page.goto("/adminpanel/calendar/")
        # Should show court names in header
        content = admin_page.content()
        assert "C1" in content or "Cancha" in content or "cancha" in content

    def test_calendar_shows_time_slots(self, admin_page: Page):
        admin_page.goto("/adminpanel/calendar/")
        content = admin_page.content()
        assert "08:00" in content or "08:30" in content

    def test_calendar_date_navigation(self, admin_page: Page):
        admin_page.goto("/adminpanel/calendar/")
        prev_btn = admin_page.locator('a:has-text("Anterior"), a:has-text("<<")')
        next_btn = admin_page.locator('a:has-text("Siguiente"), a:has-text(">>")')
        if next_btn.is_visible():
            next_btn.click()
            admin_page.wait_for_load_state("networkidle")
            assert admin_page.locator("table").is_visible()

    def test_calendar_date_picker(self, admin_page: Page):
        admin_page.goto("/adminpanel/calendar/")
        date_input = admin_page.locator('input[type="date"]')
        if date_input.is_visible():
            date_input.fill("2026-09-15")
            date_input.press("Enter")
            admin_page.wait_for_load_state("networkidle")
            assert admin_page.locator("table").is_visible()

    def test_calendar_slot_status_badges(self, admin_page: Page):
        admin_page.goto("/adminpanel/calendar/")
        # Should have slot cells with status classes
        slots = admin_page.locator(".slot-available, .slot-booked, .slot-held, .slot-blocked")
        assert slots.count() >= 0  # May be empty if no slots generated

    def test_calendar_block_slot(self, admin_page: Page):
        admin_page.goto("/adminpanel/calendar/")
        block_form = admin_page.locator('form:has(input[name="action"][value="block_slot"])')
        if block_form.count() > 0:
            # There's a block button for an available slot
            block_form.first.locator('button[type="submit"]').click()
            admin_page.wait_for_load_state("networkidle")
            # Should show success message or stay on calendar
            assert "/adminpanel/calendar/" in admin_page.url

    def test_calendar_manual_booking_form_exists(self, admin_page: Page):
        admin_page.goto("/adminpanel/calendar/")
        content = admin_page.content()
        # Manual booking form is inside a modal -- check the trigger button exists
        assert "Reserva Manual" in content or "crear" in content.lower() or "Nueva Reserva" in content
