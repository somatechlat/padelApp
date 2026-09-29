from datetime import datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone

from apps.bookings.models import Booking
from apps.courts.models import Court, PromoBanner, Venue, resolve_i18n
from apps.payments.admin import PaymentAdmin
from apps.payments.models import Payment
from apps.security.models import AuditLog
from apps.security.services import log_event

pytestmark = pytest.mark.django_db

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _png(name="banner.png"):
    return SimpleUploadedFile(name, MINIMAL_PNG, content_type="image/png")


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def venue():
    return Venue.objects.create(name="Andes Padel")


@pytest.fixture
def court(venue):
    return Court.objects.create(venue=venue, name="Cancha 1", price_base="10.00")


@pytest.fixture
def staff_users():
    User = get_user_model()
    recepcionista = User.objects.create_user(
        email="rec@test.com", password="pass12345", role="recepcionista", is_staff=True
    )
    gerente = User.objects.create_user(
        email="gerente@test.com", password="pass12345", role="gerente", is_staff=True
    )
    dueno = User.objects.create_user(
        email="dueno@test.com", password="pass12345", role="dueno", is_staff=True
    )
    superadmin = User.objects.create_user(
        email="super@test.com", password="pass12345", role="superadmin", is_staff=True
    )
    cliente = User.objects.create_user(
        email="cli@test.com", password="pass12345", role="cliente"
    )
    return {
        "recepcionista": recepcionista,
        "gerente": gerente,
        "dueno": dueno,
        "superadmin": superadmin,
        "cliente": cliente,
    }


@pytest.fixture
def booking(staff_users, court):
    return Booking.objects.create(
        user=staff_users["cliente"],
        court=court,
        date=timezone.localdate(),
        start_time=datetime.strptime("10:00", "%H:%M").time(),
        end_time=datetime.strptime("11:00", "%H:%M").time(),
        duration_minutes=60,
        players=4,
        price="10.00",
        status=Booking.Status.CONFIRMED,
    )


@pytest.fixture
def payment(booking):
    return Payment.objects.create(
        booking=booking,
        user=booking.user,
        method=Payment.Method.CASH,
        amount="10.00",
        status=Payment.Status.CONFIRMED,
    )


@pytest.fixture
def staff_user():
    User = get_user_model()
    return User.objects.create_user(
        email="admin@test.com", password="pass12345", role="dueno", is_staff=True
    )


@pytest.fixture
def banner():
    b = PromoBanner(title_i18n={"es": "Torneo"}, active=True, sort_order=1)
    b.image = _png()
    b.save()
    return b


class TestAuditLog:
    def test_append_only_blocks_update_and_delete(self, staff_users):
        log_event(staff_users["dueno"], "login", "User", staff_users["dueno"].id)
        entry = AuditLog.objects.get()
        entry.created_at = timezone.now()
        with pytest.raises(PermissionError):
            entry.save()
        with pytest.raises(PermissionError):
            entry.delete()

    def test_log_event_creates_entry(self, staff_users):
        log_event(staff_users["dueno"], "booking.cancel", "Booking", "42")
        assert AuditLog.objects.count() == 1
        assert AuditLog.objects.get().action == "booking.cancel"


class TestAdminpanelViews:
    def test_dashboard_requires_login(self, client):
        resp = client.get("/adminpanel/dashboard/")
        assert resp.status_code in (302, 403)

    def test_dashboard_ok_for_staff(self, client, staff_users, booking, payment):
        client.force_login(staff_users["recepcionista"])
        resp = client.get("/adminpanel/dashboard/")
        assert resp.status_code == 200
        assert resp.context["bookings_today"] == 1
        assert resp.context["revenue_today"] is not None

    def test_dashboard_forbidden_for_cliente(self, client, staff_users):
        client.force_login(staff_users["cliente"])
        resp = client.get("/adminpanel/dashboard/")
        assert resp.status_code in (302, 403)

    def test_calendar_renders_rows(self, client, staff_users, court, booking):
        client.force_login(staff_users["dueno"])
        resp = client.get("/adminpanel/calendar/")
        assert resp.status_code == 200
        assert any(resp.context["rows"])

    def test_audit_list_and_filter(self, client, staff_users):
        log_event(staff_users["dueno"], "booking.cancel", "Booking", "1")
        log_event(staff_users["dueno"], "login", "User", "2")
        client.force_login(staff_users["dueno"])
        resp = client.get("/adminpanel/audit/")
        assert resp.status_code == 200
        assert len(resp.context["entries"]) == 2
        resp = client.get("/adminpanel/audit/?action=login")
        assert [e.action for e in resp.context["entries"]] == ["login"]


class TestAdminRBAC:
    @staticmethod
    def _req(user):
        from types import SimpleNamespace

        return SimpleNamespace(user=user)

    def test_recepcionista_cannot_view_financial_admin(self, staff_users):
        admin = PaymentAdmin(Payment, None)
        assert admin.FINANCIAL is True
        assert admin.has_view_permission(self._req(staff_users["recepcionista"])) is False
        assert admin.has_change_permission(self._req(staff_users["recepcionista"])) is False

    def test_dueno_can_view_financial_admin(self, staff_users):
        admin = PaymentAdmin(Payment, None)
        assert admin.has_view_permission(self._req(staff_users["dueno"])) is True
        assert admin.has_change_permission(self._req(staff_users["dueno"])) is True

    def test_payment_changelist_forbidden_for_recepcionista(self, client, staff_users):
        client.force_login(staff_users["recepcionista"])
        resp = client.get("/admin/payments/payment/")
        assert resp.status_code == 403

    def test_payment_changelist_ok_for_dueno(self, client, staff_users):
        client.force_login(staff_users["dueno"])
        resp = client.get("/admin/payments/payment/")
        assert resp.status_code == 200


class TestVenueClubProfile:
    def test_contact_bank_i18n_fields_exist(self, venue):
        venue.phone = "099 267 6842"
        venue.email = "andespadelclub@gmail.com"
        venue.whatsapp_number = "593992676842"
        venue.whatsapp_message = "Hola"
        venue.instagram_url = "https://instagram.com/andespadelec"
        venue.maps_query = "Rodriguez Labandera y Ernesto Alban"
        venue.maps_url = "https://maps.google.com/?q=Andes+Padel"
        venue.bank_name = "Banco Pichincha"
        venue.bank_account_number = "21001234567890"
        venue.bank_account_holder = "Andes Padel S.A."
        venue.bank_account_code = "1799999999"
        venue.bank_extra = "Cuenta corriente"
        venue.home_section_title_i18n = {"es": "Reserva tu cancha", "en": "Book your court"}
        venue.home_greeting_tagline_i18n = {"es": "Bienvenido", "en": "Welcome"}
        venue.save()
        venue.refresh_from_db()
        assert venue.whatsapp_number == "593992676842"
        assert venue.bank_name == "Banco Pichincha"
        assert venue.home_section_title_for("es") == "Reserva tu cancha"
        assert venue.home_section_title_for("en") == "Book your court"

    def test_logo_optional(self, venue):
        assert not venue.logo

    def test_resolve_i18n_fallback(self):
        assert resolve_i18n({"es": "Hola", "en": "Hi"}, "en") == "Hi"
        assert resolve_i18n({"es": "Hola"}, "en") == "Hola"
        assert resolve_i18n({}, "es") == ""
        assert resolve_i18n(None, "es") == ""


class TestPromoBannerModel:
    def test_title_resolution(self, banner):
        assert banner.title_for("es") == "Torneo"
        assert banner.title_for("en") == "Torneo"

    def test_is_visible_now_respects_active_and_window(self, banner):
        assert banner.is_visible_now() is True
        banner.active = False
        assert banner.is_visible_now() is False
        banner.active = True
        banner.starts_at = timezone.now() + timedelta(days=1)
        banner.ends_at = timezone.now() + timedelta(days=2)
        assert banner.is_visible_now() is False
        banner.starts_at = timezone.now() - timedelta(days=1)
        banner.ends_at = timezone.now() + timedelta(days=1)
        assert banner.is_visible_now() is True

    def test_image_required_on_model(self):
        from django.core.exceptions import ValidationError

        b = PromoBanner(title_i18n={"es": "Sin imagen"})
        b.image = None
        with pytest.raises(ValidationError):
            b.save()


class TestSettingsClubAdmin:
    def test_settings_get_renders_club_fields(self, client, staff_user, venue):
        client.force_login(staff_user)
        resp = client.get("/adminpanel/settings/")
        assert resp.status_code == 200
        content = resp.content.decode()
        for name in (
            "address",
            "phone",
            "whatsapp_number",
            "email",
            "instagram_url",
            "bank_name",
            "bank_account_number",
            "bank_account_holder",
            "bank_account_code",
            "bank_extra",
            "home_section_title_es",
            "home_section_title_en",
            "home_section_title_pt",
            "home_section_title_ca",
            "home_greeting_tagline_es",
            "home_greeting_tagline_en",
            "home_greeting_tagline_pt",
            "home_greeting_tagline_ca",
        ):
            assert f'name="{name}"' in content, f"settings.html missing field {name}"

    def test_update_club_persists_contact_bank_i18n(self, client, staff_user, venue):
        client.force_login(staff_user)
        resp = client.post(
            "/adminpanel/settings/",
            {
                "action": "update_club",
                "name": "Andes Padel Club",
                "address": "Rodriguez Labandera y Ernesto Alban, Quito",
                "maps_query": "Andes Padel Quito",
                "maps_url": "https://maps.google.com/?q=Andes",
                "phone": "099 267 6842",
                "email": "andespadelclub@gmail.com",
                "whatsapp_number": "593992676842",
                "whatsapp_message": "Hola, quiero reservar",
                "instagram_url": "https://instagram.com/andespadelec",
                "bank_name": "Banco Pichincha",
                "bank_account_number": "21001234567890",
                "bank_account_holder": "Andes Padel S.A.",
                "bank_account_code": "1799999999",
                "bank_extra": "Cuenta corriente",
                "home_section_title_es": "Reserva tu cancha",
                "home_section_title_en": "Book your court",
                "home_section_title_pt": "Reserve sua quadra",
                "home_section_title_ca": "Reserva la teva pista",
                "home_greeting_tagline_es": "Bienvenido",
                "home_greeting_tagline_en": "Welcome",
                "home_greeting_tagline_pt": "Bem-vindo",
                "home_greeting_tagline_ca": "Benvingut",
            },
        )
        assert resp.status_code == 302
        venue.refresh_from_db()
        assert venue.whatsapp_number == "593992676842"
        assert venue.instagram_url == "https://instagram.com/andespadelec"
        assert venue.bank_account_number == "21001234567890"
        assert venue.home_section_title_for("es") == "Reserva tu cancha"
        assert venue.home_greeting_tagline_for("en") == "Welcome"
        assert AuditLog.objects.filter(action="admin.club_update").exists()

    def test_update_club_logo_upload_and_remove(self, client, staff_user, venue):
        client.force_login(staff_user)
        resp = client.post(
            "/adminpanel/settings/",
            {"action": "update_club", "logo": _png("logo.png")},
        )
        assert resp.status_code == 302
        venue.refresh_from_db()
        assert venue.logo
        resp = client.post(
            "/adminpanel/settings/",
            {"action": "update_club", "remove_logo": "1"},
        )
        venue.refresh_from_db()
        assert not venue.logo

    def test_update_club_strips_empty_i18n(self, client, staff_user, venue):
        client.force_login(staff_user)
        client.post(
            "/adminpanel/settings/",
            {
                "action": "update_club",
                "home_section_title_es": "Reserva tu cancha",
                "home_section_title_en": "   ",
                "home_greeting_tagline_es": "Hola",
                "home_greeting_tagline_en": "",
            },
        )
        venue.refresh_from_db()
        assert venue.home_section_title_i18n == {"es": "Reserva tu cancha"}
        assert venue.home_greeting_tagline_i18n == {"es": "Hola"}


class TestBannersAdminCRUD:
    def test_banners_page_requires_staff(self, client):
        resp = client.get("/adminpanel/banners/")
        assert resp.status_code in (302, 403)

    def test_banners_get_lists_and_fields(self, client, staff_user, banner):
        client.force_login(staff_user)
        resp = client.get("/adminpanel/banners/")
        assert resp.status_code == 200
        content = resp.content.decode()
        for name in (
            "image",
            "title_es",
            "title_en",
            "title_pt",
            "title_ca",
            "subtitle_es",
            "link_type",
            "link_url",
            "sort_order",
            "starts_at",
            "ends_at",
            "active",
            "remove_image",
        ):
            assert f'name="{name}"' in content, f"banners.html missing field {name}"
        for action in (
            "create_banner",
            "edit_banner",
            "toggle_banner",
            "move_banner",
            "delete_banner",
        ):
            assert f'value="{action}"' in content, f"banners.html missing action {action}"

    def test_create_banner_requires_image(self, client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            "/adminpanel/banners/",
            {"action": "create_banner", "title_es": "Sin imagen"},
        )
        assert resp.status_code == 302
        assert PromoBanner.objects.count() == 0

    def test_create_banner_with_image(self, client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            "/adminpanel/banners/",
            {
                "action": "create_banner",
                "image": _png(),
                "title_es": "Torneo de Verano",
                "title_en": "Summer Open",
                "subtitle_es": "Inscribete",
                "link_type": "url",
                "link_url": "https://example.com/evento",
                "sort_order": "3",
                "active": "on",
            },
        )
        assert resp.status_code == 302
        b = PromoBanner.objects.get()
        assert b.title_i18n == {"es": "Torneo de Verano", "en": "Summer Open"}
        assert b.subtitle_i18n == {"es": "Inscribete"}
        assert b.link_type == "url"
        assert b.active is True
        assert b.sort_order == 3
        assert b.image
        assert AuditLog.objects.filter(action="admin.banner_create").exists()

    def test_edit_banner_updates_fields(self, client, staff_user, banner):
        client.force_login(staff_user)
        resp = client.post(
            "/adminpanel/banners/",
            {
                "action": "edit_banner",
                "banner_id": str(banner.id),
                "title_es": "Titulo Editado",
                "title_en": "Edited",
                "link_type": "whatsapp",
                "link_url": "https://wa.me/593992676842",
                "sort_order": "7",
            },
        )
        assert resp.status_code == 302
        banner.refresh_from_db()
        assert banner.title_for("es") == "Titulo Editado"
        assert banner.link_type == "whatsapp"
        assert banner.sort_order == 7

    def test_edit_banner_image_upload_and_remove(self, client, staff_user, banner):
        client.force_login(staff_user)
        old_name = banner.image.name
        resp = client.post(
            "/adminpanel/banners/",
            {
                "action": "edit_banner",
                "banner_id": str(banner.id),
                "image": _png("nueva.png"),
            },
        )
        assert resp.status_code == 302
        banner.refresh_from_db()
        assert banner.image
        assert banner.image.name != old_name

        client.post(
            "/adminpanel/banners/",
            {
                "action": "edit_banner",
                "banner_id": str(banner.id),
                "remove_image": "1",
            },
        )
        banner.refresh_from_db()
        assert not banner.image

    def test_toggle_banner(self, client, staff_user, banner):
        client.force_login(staff_user)
        assert banner.active is True
        client.post(
            "/adminpanel/banners/",
            {"action": "toggle_banner", "banner_id": str(banner.id)},
        )
        banner.refresh_from_db()
        assert banner.active is False
        client.post(
            "/adminpanel/banners/",
            {"action": "toggle_banner", "banner_id": str(banner.id)},
        )
        banner.refresh_from_db()
        assert banner.active is True

    def test_move_banner_reorders(self, client, staff_user, banner):
        client.force_login(staff_user)
        client.post(
            "/adminpanel/banners/",
            {
                "action": "move_banner",
                "banner_id": str(banner.id),
                "direction": "up",
            },
        )
        banner.refresh_from_db()
        assert banner.sort_order == 0

    def test_delete_banner(self, client, staff_user, banner):
        client.force_login(staff_user)
        bid = banner.id
        resp = client.post(
            "/adminpanel/banners/",
            {"action": "delete_banner", "banner_id": str(bid)},
        )
        assert resp.status_code == 302
        assert not PromoBanner.objects.filter(id=bid).exists()
        assert AuditLog.objects.filter(action="admin.banner_delete").exists()

    def test_invalid_dates_rejected(self, client, staff_user):
        client.force_login(staff_user)
        resp = client.post(
            "/adminpanel/banners/",
            {
                "action": "create_banner",
                "image": _png(),
                "title_es": "Fechas malas",
                "starts_at": "not-a-date",
            },
        )
        assert resp.status_code == 302
        assert PromoBanner.objects.count() == 0


class TestAdminPanelRoleScoping:
    """RBAC on the custom admin panel: recepcionista is operational-only."""

    def test_recepcionista_cannot_refund(self, client, staff_users, payment):
        client.force_login(staff_users["recepcionista"])
        resp = client.post(
            "/adminpanel/payments/",
            {"action": "refund", "payment_id": str(payment.id)},
        )
        assert resp.status_code == 403
        payment.refresh_from_db()
        assert payment.status != Payment.Status.REFUNDED

    def test_recepcionista_cannot_confirm_transfer(self, client, staff_users, payment):
        client.force_login(staff_users["recepcionista"])
        resp = client.post(
            "/adminpanel/payments/",
            {"action": "confirm_transfer", "payment_id": str(payment.id)},
        )
        assert resp.status_code == 403

    def test_recepcionista_cannot_change_role(self, client, staff_users):
        client.force_login(staff_users["recepcionista"])
        target = staff_users["cliente"]
        resp = client.post(
            "/adminpanel/users/",
            {"action": "change_role", "user_id": str(target.id), "role": "superadmin"},
        )
        assert resp.status_code == 403
        target.refresh_from_db()
        assert target.role == "cliente"

    def test_recepcionista_cannot_edit_bank_settings(self, client, staff_users, venue):
        client.force_login(staff_users["recepcionista"])
        resp = client.post(
            "/adminpanel/settings/",
            {"action": "update_club", "bank_name": "Banco Hackeado"},
        )
        assert resp.status_code == 403
        venue.refresh_from_db()
        assert venue.bank_name != "Banco Hackeado"

    def test_recepcionista_cannot_view_settings(self, client, staff_users, venue):
        client.force_login(staff_users["recepcionista"])
        resp = client.get("/adminpanel/settings/")
        assert resp.status_code == 403

    def test_recepcionista_cannot_view_audit(self, client, staff_users):
        client.force_login(staff_users["recepcionista"])
        resp = client.get("/adminpanel/audit/")
        assert resp.status_code == 403

    def test_recepcionista_cannot_view_reports(self, client, staff_users):
        client.force_login(staff_users["recepcionista"])
        resp = client.get("/adminpanel/reports/")
        assert resp.status_code == 403

    def test_recepcionista_cannot_export_csv(self, client, staff_users, booking):
        client.force_login(staff_users["recepcionista"])
        resp = client.get("/adminpanel/reports/?export=csv")
        assert resp.status_code == 403

    def test_gerente_cannot_refund(self, client, staff_users, payment):
        client.force_login(staff_users["gerente"])
        resp = client.post(
            "/adminpanel/payments/",
            {"action": "refund", "payment_id": str(payment.id)},
        )
        assert resp.status_code == 403
        payment.refresh_from_db()
        assert payment.status != Payment.Status.REFUNDED

    def test_gerente_cannot_change_role(self, client, staff_users):
        client.force_login(staff_users["gerente"])
        target = staff_users["cliente"]
        resp = client.post(
            "/adminpanel/users/",
            {"action": "change_role", "user_id": str(target.id), "role": "gerente"},
        )
        assert resp.status_code == 403

    def test_gerente_cannot_edit_bank_settings(self, client, staff_users, venue):
        client.force_login(staff_users["gerente"])
        resp = client.post(
            "/adminpanel/settings/",
            {"action": "update_club", "bank_name": "Banco Hackeado"},
        )
        assert resp.status_code == 403

    def test_gerente_cannot_export_csv(self, client, staff_users, booking):
        client.force_login(staff_users["gerente"])
        resp = client.get("/adminpanel/reports/?export=csv")
        assert resp.status_code == 403

    def test_gerente_can_view_reports(self, client, staff_users, booking):
        client.force_login(staff_users["gerente"])
        resp = client.get("/adminpanel/reports/")
        assert resp.status_code == 200

    def test_gerente_can_confirm_transfer(self, client, staff_users, payment, monkeypatch):
        from apps.notifications.services import NotificationService

        monkeypatch.setattr(NotificationService, "notify", staticmethod(lambda *a, **k: None))
        client.force_login(staff_users["gerente"])
        resp = client.post(
            "/adminpanel/payments/",
            {"action": "confirm_transfer", "payment_id": str(payment.id)},
        )
        assert resp.status_code == 302

    def test_dueno_can_refund(self, client, staff_users, payment, monkeypatch):
        from apps.notifications.services import NotificationService

        monkeypatch.setattr(NotificationService, "notify", staticmethod(lambda *a, **k: None))
        client.force_login(staff_users["dueno"])
        resp = client.post(
            "/adminpanel/payments/",
            {"action": "refund", "payment_id": str(payment.id)},
        )
        assert resp.status_code == 302
        payment.refresh_from_db()
        assert payment.status == Payment.Status.REFUNDED

    def test_dueno_can_export_csv(self, client, staff_users, booking):
        client.force_login(staff_users["dueno"])
        resp = client.get("/adminpanel/reports/?export=csv")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"

    def test_dueno_can_change_role_to_gerente(self, client, staff_users):
        client.force_login(staff_users["dueno"])
        target = staff_users["cliente"]
        resp = client.post(
            "/adminpanel/users/",
            {"action": "change_role", "user_id": str(target.id), "role": "gerente"},
        )
        assert resp.status_code == 302
        target.refresh_from_db()
        assert target.role == "gerente"

    def test_dueno_cannot_promote_to_superadmin(self, client, staff_users):
        client.force_login(staff_users["dueno"])
        target = staff_users["recepcionista"]
        resp = client.post(
            "/adminpanel/users/",
            {"action": "change_role", "user_id": str(target.id), "role": "superadmin"},
        )
        assert resp.status_code == 302
        target.refresh_from_db()
        assert target.role == "recepcionista"

    def test_superadmin_can_grant_superadmin(self, client, staff_users):
        client.force_login(staff_users["superadmin"])
        target = staff_users["recepcionista"]
        resp = client.post(
            "/adminpanel/users/",
            {"action": "change_role", "user_id": str(target.id), "role": "superadmin"},
        )
        assert resp.status_code == 302
        target.refresh_from_db()
        assert target.role == "superadmin"

    def test_dueno_can_edit_bank_settings(self, client, staff_users, venue):
        client.force_login(staff_users["dueno"])
        resp = client.post(
            "/adminpanel/settings/",
            {"action": "update_club", "bank_name": "Banco Pichincha"},
        )
        assert resp.status_code == 302
        venue.refresh_from_db()
        assert venue.bank_name == "Banco Pichincha"

    def test_court_image_upload_rejects_bad_type(self, client, staff_users, venue):
        client.force_login(staff_users["recepcionista"])
        bad = SimpleUploadedFile("evil.php", b"<?php ?>", content_type="application/x-php")
        resp = client.post(
            "/adminpanel/courts/",
            {"action": "create_court", "name": "Cancha X", "image": bad},
        )
        assert resp.status_code == 302
        assert not Court.objects.filter(name="Cancha X").exists()

    def test_edit_event_invalid_capacity_rejected(self, client, staff_users):
        from apps.events.models import Event

        client.force_login(staff_users["recepcionista"])
        event = Event.objects.create(
            title="Prueba",
            title_es="Prueba",
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(hours=2),
            status="published",
            capacity=10,
            created_by=staff_users["dueno"],
        )
        resp = client.post(
            "/adminpanel/events/",
            {
                "action": "edit_event",
                "event_id": str(event.id),
                "capacity": "not-a-number",
            },
        )
        assert resp.status_code == 302
        event.refresh_from_db()
        assert event.capacity == 10

    def test_edit_banner_invalid_sort_order_rejected(self, client, staff_user, banner):
        client.force_login(staff_user)
        resp = client.post(
            "/adminpanel/banners/",
            {
                "action": "edit_banner",
                "banner_id": str(banner.id),
                "sort_order": "not-a-number",
            },
        )
        assert resp.status_code == 302
        banner.refresh_from_db()
        assert banner.sort_order == 1
