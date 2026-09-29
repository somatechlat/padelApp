from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.events.models import (
    Event,
    NewsPost,
    OpenMatch,
    OpenMatchPlayer,
    Tournament,
    TournamentRegistration,
)
from apps.events.serializers import (
    EventSerializer,
    NewsPostSerializer,
    OpenMatchSerializer,
    TournamentRegistrationSerializer,
    TournamentSerializer,
)
from apps.events.services import TournamentService
from apps.users.permissions import IsStaffRole


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    http_method_names = ["get", "post", "put", "patch", "delete"]

    def get_queryset(self):
        qs = Event.objects.prefetch_related("registrations")
        if not self.request.user or not self.request.user.is_authenticated:
            return qs.none()
        if self.request.user.role not in ("recepcionista", "gerente", "dueno", "superadmin"):
            qs = Event.published.all()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return (IsStaffRole(),)
        return (IsAuthenticated(),)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        """RSVP 'Me apunto' — EventRegistration row, visible in admin."""
        from apps.events.models import EventRegistration

        event = self.get_object()
        if not event.allow_registration:
            return Response(
                {"detail": _("Este evento no acepta inscripciones")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if event.status != Event.Status.PUBLISHED:
            return Response(
                {"detail": _("El evento no esta publicado")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if event.is_full:
            return Response(
                {"detail": _("El evento esta completo")},
                status=status.HTTP_409_CONFLICT,
            )
        reg, created = EventRegistration.objects.get_or_create(
            event=event,
            user=request.user,
            defaults={"status": EventRegistration.Status.GOING},
        )
        if not created and reg.status != EventRegistration.Status.GOING:
            reg.status = EventRegistration.Status.GOING
            reg.save(update_fields=["status"])
        if created:
            from apps.notifications.tasks import notify_task

            notify_task.delay(
                request.user.id,
                "event_registered",
                "",
                "",
                {"title": event.title_localized, "event_id": event.id},
            )
        return Response(self.get_serializer(event).data)

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        """Cancel RSVP 'No voy'."""
        from apps.events.models import EventRegistration

        event = self.get_object()
        EventRegistration.objects.filter(event=event, user=request.user).update(
            status=EventRegistration.Status.CANCELLED
        )
        return Response(self.get_serializer(event).data)


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
        return (IsAuthenticated(),)

    @action(detail=True, methods=["post"])
    def register(self, request, pk=None):
        tournament = self.get_object()
        tournament.close_if_deadline_passed()
        try:
            reg = TournamentService.register(
                request.user, tournament, partner_name=request.data.get("partner_name", "")
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
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
                {"detail": _("Inscripcion no encontrada")}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(TournamentRegistrationSerializer(reg).data)


class OpenMatchViewSet(viewsets.ModelViewSet):
    """Armar partidos: clients create open matches and join them."""

    serializer_class = OpenMatchSerializer
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        qs = OpenMatch.objects.select_related(
            "created_by", "skill_level"
        ).prefetch_related("players")
        if not self.request.user or not self.request.user.is_authenticated:
            return qs.none()
        category = self.request.query_params.get("skill_level")
        if category:
            qs = qs.filter(skill_level_id=category)
        mine = self.request.query_params.get("mine")
        if mine in ("1", "true"):
            qs = qs.filter(players__user=self.request.user)
        return qs

    def get_permissions(self):
        return (IsAuthenticated(),)

    def perform_create(self, serializer):
        match = serializer.save(created_by=self.request.user)
        OpenMatchPlayer.objects.get_or_create(match=match, user=self.request.user)
        match.notify_category()

    def perform_destroy(self, instance):
        instance.status = instance.Status.CANCELLED
        instance.save(update_fields=["status"])

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        match = self.get_object()
        if match.status != OpenMatch.Status.OPEN:
            return Response(
                {"detail": _("El partido ya no esta abierto")},
                status=status.HTTP_409_CONFLICT,
            )
        if match.players.count() >= match.max_players:
            match.status = OpenMatch.Status.FULL
            match.save(update_fields=["status"])
            return Response(
                {"detail": _("El partido ya esta completo")},
                status=status.HTTP_409_CONFLICT,
            )
        _player, created = OpenMatchPlayer.objects.get_or_create(
            match=match, user=request.user
        )
        if not created:
            return Response(
                {"detail": _("Ya estas en este partido")},
                status=status.HTTP_409_CONFLICT,
            )
        if match.players.count() >= match.max_players:
            match.status = OpenMatch.Status.FULL
            match.save(update_fields=["status"])
        serializer = self.get_serializer(match)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        match = self.get_object()
        OpenMatchPlayer.objects.filter(match=match, user=request.user).delete()
        if match.status == OpenMatch.Status.FULL and match.players.count() < match.max_players:
            match.status = OpenMatch.Status.OPEN
            match.save(update_fields=["status"])
        return Response(self.get_serializer(match).data)


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
