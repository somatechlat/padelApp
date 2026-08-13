from django.urls import path

from apps.gdpr import views

app_name = "gdpr"

urlpatterns = [
    path("me/consent/", views.ConsentView.as_view(), name="consent"),
    path("me/export/", views.ExportView.as_view(), name="export"),
    path("me/erase/", views.EraseView.as_view(), name="erase"),
]
