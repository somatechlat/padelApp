from datetime import date as date_type
from datetime import timedelta

from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.bookings.models import Booking
from apps.bookings.serializers import (
    BookingCreateSerializer,
    BookingPreviewSerializer,
    BookingSerializer,
)
from apps.bookings.services import SLOT_MINUTES, BookingService
from apps.users.permissions import IsOwnerOrStaff


class BookingViewSet(
    GenericViewSet, CreateModelMixin, ListModelMixin, RetrieveModelMixin
):
    serializer_class = BookingSerializer

    def get_queryset(self):
        qs = Booking.objects.select_related("court").prefetch_related("slots__slot")
        user = self.request.user
        if user.role in ("recepcionista", "gerente", "dueno", "superadmin"):
            return qs.all()
        return qs.filter(user=user)

    def get_permissions(self):
        if self.action in ("available_starts",):
            return [AllowAny()]
        return [IsOwnerOrStaff()]

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        if self.action == "preview":
            return BookingPreviewSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = serializer.save()
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def preview(self, request):
        serializer = BookingPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"price": str(serializer.validated_data["_price"])})

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        try:
            BookingService.confirm(booking)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        booking.refresh_from_db()
        return Response(BookingSerializer(booking).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        try:
            BookingService.cancel(booking)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        booking.refresh_from_db()
        return Response(BookingSerializer(booking).data)

    @action(
        detail=False,
        methods=["get"],
        url_path="available-starts",
        permission_classes=[AllowAny],
    )
    def available_starts(self, request):
        """Real free start times for `date` + `duration_minutes`.

        Computed from TimeSlot occupancy (booked/held/maintenance filtered out)
        across every active court. Never a hardcoded grid.
        """
        from apps.common.timefmt import fmt_time
        from apps.courts.models import Court
        from apps.scheduling.services import SlotService

        date_str = request.query_params.get("date")
        duration_raw = request.query_params.get("duration_minutes", "90")
        if not date_str:
            return Response({"detail": _("El parametro 'date' es obligatorio")}, status=400)
        try:
            day = date_type.fromisoformat(date_str)
            duration = int(duration_raw)
        except (ValueError, TypeError):
            return Response({"detail": _("Parametros invalidos")}, status=400)
        if duration < 30 or duration > 240 or duration % SLOT_MINUTES != 0:
            return Response({"detail": _("Duracion invalida")}, status=400)

        needed = duration // SLOT_MINUTES
        courts = Court.objects.filter(status=Court.Status.ACTIVE)
        free_counts: dict[str, int] = {}
        for court in courts:
            SlotService.generate_day(court, day)
            free = {
                fmt_time(s.start)
                for s in SlotService.available_slots(court, day)
            }
            # Walk every possible start in 30-min steps that fits `needed` free slots.
            for start_s in sorted(free):
                hh, mm = map(int, start_s.split(":"))
                start_dt = timezone_datetime_combine(day, hh, mm)
                ok = True
                for i in range(needed):
                    t = (start_dt + timedelta(minutes=SLOT_MINUTES * i)).strftime("%H:%M")
                    if t not in free:
                        ok = False
                        break
                if ok:
                    free_counts[start_s] = free_counts.get(start_s, 0) + 1

        starts = [
            {"start": s, "courts_free": n}
            for s, n in sorted(free_counts.items())
            if n > 0
        ]
        return Response({"date": date_str, "duration_minutes": duration, "starts": starts})


def timezone_datetime_combine(day, hour, minute):
    from django.utils import timezone as tz

    return tz.datetime.combine(day, tz.datetime.min.time().replace(hour=hour, minute=minute))
