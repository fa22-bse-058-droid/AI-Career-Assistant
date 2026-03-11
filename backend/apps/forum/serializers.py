"""
Forum serializers.
"""
from rest_framework import serializers
from .models import ForumCategory, ForumPost, ForumReply, UserPoints, UserBadge


class ForumCategorySerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(source="posts.count", read_only=True)

    class Meta:
        model = ForumCategory
        fields = ["id", "name", "slug", "description", "icon", "color", "post_count"]


class ForumReplySerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    author_id = serializers.UUIDField(source="author.id", read_only=True)
    likes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ForumReply
        fields = [
            "id", "author_id", "author_name", "content", "parent",
            "likes_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "author_id", "author_name", "likes_count", "created_at", "updated_at"]


class ForumPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    author_id = serializers.UUIDField(source="author.id", read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = ForumPost
        fields = [
            "id", "category", "category_name", "author_id", "author_name",
            "title", "content", "is_pinned", "views_count",
            "likes_count", "replies_count", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "author_id", "author_name", "is_pinned", "views_count",
            "likes_count", "replies_count", "created_at", "updated_at",
        ]


class UserBadgeSerializer(serializers.ModelSerializer):
    badge_name = serializers.CharField(source="badge.name", read_only=True)
    badge_tier = serializers.CharField(source="badge.tier", read_only=True)

    class Meta:
        model = UserBadge
        fields = ["badge_name", "badge_tier", "earned_at"]


class LeaderboardSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    badges = UserBadgeSerializer(source="user.badges", many=True, read_only=True)

    class Meta:
        model = UserPoints
        fields = ["user_id", "user_name", "user_email", "total_points", "badges"]
