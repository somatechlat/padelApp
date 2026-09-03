"""Playwright E2E test fixtures for Andes Padel admin panel."""

import pytest
from playwright.sync_api import sync_playwright, Page, BrowserContext

BASE_URL = "https://andespadel.yachaq.io"

ADMIN_EMAIL = "admin@andespadel.com"
ADMIN_PASSWORD = "Andes12345!"

GERENTE_EMAIL = "gerente@andespadel.com"
GERENTE_PASSWORD = "Andes12345!"

RECEPCION_EMAIL = "recepcion@andespadel.com"
RECEPCION_PASSWORD = "Andes12345!"

CLIENTE_EMAIL = "cliente@andespadel.com"
CLIENTE_PASSWORD = "Andes12345!"


@pytest.fixture(scope="session")
def browser():
    pw = sync_playwright().start()
    br = pw.chromium.launch(headless=True)
    yield br
    br.close()
    pw.stop()


@pytest.fixture
def context(browser):
    ctx = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        base_url=BASE_URL,
    )
    yield ctx
    ctx.close()


@pytest.fixture
def page(context):
    p = context.new_page()
    yield p
    p.close()


@pytest.fixture
def admin_page(context):
    """Authenticated admin (superadmin) page."""
    p = context.new_page()
    _login(p, ADMIN_EMAIL, ADMIN_PASSWORD)
    yield p
    p.close()


@pytest.fixture
def gerente_page(context):
    """Authenticated gerente page."""
    p = context.new_page()
    _login(p, GERENTE_EMAIL, GERENTE_PASSWORD)
    yield p
    p.close()


@pytest.fixture
def recepcion_page(context):
    """Authenticated recepcionista page."""
    p = context.new_page()
    _login(p, RECEPCION_EMAIL, RECEPCION_PASSWORD)
    yield p
    p.close()


def _login(page: Page, email: str, password: str):
    """Login to admin panel via session auth."""
    page.goto(f"{BASE_URL}/adminpanel/login/")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
