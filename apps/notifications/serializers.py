from rest_framework import serializers

from apps.notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "event_type", "title", "body", "data", "read_at", "created_at"]
        read_only_fields = fields


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ["event_type", "channel", "enabled"]
