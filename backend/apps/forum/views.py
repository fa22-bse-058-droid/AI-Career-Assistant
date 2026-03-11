"""
Forum views — posts, replies, likes, leaderboard.
"""
import bleach
from django.core.cache import cache
from django.db.models import Count
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    ForumCategory, ForumPost, ForumReply,
    PostLike, ReplyLike, UserPoints, UserBadge,
)
from .serializers import (
    ForumCategorySerializer, ForumPostSerializer,
    ForumReplySerializer, LeaderboardSerializer,
)

ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS + ["p", "br", "pre", "code", "ul", "ol", "li", "h3", "h4"]


class CategoryListView(generics.ListAPIView):
    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = ForumPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = ForumPost.objects.filter(is_deleted=False).select_related(
            "author", "author__profile", "category"
        ).annotate(
            likes_total=Count("likes"),
            replies_total=Count("replies"),
        )
        category_slug = self.request.query_params.get("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs

    def perform_create(self, serializer):
        content = bleach.clean(serializer.validated_data["content"], tags=ALLOWED_TAGS)
        post = serializer.save(author=self.request.user, content=content)
        # Award points for creating a post
        points, _ = UserPoints.objects.get_or_create(user=self.request.user)
        points.award_points(10, "Created a forum post")
        # Trigger notification for followers (placeholder)
        return post


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ForumPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ForumPost.objects.filter(is_deleted=False)

    def perform_update(self, serializer):
        content = bleach.clean(
            serializer.validated_data.get("content", serializer.instance.content),
            tags=ALLOWED_TAGS,
        )
        serializer.save(content=content)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])


class ReplyListCreateView(generics.ListCreateAPIView):
    serializer_class = ForumReplySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ForumReply.objects.filter(
            post_id=self.kwargs["post_id"], is_deleted=False
        ).select_related("author", "author__profile")

    def perform_create(self, serializer):
        content = bleach.clean(serializer.validated_data["content"], tags=ALLOWED_TAGS)
        post_id = self.kwargs["post_id"]
        reply = serializer.save(author=self.request.user, post_id=post_id, content=content)
        points, _ = UserPoints.objects.get_or_create(user=self.request.user)
        points.award_points(5, "Posted a reply")
        # Notify post author
        post = reply.post
        if post.author != self.request.user:
            from apps.notifications.tasks import create_notification
            create_notification.delay(
                str(post.author.id),
                "forum_reply",
                "New reply on your post",
                f"{self.request.user.full_name} replied to your post: {post.title}",
                f"/forum/posts/{post.id}/",
            )


class LikePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = generics.get_object_or_404(ForumPost, pk=post_id, is_deleted=False)
        like, created = PostLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            # Refresh count from DB after deletion
            return Response({"liked": False, "likes": post.likes.count()})
        # Award points to post author
        if post.author != request.user:
            points, _ = UserPoints.objects.get_or_create(user=post.author)
            points.award_points(2, "Received a like on post")
        # Refresh count from DB after creation
        return Response({"liked": True, "likes": post.likes.count()})


class LeaderboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cache_key = "forum_leaderboard"
        data = cache.get(cache_key)
        if data is None:
            top_users = (
                UserPoints.objects.select_related("user", "user__profile")
                .order_by("-total_points")[:20]
            )
            data = LeaderboardSerializer(top_users, many=True).data
            cache.set(cache_key, data, timeout=300)
        return Response(data)
