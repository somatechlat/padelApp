from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.serializers import (
    NotificationSerializer,
    PreferenceSerializer,
)


class NotificationListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_read()
        return Response(NotificationSerializer(notification).data)


class PreferenceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefs = NotificationPreference.objects.filter(user=request.user)
        return Response(PreferenceSerializer(prefs, many=True).data)

    def put(self, request):
        serializer = PreferenceSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        NotificationPreference.objects.filter(user=request.user).delete()
        for item in serializer.validated_data:
            NotificationPreference.objects.create(
                user=request.user,
                event_type=item["event_type"],
                channel=item["channel"],
                enabled=item["enabled"],
            )
        prefs = NotificationPreference.objects.filter(user=request.user)
        return Response(PreferenceSerializer(prefs, many=True).data)
