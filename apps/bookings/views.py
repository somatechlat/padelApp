from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.bookings.models import Booking
from apps.bookings.serializers import (
    BookingCreateSerializer,
    BookingPreviewSerializer,
    BookingSerializer,
)
from apps.bookings.services import BookingService
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
