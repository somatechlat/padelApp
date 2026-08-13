from rest_framework import serializers

from apps.events.models import Event, NewsPost, Tournament, TournamentRegistration


class EventSerializer(serializers.ModelSerializer):
    title_localized = serializers.CharField(read_only=True)
    description_localized = serializers.CharField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "id", "title", "title_es", "title_localized",
            "description", "description_es", "description_localized",
            "start_at", "end_at", "location", "status", "created_at",
        )
        read_only_fields = ("created_at",)


class NewsPostSerializer(serializers.ModelSerializer):
    title_localized = serializers.CharField(read_only=True)
    body_localized = serializers.CharField(read_only=True)

    class Meta:
        model = NewsPost
        fields = (
            "id", "title", "title_es", "title_localized",
            "body", "body_es", "body_localized", "status", "published_at", "created_at",
        )
        read_only_fields = ("published_at", "created_at")


class TournamentSerializer(serializers.ModelSerializer):
    name_localized = serializers.CharField(read_only=True)
    confirmed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tournament
        fields = (
            "id", "name", "name_es", "name_localized", "description", "description_es",
            "start_date", "end_date", "capacity", "price", "registration_deadline",
            "status", "confirmed_count", "created_at",
        )
        read_only_fields = ("created_at",)


class TournamentRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentRegistration
        fields = ("id", "tournament", "status", "created_at")
        read_only_fields = ("status", "created_at")
