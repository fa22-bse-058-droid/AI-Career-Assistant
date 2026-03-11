"""
URL patterns for forum.
"""
from django.urls import path
from .views import (
    CategoryListView, PostListCreateView, PostDetailView,
    ReplyListCreateView, LikePostView, LeaderboardView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="forum-categories"),
    path("posts/", PostListCreateView.as_view(), name="forum-posts"),
    path("posts/<uuid:pk>/", PostDetailView.as_view(), name="forum-post-detail"),
    path("posts/<uuid:post_id>/replies/", ReplyListCreateView.as_view(), name="forum-replies"),
    path("posts/<uuid:post_id>/like/", LikePostView.as_view(), name="forum-like-post"),
    path("leaderboard/", LeaderboardView.as_view(), name="forum-leaderboard"),
]
