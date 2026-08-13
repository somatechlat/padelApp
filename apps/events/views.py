from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.events.models import (
    Event,
    NewsPost,
    Tournament,
    TournamentRegistration,
)
from apps.events.serializers import (
    EventSerializer,
    NewsPostSerializer,
    TournamentRegistrationSerializer,
    TournamentSerializer,
)
from apps.events.services import TournamentService
from apps.users.permissions import IsStaffRole


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    http_method_names = ["get", "post", "put", "patch", "delete"]

    def get_queryset(self):
        qs = Event.objects.all()
        if not self.request.user or not self.request.user.is_authenticated:
            return qs.none()
        if self.request.user.role in ("recepcionista", "gerente", "dueno", "superadmin"):
            return qs
        return Event.published.all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return (IsStaffRole(),)
        return (IsAuthenticated(),)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TournamentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TournamentSerializer

    def get_queryset(self):
        qs = Tournament.objects.all()
        if not self.request.user or not self.request.user.is_authenticated:
            return qs.none()
        if self.request.user.role in ("recepcionista", "gerente", "dueno", "superadmin"):
            return qs
        return qs.filter(status__in=(Tournament.Status.OPEN, Tournament.Status.IN_PROGRESS))

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return (IsStaffRole(),)
        return (IsAuthenticated(),)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def register(self, request, pk=None):
        tournament = self.get_object()
        tournament.close_if_deadline_passed()
        try:
            reg = TournamentService.register(request.user, tournament)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        from apps.notifications.services import NotificationService

        NotificationService.notify(
            request.user,
            "tournament_registered",
            "Inscripcion registrada",
            f"Te inscribiste en {tournament.name_localized}. Completa el pago para confirmar.",
        )
        return Response(
            TournamentRegistrationSerializer(reg).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        tournament = self.get_object()
        try:
            reg = TournamentRegistration.objects.get(
                tournament=tournament, user=request.user
            )
            TournamentService.confirm(reg)
        except TournamentRegistration.DoesNotExist:
            return Response(
                {"detail": "Inscripcion no encontrada"}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(TournamentRegistrationSerializer(reg).data)


class NewsPostViewSet(viewsets.ModelViewSet):
    serializer_class = NewsPostSerializer
    http_method_names = ["get", "post", "put", "patch", "delete"]

    def get_queryset(self):
        qs = NewsPost.objects.all()
        if not self.request.user or not self.request.user.is_authenticated:
            return qs.none()
        if self.request.user.role in ("recepcionista", "gerente", "dueno", "superadmin"):
            return qs
        return qs.filter(status=NewsPost.Status.PUBLISHED)

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return (IsStaffRole(),)
        return (IsAuthenticated(),)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
