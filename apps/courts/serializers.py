from rest_framework import serializers

from apps.courts.models import Court, CourtSchedule, Venue


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ["id", "name", "address", "timezone", "currency", "active"]


class CourtSerializer(serializers.ModelSerializer):
    venue = serializers.PrimaryKeyRelatedField(queryset=Venue.objects.all())

    class Meta:
        model = Court
        fields = [
            "id",
            "venue",
            "name",
            "court_type",
            "has_lighting",
            "price_base",
            "status",
        ]
        read_only_fields = ["id"]


class CourtScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourtSchedule
        fields = ["id", "court", "weekday", "open_time", "close_time", "is_active"]
        read_only_fields = ["id"]


class TimeSlotSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start = serializers.TimeField()
    end = serializers.TimeField()
    status = serializers.CharField()
