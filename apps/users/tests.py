import pytest

from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserManager:
    def test_create_user_requires_email(self):
        with pytest.raises(ValueError, match="email"):
            User.objects.create_user(email="", password="pass12345")

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(email=" Test@Example.COM ", password="pass12345")
        assert user.email == "test@example.com"

    def test_create_user_hashes_password_with_argon2(self):
        user = User.objects.create_user(email="a@b.com", password="pass12345")
        assert user.password.startswith("argon2$")

    def test_create_user_defaults(self):
        user = User.objects.create_user(email="a@b.com", password="pass12345")
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.role == "cliente"
        assert user.status == "active"

    def test_create_superuser_sets_flags_and_role(self):
        admin = User.objects.create_superuser(email="admin@b.com", password="pass12345")
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == "superadmin"
        assert admin.status == "active"

    def test_create_superuser_requires_staff(self):
        with pytest.raises(ValueError, match="is_staff"):
            User.objects.create_superuser(email="a@b.com", password="x", is_staff=False)


@pytest.mark.django_db
class TestUserRolesAndStates:
    @pytest.mark.parametrize("role", ["cliente", "recepcionista", "gerente", "dueno", "superadmin"])
    def test_valid_roles(self, role):
        user = User.objects.create_user(email="r@b.com", password="pass12345", role=role)
        assert user.role == role

    def test_invalid_role_rejected(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email="r@b.com", password="pass12345", role="nobody")

    def test_default_account_state_is_active(self):
        user = User.objects.create_user(email="r@b.com", password="pass12345")
        assert user.status == "active"
        assert user.is_active_account is True

    def test_suspended_account_not_active(self):
        user = User.objects.create_user(
            email="r@b.com", password="pass12345", status="suspended"
        )
        assert user.is_active_account is False

    def test_full_name_and_phone_fields(self):
        user = User.objects.create_user(
            email="r@b.com", password="pass12345", full_name="Ana Paz", phone="0999999999"
        )
        assert user.full_name == "Ana Paz"
        assert user.phone == "0999999999"

    def test_str_returns_email(self):
        user = User.objects.create_user(email="r@b.com", password="pass12345")
        assert str(user) == "r@b.com"

    def test_uses_email_as_username_field(self):
        assert User.USERNAME_FIELD == "email"
