from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.courts.views import ClubInfoView, CourtViewSet, PromoBannerListView

router = DefaultRouter()
router.register("courts", CourtViewSet, basename="court")

urlpatterns = [
    path("club/", ClubInfoView.as_view(), name="club-info"),
    path("banners/", PromoBannerListView.as_view(), name="promo-banners"),
    *router.urls,
]
