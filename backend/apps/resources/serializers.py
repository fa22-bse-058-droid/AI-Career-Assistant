"""
Resource serializers.
"""
from rest_framework import serializers
from .models import Resource


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = [
            "id", "title", "platform", "url", "description",
            "skill_tags", "difficulty", "is_free", "duration_hours", "rating",
        ]
