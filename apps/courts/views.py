from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.courts.models import Court
from apps.courts.serializers import CourtSerializer, TimeSlotSerializer
from apps.scheduling.services import SlotService
from apps.users.permissions import IsStaffRole


class CourtViewSet(viewsets.ModelViewSet):
    queryset = Court.objects.select_related("venue").order_by("name")
    serializer_class = CourtSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsStaffRole()]
        return [AllowAny()]

    def destroy(self, request, *args, **kwargs):
        court = self.get_object()
        court.status = Court.Status.ARCHIVED
        court.save(update_fields=["status"])
        return Response(status=204)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def availability(self, request, pk=None):
        court = get_object_or_404(Court, pk=pk)
        date_str = request.query_params.get("date")
        if not date_str:
            return Response({"detail": "El parametro 'date' es obligatorio"}, status=400)
        from datetime import date as date_type

        day = date_type.fromisoformat(date_str)
        SlotService.generate_day(court, day)
        slots = SlotService.available_slots(court, day)
        return Response(TimeSlotSerializer(slots, many=True).data)
