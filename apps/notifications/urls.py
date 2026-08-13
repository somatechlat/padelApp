from django.urls import path

from apps.notifications.views import (
    NotificationListView,
    NotificationReadView,
    PreferenceListView,
)

app_name = "notifications"

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/<int:pk>/read/", NotificationReadView.as_view(), name="notification-read"),
    path("notifications/preferences/", PreferenceListView.as_view(), name="preferences"),
]
