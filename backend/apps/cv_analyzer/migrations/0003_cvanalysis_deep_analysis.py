from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "cv_analyzer",
            "0002_rename_cv_analyze_user_id_idx_cv_analyzer_user_id_4125d5_idx",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="cvanalysis",
            name="deep_analysis",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
