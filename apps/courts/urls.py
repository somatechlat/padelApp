from rest_framework.routers import DefaultRouter

from apps.courts.views import CourtViewSet

router = DefaultRouter()
router.register("courts", CourtViewSet, basename="court")

urlpatterns = router.urls
