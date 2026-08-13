import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from apps.bookings.models import Booking
from apps.courts.models import Court, Venue
from apps.payments.admin import PaymentAdmin
from apps.payments.models import Payment
from apps.security.models import AuditLog
from apps.security.services import log_event

pytestmark = pytest.mark.django_db


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
    dueno = User.objects.create_user(
        email="dueno@test.com", password="pass12345", role="dueno", is_staff=True
    )
    cliente = User.objects.create_user(
        email="cli@test.com", password="pass12345", role="cliente"
    )
    return {"recepcionista": recepcionista, "dueno": dueno, "cliente": cliente}


@pytest.fixture
def booking(staff_users, court):
    return Booking.objects.create(
        user=staff_users["cliente"],
        court=court,
        date=timezone.localdate(),
        start_time=timezone.datetime.strptime("10:00", "%H:%M").time(),
        end_time=timezone.datetime.strptime("11:00", "%H:%M").time(),
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
        client.force_login(staff_users["recepcionista"])
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
