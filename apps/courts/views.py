from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.courts.lang import resolve_request_lang
from apps.courts.models import Court, PromoBanner, Venue
from apps.courts.serializers import (
    ClubInfoSerializer,
    CourtSerializer,
    PromoBannerSerializer,
    TimeSlotSerializer,
)
from apps.scheduling.services import SlotService
from apps.users.permissions import IsStaffRole


class ClubInfoView(generics.RetrieveAPIView):
    """Public club profile: contact, maps, bank transfer data and home titles."""

    permission_classes = [AllowAny]
    serializer_class = ClubInfoSerializer

    def get_object(self):
        return Venue.objects.first()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response(
                {
                    "id": None,
                    "name": "",
                    "address": "",
                    "maps_query": "",
                    "maps_url": "",
                    "phone": "",
                    "email": "",
                    "whatsapp_number": "",
                    "whatsapp_message": "",
                    "instagram_url": "",
                    "logo_url": "",
                    "home_section_title": "",
                    "home_greeting_tagline": "",
                    "home_section_title_i18n": {},
                    "home_greeting_tagline_i18n": {},
                    "bank_name": "",
                    "bank_account_number": "",
                    "bank_account_holder": "",
                    "bank_account_code": "",
                    "bank_extra": "",
                    "timezone": "",
                    "currency": "USD",
                }
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["lang"] = resolve_request_lang(self.request)
        return ctx


class PromoBannerListView(generics.ListAPIView):
    """Public active promo banners currently inside their display window."""

    permission_classes = [AllowAny]
    serializer_class = PromoBannerSerializer
    pagination_class = None

    def get_queryset(self):
        now = timezone.now()
        return (
            PromoBanner.objects.filter(active=True)
            .filter(Q(starts_at__isnull=True) | Q(starts_at__lte=now))
            .filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now))
            .order_by("sort_order", "-created_at")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["lang"] = resolve_request_lang(self.request)
        return ctx


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
            return Response({"detail": _("El parametro 'date' es obligatorio")}, status=400)
        from datetime import date as date_type

        try:
            day = date_type.fromisoformat(date_str)
        except (ValueError, TypeError):
            return Response({"detail": _("Formato de fecha invalido. Use YYYY-MM-DD.")}, status=400)
        SlotService.generate_day(court, day)
        slots = SlotService.available_slots(court, day)
        return Response(TimeSlotSerializer(slots, many=True).data)
