from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import translation
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from apps.notifications.models import DeviceToken
from apps.users.serializers import (
    DeviceTokenSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
    VerifySerializer,
)
from apps.verification.models import VerificationCode, VerificationCodeService

User = get_user_model()


def _negotiate_language(request):
    """Map the Accept-Language header to one of the supported language codes."""
    header = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    supported = dict(settings.LANGUAGES)
    for part in header.split(","):
        code = part.split(";")[0].strip().split("-")[0].lower()
        if code in supported:
            return code
    return None


class AuthThrottle(SimpleRateThrottle):
    scope = "auth"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = []
    throttle_classes = [AuthThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            if any("registrado" in str(e) for e in serializer.errors.get("email", [])):
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        lang = _negotiate_language(request)
        if lang and lang != user.language_code:
            user.language_code = lang
            user.save(update_fields=["language_code"])
        code = VerificationCodeService.issue(user, VerificationCode.Purpose.EMAIL_VERIFY)
        with translation.override(user.language_code):
            subject = gettext("Verification code - Andes Padel")
            message = gettext("Your verification code is: {code}").format(code=code.code)
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
        return Response(
            {"email": user.email, "detail": _("Revisa tu email para verificar la cuenta")},
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["_user"]
        ok = VerificationCodeService.verify(
            user, VerificationCode.Purpose.EMAIL_VERIFY, serializer.validated_data["code"]
        )
        if not ok:
            return Response(
                {"detail": _("Codigo invalido o expirado")}, status=status.HTTP_400_BAD_REQUEST
            )
        user.email_verified = True
        user.save(update_fields=["email_verified"])
        return Response({"detail": _("Email verificado")})


class LoginView(APIView):
    permission_classes = []
    throttle_classes = [AuthThrottle]

    def post(self, request):
        from apps.security.services import log_event

        serializer = LoginSerializer(data=request.data)
        ip = request.META.get("REMOTE_ADDR")
        email = request.data.get("email", "")
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            log_event(None, "auth.login_failed", "User", before={"email": email}, ip=ip)
            raise
        log_event(None, "auth.login", "User", email, ip=ip)
        lang = _negotiate_language(request)
        if lang:
            user = serializer.validated_data["_user"]
            if user.language_code != lang:
                user.language_code = lang
                user.save(update_fields=["language_code"])
                serializer.validated_data["user"]["language_code"] = lang
        return Response(serializer.validated_data)


class LogoutView(APIView):
    permission_classes = []

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken

        try:
            token = RefreshToken(request.data.get("refresh"))
            token.blacklist()
        except Exception:
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordResetView(APIView):
    permission_classes = []
    throttle_classes = [AuthThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # No enumeration: respond identically.
            return Response({"detail": _("Si el email existe, recibira un codigo")})
        code = VerificationCodeService.issue(user, VerificationCode.Purpose.PASSWORD_RESET)
        send_mail(
            "Restablecer contrasena - Andes Padel",
            f"Tu codigo de restablecimiento es: {code.code}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
        return Response({"detail": _("Si el email existe, recibira un codigo")})


class PasswordResetConfirmView(APIView):
    permission_classes = []
    throttle_classes = [AuthThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=serializer.validated_data["email"].lower())
        except User.DoesNotExist:
            return Response({"detail": _("Codigo invalido")}, status=status.HTTP_400_BAD_REQUEST)
        ok = VerificationCodeService.verify(
            user, VerificationCode.Purpose.PASSWORD_RESET, serializer.validated_data["code"]
        )
        if not ok:
            return Response(
                {"detail": _("Codigo invalido o expirado")}, status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.validated_data["password"])
        user.save()
        _blacklist_all_user_tokens(user)
        return Response({"detail": _("Contrasena actualizada")})


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.security.services import log_event

        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        _blacklist_all_user_tokens(user)
        log_event(user, "auth.password_change", "User", user.id)
        return Response({"detail": _("Contrasena cambiada")})


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class DeviceView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceTokenSerializer

    def perform_create(self, serializer):
        DeviceToken.objects.filter(
            user=self.request.user, token=serializer.validated_data["token"]
        ).delete()
        serializer.save(user=self.request.user)


def _blacklist_all_user_tokens(user):
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)
