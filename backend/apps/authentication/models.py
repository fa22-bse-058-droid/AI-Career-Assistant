"""
Custom User model with RBAC roles and account lockout support.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email is required"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = "student", _("Student")
        EMPLOYER = "employer", _("Employer")
        ADMIN = "admin", _("Admin")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(_("full name"), max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/%Y/%m/", null=True, blank=True
    )
    bio = models.TextField(_("bio"), max_length=500, blank=True)
    university = models.CharField(_("university"), max_length=200, blank=True)
    graduation_year = models.IntegerField(_("graduation year"), null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    # Account lockout
    failed_login_attempts = models.IntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.full_name or self.email

    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email

    def is_locked_out(self):
        if self.lockout_until and timezone.now() < self.lockout_until:
            return True
        return False

    def record_failed_login(self):
        from django.conf import settings
        max_attempts = getattr(settings, "ACCOUNT_LOCKOUT_MAX_ATTEMPTS", 5)
        lockout_minutes = getattr(settings, "ACCOUNT_LOCKOUT_DURATION_MINUTES", 15)
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.lockout_until = timezone.now() + timezone.timedelta(minutes=lockout_minutes)
        self.save(update_fields=["failed_login_attempts", "lockout_until"])

    def reset_login_attempts(self):
        self.failed_login_attempts = 0
        self.lockout_until = None
        self.save(update_fields=["failed_login_attempts", "lockout_until"])


class UserProfile(models.Model):
    """Extended profile fields supplementing CustomUser."""

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="profile"
    )
    target_role = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"
