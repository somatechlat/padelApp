from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.gdpr.services import erase_user, export_user_data, record_consent
from apps.users.views import _blacklist_all_user_tokens


class ConsentSerializer(serializers.Serializer):
    version = serializers.CharField(max_length=16)
    granted = serializers.BooleanField()
    source = serializers.CharField(max_length=32, default="app", required=False)


class ConsentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ConsentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record_consent(
            request.user,
            serializer.validated_data["version"],
            serializer.validated_data["granted"],
            serializer.validated_data.get("source", "app"),
        )
        return Response({"detail": _("Consentimiento registrado")}, status=status.HTTP_201_CREATED)


class ExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(export_user_data(request.user))


class EraseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        _blacklist_all_user_tokens(request.user)
        ip = request.META.get("REMOTE_ADDR")
        erase_user(request.user, ip=ip)
        return Response(
            {"detail": _("Tus datos fueron anonimizados (derecho al olvido)")}
        )
