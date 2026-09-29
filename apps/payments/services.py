import logging

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
        payment = Payment.objects.create(
            booking=booking,
            user=booking.user,
            method=Payment.Method.CASH,
            amount=amount,
            currency="USD",
            status=Payment.Status.PENDING if on_arrival else Payment.Status.CAPTURED,
        )
        log_event(
            booking.user,
            "payment.cash_on_arrival" if on_arrival else "payment.cash_recorded",
            "Payment",
            payment.id,
        )
        if on_arrival and booking.status == "pending_payment":
            try:
                booking.transition_to("confirmed")
            except ValueError:
                logger.exception(
                    "Failed to confirm booking %s after cash-on-arrival payment %s",
                    booking.id,
                    payment.id,
                )
                raise
        NotificationService.notify(
            booking.user,
            "payment_success",
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
        For Stripe payments, call the Stripe API first."""
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
