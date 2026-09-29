from rest_framework import serializers

from apps.events.models import (
    Event,
    EventRegistration,
    NewsPost,
    OpenMatch,
    Tournament,
    TournamentRegistration,
)


class EventSerializer(serializers.ModelSerializer):
    title_localized = serializers.CharField(read_only=True)
    description_localized = serializers.CharField(read_only=True)
    attendee_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    joined = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "id", "title", "title_es", "title_localized",
            "description", "description_es", "description_localized",
            "start_at", "end_at", "location", "category", "status",
            "capacity", "allow_registration", "attendee_count", "is_full", "joined",
            "created_at",
        )
        read_only_fields = ("created_at",)

    def get_joined(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.registrations.filter(
            user=request.user, status=EventRegistration.Status.GOING
        ).exists()


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
        fields = ("id", "tournament", "partner_name", "status", "created_at")
        read_only_fields = ("status", "created_at")


class OpenMatchSerializer(serializers.ModelSerializer):
    players_count = serializers.IntegerField(read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    skill_level_name = serializers.CharField(source="skill_level.name", read_only=True, default=None)
    joined = serializers.SerializerMethodField()

    class Meta:
        model = OpenMatch
        fields = (
            "id", "created_by", "created_by_name", "skill_level", "skill_level_name",
            "date", "start_time", "duration_minutes", "max_players", "notes",
            "status", "players_count", "joined", "created_at",
        )
        read_only_fields = ("created_by", "status", "created_at")

    def get_joined(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.players.filter(user=request.user).exists()
