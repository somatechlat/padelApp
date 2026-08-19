
from apps.notifications.services import NotificationService
from apps.payments.models import Payment
from apps.security.services import log_event
from runsecrets import secrets

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
    def record_cash(booking, amount):
        payment = Payment.objects.create(
            booking=booking,
            user=booking.user,
            method=Payment.Method.CASH,
            amount=amount,
            currency="USD",
            status=Payment.Status.CAPTURED,
        )
        log_event(booking.user, "payment.cash_recorded", "Payment", payment.id)
        return payment

    @staticmethod
    def refund(payment, amount):
        if payment.stripe_payment_intent_id:
            try:
                import stripe

                stripe.api_key = secrets.STRIPE_SECRET_KEY
                stripe.Refund.create(
                    payment_intent=payment.stripe_payment_intent_id,
                    amount=int(amount * 100),
                )
            except Exception:
                pass
        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=["status", "updated_at"])
        log_event(payment.user, "payment.refund", "Payment", payment.id)
        NotificationService.notify(
            payment.user,
            "payment_refunded",
            data={"amount": f"${amount}", "payment_id": payment.id},
        )
        return payment
