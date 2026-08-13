from rest_framework.routers import DefaultRouter

from apps.events import views

router = DefaultRouter()
router.register("events", views.EventViewSet, basename="event")
router.register("tournaments", views.TournamentViewSet, basename="tournament")
router.register("news", views.NewsPostViewSet, basename="news")

urlpatterns = router.urls
