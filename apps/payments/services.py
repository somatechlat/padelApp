import logging
from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext

from apps.notifications.services import NotificationService
from apps.payments.models import Payment
from apps.security.services import log_event
from runsecrets import secrets

logger = logging.getLogger(__name__)

# No card data is ever stored (PCI SAQ-A, NFR-0028): only Stripe PaymentIntent
# identifiers are persisted.


class PaymentService:
    @staticmethod
    def create_intent(booking):
        import stripe

        stripe.api_key = secrets.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=int(booking.price * 100),
            currency="usd",
            metadata={"booking_id": booking.id},
        )
        payment = PaymentService.create_stripe_payment(booking, intent)
        log_event(booking.user, "payment.intent", "Payment", payment.id)
        return payment

    @staticmethod
    def create_stripe_payment(booking, intent):
        return Payment.objects.create(
            booking=booking,
            user=booking.user,
            method=Payment.Method.STRIPE,
            amount=booking.price,
            currency="USD",
            status=Payment.Status.PENDING,
            stripe_payment_intent_id=intent.id,
        )

    @staticmethod
    def confirm(payment):
        payment.status = Payment.Status.CAPTURED
        payment.save(update_fields=["status", "updated_at"])
        log_event(payment.user, "payment.captured", "Payment", payment.id)
        NotificationService.notify(
            payment.user,
            "payment_success",
            data={"amount": f"${payment.amount}", "payment_id": payment.id},
        )
        return payment

    @staticmethod
    def fail(payment, reason=""):
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
        log_event(payment.user, "payment.failed", "Payment", payment.id,
                  after={"reason": reason})
        NotificationService.notify(
            payment.user,
            "payment_failed",
            data={"amount": f"${payment.amount}", "payment_id": payment.id, "reason": reason},
        )
        return payment

    @staticmethod
    def record_transfer(booking, reference):
        payment = Payment.objects.create(
            booking=booking,
            user=booking.user,
            method=Payment.Method.TRANSFER,
            amount=booking.price,
            currency="USD",
            status=Payment.Status.PENDING_TRANSFER,
            reference=reference,
        )
        log_event(booking.user, "payment.transfer_recorded", "Payment", payment.id)
        return payment

    @staticmethod
    def confirm_transfer(payment):
        """Mark a bank transfer as captured and confirm its booking.

        Idempotent: a double-click on the admin button, or two receptionists
        confirming the same receipt, must not send two notifications or
        re-run the booking transition.
        """
        with transaction.atomic():
            payment.refresh_from_db()
            if payment.status == Payment.Status.CAPTURED:
                return payment
            payment.status = Payment.Status.CAPTURED
            payment.save(update_fields=["status", "updated_at"])
            if payment.booking and payment.booking.status == "pending_payment":
                payment.booking.transition_to("confirmed")
        log_event(payment.user, "payment.transfer_confirmed", "Payment", payment.id)
        NotificationService.notify(
            payment.user,
            "transfer_confirmed",
            data={"amount": f"${payment.amount}", "payment_id": payment.id},
        )
        return payment

    @staticmethod
    def reject_transfer(payment, reason):
        """Reject a pending bank transfer. Refuses payments already processed."""
        payment.refresh_from_db()
        if payment.status not in (
            Payment.Status.PENDING,
            Payment.Status.PENDING_TRANSFER,
        ):
            raise ValueError(
                gettext("El pago #{payment_id} ya fue procesado.").format(
                    payment_id=payment.id
                )
            )
        payment.status = Payment.Status.FAILED
        payment.rejection_reason = reason
        payment.save(update_fields=["status", "rejection_reason", "updated_at"])
        log_event(
            payment.user, "payment.transfer_rejected", "Payment", payment.id,
            after={"rejection_reason": reason},
        )
        NotificationService.notify(
            payment.user,
            "transfer_rejected",
            data={
                "amount": f"${payment.amount}",
                "payment_id": payment.id,
                "reason": reason,
            },
        )
        return payment

    @staticmethod
    def _record_cash_payment(booking, amount, on_arrival=False):
        """Create a cash Payment and notify the player.

        ``on_arrival`` is the client "Pago en el establecimiento" path: the
        payment stays open until staff collects it, the booking is confirmed up
        front and admins get an immediate alert.
        """
        with transaction.atomic():
            payment = Payment.objects.create(
                booking=booking,
                user=booking.user,
                method=Payment.Method.CASH,
                amount=amount,
                currency="USD",
                status=Payment.Status.PENDING if on_arrival else Payment.Status.CAPTURED,
            )
            if on_arrival and booking.status == "pending_payment":
                # If the booking cannot be confirmed (cancelled in a race, say),
                # roll back so there is no orphan Payment row left behind.
                booking.transition_to("confirmed")
        log_event(
            booking.user,
            "payment.cash_on_arrival" if on_arrival else "payment.cash_recorded",
            "Payment",
            payment.id,
        )
        # Tell the player which thing actually happened. Paying at the venue
        # is not a payment yet — only a recorded cash payment is.
        if on_arrival:
            from apps.common.timefmt import fmt_date, fmt_time

            NotificationService.notify(
                booking.user,
                "payment_cash_on_arrival",
                data={
                    "amount": f"${amount}",
                    "court": booking.court.name,
                    "date": fmt_date(booking.date),
                    "time": fmt_time(booking.start_time),
                    "payment_id": payment.id,
                    "booking_id": booking.id,
                },
            )
        else:
            NotificationService.notify(
                booking.user,
                "payment_cash_collected",
                data={"amount": f"${amount}", "payment_id": payment.id},
            )
        if on_arrival:
            from apps.notifications.tasks import notify_admins_task

            notify_admins_task.delay(
                "admin_cash_booking",
                {
                    "user": booking.user.email,
                    "court": booking.court.name,
                    "date": str(booking.date),
                    "time": str(booking.start_time),
                    "amount": f"${amount}",
                    "booking_id": booking.id,
                },
            )
        return payment

    @staticmethod
    def collect_cash(payment):
        """Staff collected the cash for a 'Pago en el establecimiento' booking.

        The client's booking is only really confirmed once this happens, so
        the money and the notification both move here — not at booking time.
        """
        if payment.method != Payment.Method.CASH:
            raise ValueError(gettext("Solo se puede cobrar en efectivo"))
        if payment.status != Payment.Status.PENDING:
            raise ValueError(gettext("Este pago ya fue registrado"))
        with transaction.atomic():
            payment.status = Payment.Status.CAPTURED
            payment.save(update_fields=["status", "updated_at"])
            if payment.booking and payment.booking.status != "confirmed":
                payment.booking.transition_to("confirmed")
        from apps.security.services import log_event

        log_event(payment.user, "payment.cash_collected", "Payment", payment.id)
        from apps.common.timefmt import fmt_date, fmt_time

        NotificationService.notify(
            payment.user,
            "payment_cash_collected",
            data={
                "amount": f"${payment.amount}",
                "court": payment.booking.court.name if payment.booking else "",
                "date": fmt_date(payment.booking.date) if payment.booking else "",
                "time": fmt_time(payment.booking.start_time) if payment.booking else "",
                "payment_id": payment.id,
            },
        )
        return payment

    @staticmethod
    def record_cash(booking, amount):
        """Staff recording cash already collected at the venue."""
        return PaymentService._record_cash_payment(booking, amount, on_arrival=False)

    @staticmethod
    def record_cash_on_arrival(booking, amount):
        """Client chose "Pago en el establecimiento"."""
        return PaymentService._record_cash_payment(booking, amount, on_arrival=True)

    @staticmethod
    def refund(payment, amount):
        """Process a refund. For transfer/cash payments, just mark as refunded.
        For Stripe payments, call the Stripe API first.

        Bounded: refuses non-positive amounts, amounts above what was captured,
        and a second refund of the same payment.
        """
        payment.refresh_from_db()
        if payment.status == Payment.Status.REFUNDED:
            raise ValueError(
                gettext("El pago #{payment_id} ya fue reembolsado.").format(
                    payment_id=payment.id
                )
            )
        try:
            amount = Decimal(str(amount))
            captured = Decimal(str(payment.amount))
        except Exception as err:
            raise ValueError(gettext("Monto de reembolso invalido.")) from err
        if amount <= 0:
            raise ValueError(gettext("El monto del reembolso debe ser mayor que cero."))
        if amount > captured:
            raise ValueError(
                gettext("No se puede reembolsar ${amount} de un pago de ${captured}.").format(
                    amount=amount, captured=captured
                )
            )
        if payment.stripe_payment_intent_id:
            import stripe

            stripe.api_key = secrets.STRIPE_SECRET_KEY
            stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=int(amount * 100),
            )
        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=["status", "updated_at"])
        log_event(payment.user, "payment.refund", "Payment", payment.id)
        NotificationService.notify(
            payment.user,
            "payment_refunded",
            data={"amount": f"${amount}", "payment_id": payment.id},
        )
        return payment
