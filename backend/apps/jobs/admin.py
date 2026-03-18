"""
Django admin configuration for Jobs app.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import JobListing, UserJobMatch, JobApplication, ScraperRun, SavedJob
from .tasks import compute_matches_for_user, recompute_all_matches


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = [
        "title", "company", "location", "source",
        "job_type", "is_active", "scraped_at", "days_remaining_display",
    ]
    list_filter = ["source", "job_type", "experience_level", "is_active"]
    search_fields = ["title", "company", "description"]
    readonly_fields = ["scraped_at", "expires_at", "skills_required"]
    ordering = ["-scraped_at"]
    actions = ["mark_inactive", "action_recompute_matches"]

    def days_remaining_display(self, obj):
        days = obj.days_remaining()
        color = "green" if days > 7 else ("orange" if days > 0 else "red")
        return format_html('<span style="color:{}">{} days</span>', color, days)

    days_remaining_display.short_description = "Days Remaining"

    @admin.action(description="Mark selected jobs as inactive")
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} job(s) marked inactive.")

    @admin.action(description="Recompute matches for all users")
    def action_recompute_matches(self, request, queryset):
        recompute_all_matches.delay()
        self.message_user(request, "Match recomputation queued for all users.")


@admin.register(ScraperRun)
class ScraperRunAdmin(admin.ModelAdmin):
    list_display = [
        "source", "status", "jobs_added", "jobs_found",
        "duration_seconds_display", "started_at", "triggered_by",
    ]
    list_filter = ["source", "status", "triggered_by"]
    readonly_fields = [
        "id", "source", "triggered_by", "started_at", "ended_at",
        "jobs_found", "jobs_added", "jobs_updated", "jobs_skipped",
        "errors", "status",
    ]
    ordering = ["-started_at"]

    def duration_seconds_display(self, obj):
        secs = obj.duration_seconds
        return f"{secs:.1f}s" if secs else "—"

    duration_seconds_display.short_description = "Duration"


@admin.register(UserJobMatch)
class UserJobMatchAdmin(admin.ModelAdmin):
    list_display = [
        "user_email", "job_title", "score_pct_display",
        "match_label_display", "computed_at",
    ]
    list_filter = ["computed_at"]
    search_fields = ["user__email", "job__title", "job__company"]
    readonly_fields = [
        "id", "user", "job", "score", "skill_overlap",
        "skill_overlap_count", "computed_at",
    ]
    ordering = ["-score"]

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User"

    def job_title(self, obj):
        return obj.job.title

    job_title.short_description = "Job Title"

    def score_pct_display(self, obj):
        pct = obj.score_percentage
        color = "green" if pct >= 80 else ("orange" if pct >= 50 else "red")
        return format_html('<span style="color:{}">{} %</span>', color, pct)

    score_pct_display.short_description = "Score"

    def match_label_display(self, obj):
        return obj.match_label

    match_label_display.short_description = "Label"


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "status", "auto_applied", "applied_at"]
    list_filter = ["status", "auto_applied"]
    search_fields = ["user__email", "job__title", "job__company"]
    readonly_fields = ["id", "applied_at"]


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "saved_at"]
    search_fields = ["user__email", "job__title"]
    readonly_fields = ["saved_at"]
