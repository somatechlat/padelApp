import logging

from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView

from apps.courts.lang import resolve_request_lang
from apps.notifications.models import DeviceToken
from apps.users.emails import (
    from_email,
    make_token,
    password_reset_email_html,
    password_reset_form_html,
    read_token,
    success_page_html,
    verification_email_html,
    verify_confirm_form_html,
)
from apps.users.models import SkillLevel
from apps.users.serializers import (
    DeviceTokenSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    SkillLevelSerializer,
    UserSerializer,
    VerifySerializer,
)
from apps.verification.models import VerificationCode, VerificationCodeService

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthThrottle(SimpleRateThrottle):
    scope = "auth"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class SkillLevelListView(generics.ListAPIView):
    """Public combo-box options for 'Nivel de juego' (editable in admin)."""

    serializer_class = SkillLevelSerializer
    permission_classes: list = []

    def get_queryset(self):
        return SkillLevel.objects.filter(is_active=True)


def _send_html_mail(subject: str, text_body: str, html_body: str, to: str) -> None:
    msg = EmailMultiAlternatives(subject, text_body, from_email(), [to])
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


def _send_verification_email(user, code) -> None:
    token = make_token(user.id, code.code, VerificationCode.Purpose.EMAIL_VERIFY)
    subject, html = verification_email_html(user, code.code, token)
    text = (
        f"Hola {user.first_name or 'jugador'},\n\n"
        f"Tu código de verificación es: {code.code}\n\n"
        "O usa el enlace de un clic del correo HTML para activar tu cuenta.\n\n"
        "Andes Pádel"
    )
    _send_html_mail(subject, text, html, user.email)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes: list = []
    throttle_classes = [AuthThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            if any("registrado" in str(e) for e in serializer.errors.get("email", [])):
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        # Seed from Accept-Language once at registration only. After that the
        # in-app language picker is the single source of truth (login no longer
        # overwrites it).
        lang = resolve_request_lang(request, default=None)
        if lang and lang != user.language_code:
            user.language_code = lang
            user.save(update_fields=["language_code"])
        code = VerificationCodeService.issue(user, VerificationCode.Purpose.EMAIL_VERIFY)
        try:
            _send_verification_email(user, code)
        except Exception:
            logger.exception("Failed to send verification email to %s", user.email)
        return Response(
            {"email": user.email, "detail": _("Revisa tu email para verificar la cuenta")},
            status=status.HTTP_201_CREATED,
        )


class ResendVerificationView(APIView):
    """Re-issue the code + one-click link. No auth; no user enumeration."""

    permission_classes: list = []
    throttle_classes = [AuthThrottle]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        if email:
            user = User.objects.filter(email=email).first()
            if user and not user.email_verified:
                code = VerificationCodeService.issue(user, VerificationCode.Purpose.EMAIL_VERIFY)
                try:
                    _send_verification_email(user, code)
                except Exception:
                    logger.exception("Failed to resend verification email to %s", user.email)
        return Response({"detail": _("Revisa tu email para verificar la cuenta")})


class VerifyLinkView(APIView):
    """Email link flow. GET only renders a confirm form; POST performs the
    verification. Mail scanners that prefetch links cannot auto-verify."""

    permission_classes: list = []
    authentication_classes: list = []
    throttle_classes = [AuthThrottle]

    def get(self, request):
        from django.http import HttpResponse

        token = request.query_params.get("token", "")
        data = read_token(token, VerificationCode.Purpose.EMAIL_VERIFY)
        if not data:
            return HttpResponse(
                success_page_html(
                    "Enlace no válido",
                    "El enlace de verificación no es válido o ya expiró. Solicita uno nuevo desde la app.",
                ),
                status=400,
                content_type="text/html; charset=utf-8",
            )
        return HttpResponse(
            verify_confirm_form_html(token),
            content_type="text/html; charset=utf-8",
        )

    def post(self, request):
        from django.http import HttpResponse

        token = request.POST.get("token", "")
        data = read_token(token, VerificationCode.Purpose.EMAIL_VERIFY)
        if not data:
            return HttpResponse(
                success_page_html(
                    "Enlace no válido",
                    "El enlace de verificación no es válido o ya expiró. Solicita uno nuevo desde la app.",
                ),
                status=400,
                content_type="text/html; charset=utf-8",
            )
        user = User.objects.filter(id=data.get("u")).first()
        if not user:
            return HttpResponse(
                success_page_html(
                    "Cuenta no encontrada",
                    "No encontramos una cuenta asociada a este enlace.",
                ),
                status=404,
                content_type="text/html; charset=utf-8",
            )
        ok = VerificationCodeService.verify(
            user, VerificationCode.Purpose.EMAIL_VERIFY, data.get("c", "")
        )
        if not ok and not user.email_verified:
            return HttpResponse(
                success_page_html(
                    "Enlace expirado",
                    "Este enlace ya se usó o expiró. Si aún no verificaste, solicita otro código en la app.",
                ),
                status=400,
                content_type="text/html; charset=utf-8",
            )
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])
        return HttpResponse(
            success_page_html(
                "¡Cuenta verificada!",
                "Tu correo quedó confirmado. Ya puedes iniciar sesión en Andes Pádel y reservar tu cancha.",
            ),
            content_type="text/html; charset=utf-8",
        )


class PasswordResetLinkPageView(APIView):
    """GET: form to type a new password. POST: actually change it. No mocks."""

    permission_classes: list = []
    authentication_classes: list = []
    throttle_classes = [AuthThrottle]

    def get(self, request):
        from django.http import HttpResponse

        token = request.query_params.get("token", "")
        data = read_token(token, VerificationCode.Purpose.PASSWORD_RESET)
        if not data:
            return HttpResponse(
                success_page_html(
                    "Enlace no válido",
                    "El enlace de restablecimiento no es válido o expiró. Solicita uno nuevo desde la app.",
                ),
                status=400,
                content_type="text/html; charset=utf-8",
            )
        return HttpResponse(
            password_reset_form_html(token),
            content_type="text/html; charset=utf-8",
        )

    def post(self, request):
        from django.contrib.auth import password_validation
        from django.http import HttpResponse

        token = request.POST.get("token", "")
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        data = read_token(token, VerificationCode.Purpose.PASSWORD_RESET)
        if not data:
            return HttpResponse(
                success_page_html(
                    "Enlace no válido",
                    "El enlace de restablecimiento no es válido o expiró.",
                ),
                status=400,
                content_type="text/html; charset=utf-8",
            )
        user = User.objects.filter(id=data.get("u")).first()
        if not user:
            return HttpResponse(
                success_page_html("Cuenta no encontrada", "No hay cuenta asociada a este enlace."),
                status=404,
                content_type="text/html; charset=utf-8",
            )
        if password != password2:
            return HttpResponse(
                password_reset_form_html(token, "Las contraseñas no coinciden."),
                status=400,
                content_type="text/html; charset=utf-8",
            )
        try:
            password_validation.validate_password(password, user=user)
        except Exception as exc:
            msg = " ".join(str(e) for e in getattr(exc, "messages", [str(exc)]))
            return HttpResponse(
                password_reset_form_html(token, msg),
                status=400,
                content_type="text/html; charset=utf-8",
            )
        ok = VerificationCodeService.verify(
            user, VerificationCode.Purpose.PASSWORD_RESET, data.get("c", "")
        )
        if not ok:
            return HttpResponse(
                success_page_html(
                    "Enlace expirado",
                    "Este enlace ya se usó o expiró. Solicita un código nuevo en la app.",
                ),
                status=400,
                content_type="text/html; charset=utf-8",
            )
        user.set_password(password)
        user.save()
        _blacklist_all_user_tokens(user)
        return HttpResponse(
            success_page_html(
                "¡Contraseña actualizada!",
                "Tu contraseña se cambió correctamente. Ya puedes iniciar sesión en Andes Pádel con la nueva contraseña.",
            ),
            content_type="text/html; charset=utf-8",
        )


class VerifyEmailView(APIView):
    permission_classes: list = []
    throttle_classes = [AuthThrottle]

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
    permission_classes: list = []
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
        # Do NOT rewrite language_code from Accept-Language on login. The
        # in-app picker owns the language; following the device locale here
        # flipped whole accounts (and the app UI) to Portuguese unprompted.
        return Response(serializer.validated_data)


class LogoutView(APIView):
    permission_classes: list = []

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken

        try:
            token = RefreshToken(request.data.get("refresh"))
            token.blacklist()
        except Exception:
            logger.warning("Failed to blacklist refresh token on logout", exc_info=True)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordResetView(APIView):
    permission_classes: list = []
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
        try:
            token = make_token(user.id, code.code, VerificationCode.Purpose.PASSWORD_RESET)
            subject, html = password_reset_email_html(user, code.code, token)
            text = (
                f"Hola {user.first_name or 'jugador'},\n\n"
                f"Tu código de restablecimiento es: {code.code}\n\n"
                "O usa el enlace del correo HTML para crear una contraseña nueva.\n\n"
                "Andes Pádel"
            )
            _send_html_mail(subject, text, html, user.email)
        except Exception:
            logger.exception("Failed to send password reset email to %s", user.email)
        return Response({"detail": _("Si el email existe, recibira un codigo")})


class PasswordResetConfirmView(APIView):
    permission_classes: list = []
    throttle_classes = [AuthThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=serializer.validated_data["email"].lower())
        except User.DoesNotExist:
            return Response({"detail": _("Codigo invalido")}, status=status.HTTP_400_BAD_REQUEST)
        if user.status != "active":
            # Suspended/blocked/deleted accounts must not regain access by
            # resetting the password. Same message as invalid code: no
            # enumeration, no hint that the account exists.
            return Response(
                {"detail": _("Codigo invalido o expirado")}, status=status.HTTP_400_BAD_REQUEST
            )
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
