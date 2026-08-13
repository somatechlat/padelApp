from django.contrib.auth import authenticate, get_user_model, password_validation
from rest_framework import serializers

from apps.notifications.models import DeviceToken

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    consent_version = serializers.CharField()

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("El email ya esta registrado")
        return value.lower()

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_consent_version(self, value):
        if not value:
            raise serializers.ValidationError("Debes aceptar los terminos")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
            phone=validated_data.get("phone", ""),
            consent_version=validated_data["consent_version"],
        )
        from django.utils import timezone

        user.consent_ts = timezone.now()
        user.save(update_fields=["consent_ts"])
        return user


class VerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"].lower())
        except User.DoesNotExist:
            raise serializers.ValidationError("Codigo invalido") from None
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
                "Cuenta temporalmente bloqueada por intentos fallidos",
                code="account_locked",
            )
        user = authenticate(email=email, password=attrs["password"])
        if user is None:
            count = cache.get(key, 0) + 1
            cache.set(key, count, 1800)
            if count >= 5:
                raise AuthenticationFailed(
                    "Cuenta temporalmente bloqueada por intentos fallidos",
                    code="account_locked",
                )
            raise AuthenticationFailed("Credenciales invalidas", code="invalid_credentials")
        if not user.email_verified:
            raise AuthenticationFailed(
                "Verifica tu email antes de iniciar sesion", code="email_not_verified"
            )
        if user.status != "active":
            raise AuthenticationFailed("Cuenta no activa", code="account_inactive")
        cache.delete(key)
        refresh = RefreshToken.for_user(user)
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
            "full_name",
            "phone",
            "language_code",
            "role",
            "status",
            "email_verified",
        ]
        read_only_fields = ["email", "role", "status", "email_verified"]


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
            raise serializers.ValidationError("Contrasena actual incorrecta")
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
