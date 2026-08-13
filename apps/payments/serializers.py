from rest_framework import serializers

from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "method",
            "amount",
            "currency",
            "status",
            "reference",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


class RefundSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=8, decimal_places=2)
