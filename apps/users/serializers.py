from django.contrib.auth import authenticate, get_user_model, password_validation
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.notifications.models import DeviceToken
from apps.users.models import SkillLevel

User = get_user_model()


class SkillLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillLevel
        fields = ["id", "name", "order", "is_active"]
        read_only_fields = ["id"]


class RegisterSerializer(serializers.Serializer):
    """Account creation form: Nombre, Apellido, Correo, Clave,
    Fecha de nacimiento, Nivel de juego (categoría)."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=60)
    last_name = serializers.CharField(max_length=60)
    birth_date = serializers.DateField(required=False, allow_null=True)
    skill_level = serializers.PrimaryKeyRelatedField(
        queryset=SkillLevel.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    consent_version = serializers.CharField()

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(_("El email ya esta registrado"))
        return value.lower()

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_consent_version(self, value):
        if not value:
            raise serializers.ValidationError(_("Debes aceptar los terminos"))
        return value

    def create(self, validated_data):
        first = validated_data["first_name"].strip()
        last = validated_data["last_name"].strip()
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first,
            last_name=last,
            full_name=f"{first} {last}".strip(),
            birth_date=validated_data.get("birth_date"),
            skill_level=validated_data.get("skill_level"),
            phone=validated_data.get("phone", ""),
            consent_version=validated_data["consent_version"],
        )
        from django.utils import timezone

        user.consent_ts = timezone.now()
        user.save(
            update_fields=["consent_ts", "full_name", "first_name", "last_name", "skill_level"]
        )
        return user


class VerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"].lower())
        except User.DoesNotExist:
            # Same message as a wrong code — no user enumeration via verify.
            raise serializers.ValidationError(_("Codigo invalido o expirado")) from None
        attrs["_user"] = user
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        from django.core.cache import cache
        from rest_framework.exceptions import AuthenticationFailed
        from rest_framework_simplejwt.tokens import RefreshToken

        email = attrs["email"].lower()
        key = f"failed_login:{email}"
        if cache.get(key, 0) >= 5:
            raise AuthenticationFailed(
                _("Cuenta temporalmente bloqueada por intentos fallidos"),
                code="account_locked",
            )
        user = authenticate(email=email, password=attrs["password"])
        if user is None:
            count = cache.get(key, 0) + 1
            cache.set(key, count, 1800)
            if count >= 5:
                raise AuthenticationFailed(
                    _("Cuenta temporalmente bloqueada por intentos fallidos"),
                    code="account_locked",
                )
            raise AuthenticationFailed(_("Credenciales inválidas"), code="invalid_credentials")
        if not user.email_verified:
            raise AuthenticationFailed(
                _("Verifica tu email antes de iniciar sesion"),
                code="email_not_verified",
            )
        if user.status != "active":
            raise AuthenticationFailed(_("Cuenta no activa"), code="account_inactive")
        cache.delete(key)
        refresh = RefreshToken.for_user(user)
        attrs["_user"] = user
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "full_name",
            "birth_date",
            "skill_level",
            "skill_level_name",
            "phone",
            "language_code",
            "role",
            "status",
            "email_verified",
        ]
        read_only_fields = ["email", "role", "status", "email_verified", "skill_level_name"]

    skill_level_name = serializers.CharField(
        source="skill_level.name", read_only=True, default=None, allow_null=True
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Contrasena actual incorrecta"))
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class DeviceTokenSerializer(serializers.ModelSerializer):
    device_token = serializers.CharField(source="token", max_length=512)

    class Meta:
        model = DeviceToken
        fields = ["id", "platform", "device_token", "is_active", "created_at"]
        read_only_fields = ["id", "is_active", "created_at"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
