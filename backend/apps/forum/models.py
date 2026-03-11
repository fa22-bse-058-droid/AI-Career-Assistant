"""
Forum app models with gamification.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class ForumCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default="#3B82F6")  # hex color
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "forum categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ForumPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_posts"
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]
        indexes = [models.Index(fields=["created_at"])]

    def __str__(self):
        return self.title

    @property
    def likes_count(self):
        return self.likes.count()

    @property
    def replies_count(self):
        return self.replies.filter(is_deleted=False).count()


class ForumReply(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="forum_replies"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply by {self.author.email} on {self.post.title}"

    @property
    def likes_count(self):
        return self.likes.count()


class PostLike(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["post", "user"]]


class ReplyLike(models.Model):
    reply = models.ForeignKey(ForumReply, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["reply", "user"]]


# ── Gamification ──────────────────────────────────────────────────────────────

class Badge(models.Model):
    class Tier(models.TextChoices):
        NEWCOMER = "newcomer", "Newcomer"
        CONTRIBUTOR = "contributor", "Contributor"
        EXPERT = "expert", "Expert"
        CHAMPION = "champion", "Champion"

    THRESHOLDS = {
        Tier.NEWCOMER: 0,
        Tier.CONTRIBUTOR: 50,
        Tier.EXPERT: 200,
        Tier.CHAMPION: 500,
    }

    name = models.CharField(max_length=50, unique=True)
    tier = models.CharField(max_length=20, choices=Tier.choices)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class UserPoints(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="points",
    )
    total_points = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}: {self.total_points} pts"

    def award_points(self, amount: int, reason: str):
        self.total_points += amount
        self.save(update_fields=["total_points", "updated_at"])
        PointTransaction.objects.create(user=self.user, amount=amount, reason=reason)
        self._check_badges()

    def _check_badges(self):
        for tier, threshold in Badge.THRESHOLDS.items():
            if self.total_points >= threshold:
                badge = Badge.objects.filter(tier=tier).first()
                if badge:
                    UserBadge.objects.get_or_create(user=self.user, badge=badge)


class PointTransaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="point_transactions",
    )
    amount = models.IntegerField()
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class UserBadge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="badges",
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [["user", "badge"]]

    def __str__(self):
        return f"{self.user.email} — {self.badge.name}"
