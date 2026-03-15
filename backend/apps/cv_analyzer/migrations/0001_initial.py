# Generated migration for cv_analyzer app
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
            name="CVUpload",
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
                    "file",
                    models.FileField(upload_to="cvs/%Y/%m/"),
                ),
                ("original_filename", models.CharField(max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("task_id", models.CharField(blank=True, max_length=255)),
                (
                    "uploaded_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "processed_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("error_message", models.TextField(blank=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cv_uploads",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-uploaded_at"],
            },
        ),
        migrations.CreateModel(
            name="CVAnalysis",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("overall_score", models.FloatField(default=0.0)),
                (
                    "grade",
                    models.CharField(
                        choices=[
                            ("poor", "Poor (0-40)"),
                            ("average", "Average (41-60)"),
                            ("good", "Good (61-80)"),
                            ("excellent", "Excellent (81-100)"),
                        ],
                        default="poor",
                        max_length=20,
                    ),
                ),
                ("keyword_relevance_score", models.FloatField(default=0.0)),
                ("completeness_score", models.FloatField(default=0.0)),
                ("skill_density_score", models.FloatField(default=0.0)),
                ("formatting_score", models.FloatField(default=0.0)),
                ("extracted_skills", models.JSONField(default=list)),
                ("skills_by_category", models.JSONField(default=dict)),
                ("skill_gaps", models.JSONField(default=dict)),
                ("education", models.JSONField(default=list)),
                ("experience", models.JSONField(default=list)),
                ("contact_info", models.JSONField(default=dict)),
                ("raw_text", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "cv",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis",
                        to="cv_analyzer.cvupload",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="cvupload",
            index=models.Index(
                fields=["user", "status"],
                name="cv_analyze_user_id_idx",
            ),
        ),
        migrations.CreateModel(
            name="JobCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("slug", models.SlugField(max_length=120, unique=True)),
                ("required_skills", models.JSONField(default=list)),
                ("description", models.TextField(blank=True)),
            ],
            options={
                "verbose_name_plural": "Job Categories",
                "ordering": ["name"],
            },
        ),
    ]
