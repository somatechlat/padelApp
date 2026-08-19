from django.urls import path

from apps.adminpanel import views

app_name = "adminpanel"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="index"),
    path("login/", views.AdminLoginView.as_view(), name="login"),
    path("logout/", views.AdminLogoutView.as_view(), name="logout"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("calendar/", views.CalendarView.as_view(), name="calendar"),
    path("courts/", views.CourtsAdminView.as_view(), name="courts"),
    path("users/", views.UsersAdminView.as_view(), name="users"),
    path("payments/", views.PaymentsAdminView.as_view(), name="payments"),
    path("events/", views.EventsAdminView.as_view(), name="events"),
    path("reports/", views.ReportsAdminView.as_view(), name="reports"),
    path("settings/", views.SettingsAdminView.as_view(), name="settings"),
    path("audit/", views.AuditListView.as_view(), name="audit"),
]


