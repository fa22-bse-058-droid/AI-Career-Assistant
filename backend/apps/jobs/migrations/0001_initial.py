# Generated migration for jobs app
import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="JobListing",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("company", models.CharField(max_length=255)),
                ("location", models.CharField(blank=True, max_length=255)),
                (
                    "job_type",
                    models.CharField(
                        choices=[
                            ("full_time", "Full Time"),
                            ("part_time", "Part Time"),
                            ("internship", "Internship"),
                            ("remote", "Remote"),
                            ("hybrid", "Hybrid"),
                        ],
                        default="full_time",
                        max_length=20,
                    ),
                ),
                (
                    "experience_level",
                    models.CharField(
                        choices=[
                            ("entry", "Entry Level"),
                            ("mid", "Mid Level"),
                            ("senior", "Senior Level"),
                            ("any", "Any Level"),
                        ],
                        default="any",
                        max_length=20,
                    ),
                ),
                ("description", models.TextField()),
                ("requirements", models.TextField(blank=True)),
                ("salary_min", models.IntegerField(blank=True, null=True)),
                ("salary_max", models.IntegerField(blank=True, null=True)),
                ("salary_display", models.CharField(blank=True, max_length=100)),
                ("url", models.URLField(unique=True)),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("rozee", "Rozee.pk"),
                            ("indeed", "Indeed"),
                            ("linkedin", "LinkedIn"),
                        ],
                        default="rozee",
                        max_length=20,
                    ),
                ),
                ("scraped_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("skills_required", models.JSONField(default=list)),
                ("raw_html", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["-scraped_at"],
            },
        ),
        migrations.CreateModel(
            name="ScraperRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("rozee", "Rozee.pk"),
                            ("indeed", "Indeed"),
                            ("all", "All Sources"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "triggered_by",
                    models.CharField(
                        choices=[
                            ("scheduled", "Scheduled"),
                            ("manual", "Manual"),
                        ],
                        default="scheduled",
                        max_length=20,
                    ),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("jobs_found", models.IntegerField(default=0)),
                ("jobs_added", models.IntegerField(default=0)),
                ("jobs_updated", models.IntegerField(default=0)),
                ("jobs_skipped", models.IntegerField(default=0)),
                ("errors", models.JSONField(default=list)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "Running"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("partial", "Partial"),
                        ],
                        default="running",
                        max_length=20,
                    ),
                ),
            ],
            options={
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="JobApplication",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to="jobs.joblisting",
                    ),
                ),
                ("applied_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("applied", "Applied"),
                            ("interviewing", "Interviewing"),
                            ("rejected", "Rejected"),
                            ("accepted", "Accepted"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("auto_applied", models.BooleanField(default=False)),
                ("cover_letter", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "ordering": ["-applied_at"],
            },
        ),
        migrations.CreateModel(
            name="UserJobMatch",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="job_matches",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matches",
                        to="jobs.joblisting",
                    ),
                ),
                ("score", models.FloatField()),
                ("skill_overlap", models.JSONField(default=list)),
                ("skill_overlap_count", models.IntegerField(default=0)),
                ("computed_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-score"],
            },
        ),
        migrations.CreateModel(
            name="JobMatch",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="legacy_job_matches",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="legacy_matches",
                        to="jobs.joblisting",
                    ),
                ),
                ("match_score", models.FloatField(default=0.0)),
                ("semantic_score", models.FloatField(default=0.0)),
                ("keyword_score", models.FloatField(default=0.0)),
                ("is_bookmarked", models.BooleanField(default=False)),
                ("computed_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-match_score"],
            },
        ),
        migrations.CreateModel(
            name="SavedJob",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saved_jobs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saved_by",
                        to="jobs.joblisting",
                    ),
                ),
                ("saved_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-saved_at"],
            },
        ),
        migrations.AddIndex(
            model_name="joblisting",
            index=models.Index(fields=["source"], name="jobs_joblis_source_idx"),
        ),
        migrations.AddIndex(
            model_name="joblisting",
            index=models.Index(fields=["is_active"], name="jobs_joblis_is_acti_idx"),
        ),
        migrations.AddIndex(
            model_name="joblisting",
            index=models.Index(fields=["scraped_at"], name="jobs_joblis_scraped_idx"),
        ),
        migrations.AddIndex(
            model_name="joblisting",
            index=models.Index(fields=["job_type"], name="jobs_joblis_job_typ_idx"),
        ),
        migrations.AddIndex(
            model_name="joblisting",
            index=models.Index(fields=["experience_level"], name="jobs_joblis_exp_lev_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="jobapplication",
            unique_together={("user", "job")},
        ),
        migrations.AlterUniqueTogether(
            name="userjobmatch",
            unique_together={("user", "job")},
        ),
        migrations.AlterUniqueTogether(
            name="jobmatch",
            unique_together={("user", "job")},
        ),
        migrations.AlterUniqueTogether(
            name="savedjob",
            unique_together={("user", "job")},
        ),
    ]
