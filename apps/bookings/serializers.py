from rest_framework import serializers

from apps.bookings.models import Booking
from apps.bookings.services import BookingService


class BookingCreateSerializer(serializers.Serializer):
    court = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    duration_minutes = serializers.IntegerField(min_value=30, max_value=240)
    players = serializers.IntegerField(min_value=1, max_value=8, default=4)

    def create(self, validated_data):
        from apps.courts.models import Court

        try:
            court = Court.objects.get(pk=validated_data["court"], status="active")
        except Court.DoesNotExist:
            raise serializers.ValidationError({"court": "Cancha no encontrada o inactiva"})
        user = self.context["request"].user
        return BookingService.hold(
            user,
            court,
            validated_data["date"],
            validated_data["start_time"],
            validated_data["duration_minutes"],
            validated_data.get("players", 4),
        )


class BookingPreviewSerializer(serializers.Serializer):
    court = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    duration_minutes = serializers.IntegerField(min_value=30, max_value=240)
    price = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    def validate(self, attrs):
        from apps.courts.models import Court

        try:
            court = Court.objects.get(pk=attrs["court"], status="active")
        except Court.DoesNotExist:
            raise serializers.ValidationError({"court": "Cancha no encontrada o inactiva"})
        attrs["_price"] = BookingService.preview(
            court, attrs["date"], attrs["start_time"], attrs["duration_minutes"]
        )
        return attrs


class BookingSerializer(serializers.ModelSerializer):
    court = serializers.CharField(source="court.name", read_only=True)
    court_id = serializers.IntegerField(source="court.id", read_only=True)
    slots = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "user",
            "court",
            "court_id",
            "date",
            "start_time",
            "end_time",
            "duration_minutes",
            "players",
            "price",
            "status",
            "slots",
            "created_at",
        ]
        read_only_fields = fields

    def get_slots(self, obj):
        return [
            {"start": bs.slot.start.strftime("%H:%M"), "status": bs.slot.status}
            for bs in obj.slots.select_related("slot").all()
        ]
