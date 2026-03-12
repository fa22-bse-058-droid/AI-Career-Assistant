"""
Serializers for authentication app.
"""
import re
from django.contrib.auth import authenticate
from django.utils import timezone
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "target_role", "phone", "linkedin_url", "github_url",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id", "email", "full_name", "role", "profile_picture",
            "bio", "university", "graduation_year",
            "is_active", "date_joined", "profile",
        ]
        read_only_fields = ["id", "role", "is_active", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=CustomUser.Role.choices,
        default=CustomUser.Role.STUDENT,
    )

    class Meta:
        model = CustomUser
        fields = ["email", "full_name", "password", "password_confirm", "role",
                  "university", "graduation_year"]
        extra_kwargs = {
            "university": {"required": False, "allow_blank": True},
            "graduation_year": {"required": False, "allow_null": True},
        }

    def validate_email(self, value):
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"\d", value):
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )
        return value

    def validate(self, data):
        if data["password"] != data.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        token["full_name"] = user.full_name
        return token

    def validate(self, attrs):
        email = attrs.get("email") or attrs.get(self.username_field)
        password = attrs.get("password")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        if user.is_locked_out():
            seconds_remaining = int(
                (user.lockout_until - timezone.now()).total_seconds()
            )
            raise serializers.ValidationError(
                {
                    "detail": "Account locked due to too many failed attempts.",
                    "lockout_seconds_remaining": seconds_remaining,
                }
            )

        authenticated = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if not authenticated:
            user.record_failed_login()
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        user.reset_login_attempts()
        return super().validate(attrs)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        return data

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
