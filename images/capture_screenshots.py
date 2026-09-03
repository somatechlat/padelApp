#!/usr/bin/env python3
"""Capture screenshots of PadelApp web interfaces using Playwright."""

import json
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "https://andespadel.yachaq.io"
OUT = Path(__file__).parent
ADMIN_USER = "admin@andespadel.com"
ADMIN_PASS = "Andes12345!"


def capture(page, name, url=None, full_page=True, wait=3, screenshot_timeout=60000):
    print(f"  Capturing: {name}")
    if url:
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(2)
    time.sleep(wait)
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=full_page, timeout=screenshot_timeout)
    print(f"    -> {path.name}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})

        # ── 1. Swagger API docs (public, no auth) ──
        print("\n[1/5] Swagger API Docs (public)")
        page = ctx.new_page()
        capture(page, "01_swagger_overview", f"{BASE}/api/docs/", wait=5)
        page.close()

        # ── 2. ReDoc API docs ──
        print("\n[2/5] ReDoc API Docs")
        page = ctx.new_page()
        capture(page, "02_redoc_overview", f"{BASE}/api/redoc/", wait=5)
        page.close()

        # ── 3. Django Admin ──
        print("\n[3/5] Django Admin")
        page = ctx.new_page()

        # Capture login page
        capture(page, "03_admin_login", f"{BASE}/admin/login/?next=/admin/", wait=3)

        # Login to Django admin
        page.fill("#id_username", ADMIN_USER)
        page.fill("#id_password", ADMIN_PASS)
        page.click("#login-form input[type=submit]")
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        # Dashboard
        capture(page, "04_admin_dashboard", f"{BASE}/admin/", wait=3)

        # Django Admin sections
        admin_sections = [
            ("05_admin_users", f"{BASE}/admin/users/user/"),
            ("06_admin_courts", f"{BASE}/admin/courts/court/"),
            ("07_admin_bookings", f"{BASE}/admin/bookings/booking/"),
            ("08_admin_events", f"{BASE}/admin/events/event/"),
            ("09_admin_timeslots", f"{BASE}/admin/scheduling/timeslot/"),
            ("10_admin_pricing", f"{BASE}/admin/pricing/pricerule/"),
            ("11_admin_payments", f"{BASE}/admin/payments/payment/"),
            ("12_admin_notifications", f"{BASE}/admin/notifications/notification/"),
            ("13_admin_venues", f"{BASE}/admin/courts/venue/"),
            ("14_admin_policies", f"{BASE}/admin/policies/cancellationpolicy/"),
            ("15_admin_audit_logs", f"{BASE}/admin/security/auditlog/"),
        ]
        for name, url in admin_sections:
            try:
                capture(page, name, url, wait=3)
            except Exception as e:
                print(f"    SKIP {name}: {e}")

        # Keep page open for adminpanel (shares session cookie)

        # ── 4. Custom Admin Panel (reuse same authenticated session) ──
        print("\n[4/5] Custom Admin Panel")
        try:
            page.goto(f"{BASE}/adminpanel/", wait_until="networkidle", timeout=15000)
            time.sleep(3)
            print(f"    Admin panel URL: {page.url}")

            capture(page, "16_custom_admin_dashboard", wait=5)

            panel_sections = [
                ("17_custom_admin_calendar", f"{BASE}/adminpanel/calendar/"),
                ("18_custom_admin_courts", f"{BASE}/adminpanel/courts/"),
                ("19_custom_admin_users", f"{BASE}/adminpanel/users/"),
                ("20_custom_admin_payments", f"{BASE}/adminpanel/payments/"),
                ("21_custom_admin_events", f"{BASE}/adminpanel/events/"),
                ("22_custom_admin_reports", f"{BASE}/adminpanel/reports/"),
                ("23_custom_admin_settings", f"{BASE}/adminpanel/settings/"),
                ("24_custom_admin_audit", f"{BASE}/adminpanel/audit/"),
            ]
            for name, url in panel_sections:
                try:
                    capture(page, name, url, wait=3)
                except Exception as e:
                    print(f"    SKIP {name}: {e}")
        except Exception as e:
            print(f"    Admin panel error: {e}")
            # Try screenshots of whatever loaded
            try:
                page.screenshot(path=str(OUT / "16_custom_admin_dashboard.png"), full_page=True)
                print(f"    -> 16_custom_admin_dashboard.png (partial)")
            except Exception:
                pass

        page.close()

        # ── 5. Swagger with auth ──
        print("\n[5/5] Swagger with Auth")
        page = ctx.new_page()
        page.goto(f"{BASE}/api/docs/", wait_until="networkidle")
        time.sleep(5)

        try:
            req = urllib.request.Request(
                f"{BASE}/api/auth/login/",
                data=json.dumps({"email": ADMIN_USER, "password": ADMIN_PASS}).encode(),
                headers={"Content-Type": "application/json"},
            )
            resp = json.loads(urllib.request.urlopen(req).read())
            token = resp["access"]

            lock_btn = page.locator(".btn.authorize").first
            if lock_btn.is_visible():
                lock_btn.click()
                time.sleep(1)
                token_input = page.locator(".auth-container textarea, .auth-container input[type=text]").first
                token_input.fill(token)
                page.locator(".auth-container .btn.btn-done, .auth-container button.btn").first.click()
                time.sleep(2)
        except Exception as e:
            print(f"    Auth note: {e}")

        time.sleep(3)
        capture(page, "25_swagger_authenticated", wait=5)
        page.close()

        browser.close()
        print(f"\nDone! All screenshots saved to {OUT}")


if __name__ == "__main__":
    main()
