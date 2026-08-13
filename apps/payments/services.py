from decimal import Decimal

from apps.payments.models import Payment
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
        return payment

    @staticmethod
    def record_transfer(booking, reference):
        return Payment.objects.create(
            booking=booking,
            user=booking.user,
            method=Payment.Method.TRANSFER,
            amount=booking.price,
            currency="USD",
            status=Payment.Status.PENDING_TRANSFER,
            reference=reference,
        )

    @staticmethod
    def confirm_transfer(payment):
        payment.status = Payment.Status.CAPTURED
        payment.save(update_fields=["status", "updated_at"])
        return payment

    @staticmethod
    def record_cash(booking, amount):
        return Payment.objects.create(
            booking=booking,
            user=booking.user,
            method=Payment.Method.CASH,
            amount=amount,
            currency="USD",
            status=Payment.Status.CAPTURED,
        )

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
        return payment
