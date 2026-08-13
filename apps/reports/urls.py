from django.urls import path

from apps.reports import views

app_name = "reports"

urlpatterns = [
    path("reports/revenue/", views.RevenueReportView.as_view(), name="revenue"),
    path("reports/occupancy/", views.OccupancyReportView.as_view(), name="occupancy"),
    path("reports/customers/", views.CustomersReportView.as_view(), name="customers"),
    path("reports/cancellations/", views.CancellationReportView.as_view(), name="cancellations"),
]
