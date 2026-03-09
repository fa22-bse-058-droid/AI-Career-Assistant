"""
Admin Panel serializers.
"""
from rest_framework import serializers
from apps.authentication.models import CustomUser, UserProfile
from .models import AuditLog


class AdminUserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    def get_profile(self, obj):
        try:
            p = obj.profile
            return {"university": p.university, "target_role": p.target_role}
        except UserProfile.DoesNotExist:
            return {}

    class Meta:
        model = CustomUser
        fields = ["id", "email", "username", "role", "is_active", "date_joined", "profile"]


class AuditLogSerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(source="admin.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "admin_email", "action", "target_model", "target_id", "details", "ip_address", "created_at"]
        read_only_fields = fields


class AdminStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_cvs = serializers.IntegerField()
    total_jobs = serializers.IntegerField()
    total_applications = serializers.IntegerField()
