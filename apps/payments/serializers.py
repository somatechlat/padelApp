from rest_framework import serializers

from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    proof_image_url = serializers.SerializerMethodField()

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
            "proof_image",
            "proof_image_url",
            "rejection_reason",
            "created_at",
        ]
        read_only_fields = ["id", "status", "rejection_reason", "created_at"]

    def get_proof_image_url(self, obj):
        if obj.proof_image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.proof_image.url)
            return obj.proof_image.url
        return None


class RefundSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=8, decimal_places=2)
