from django.urls import path

from apps.adminpanel import views

app_name = "adminpanel"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("calendar/", views.CalendarView.as_view(), name="calendar"),
    path("audit/", views.AuditListView.as_view(), name="audit"),
]
