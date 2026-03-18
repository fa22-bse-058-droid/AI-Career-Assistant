"""
Django admin registration for Jobs app.
"""
from django.contrib import admin
from .models import JobListing, JobApplication, ScraperRun, UserJobMatch, SavedJob


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = [
        "title", "company", "location", "job_type", "experience_level",
        "source", "is_active", "is_remote", "scraped_at", "expires_at",
    ]
    list_filter = ["source", "job_type", "experience_level", "is_active", "is_remote"]
    search_fields = ["title", "company", "location", "description"]
    readonly_fields = ["id", "scraped_at", "expires_at"]
    ordering = ["-scraped_at"]


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "status", "auto_applied", "applied_at"]
    list_filter = ["status", "auto_applied"]
    search_fields = ["user__email", "job__title"]
    readonly_fields = ["id", "applied_at"]
    ordering = ["-applied_at"]


@admin.register(ScraperRun)
class ScraperRunAdmin(admin.ModelAdmin):
    list_display = [
        "source", "triggered_by", "status", "jobs_found", "jobs_added",
        "jobs_updated", "jobs_skipped", "started_at", "ended_at",
    ]
    list_filter = ["source", "status", "triggered_by"]
    readonly_fields = ["id", "started_at"]
    ordering = ["-started_at"]


@admin.register(UserJobMatch)
class UserJobMatchAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "score", "skill_overlap_count", "computed_at"]
    list_filter = []
    search_fields = ["user__email", "job__title"]
    readonly_fields = ["id", "computed_at"]
    ordering = ["-score"]


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "saved_at"]
    search_fields = ["user__email", "job__title"]
    readonly_fields = ["saved_at"]
    ordering = ["-saved_at"]
