"""
Management command: seed_job_categories
Seeds the JobCategory table with 10 predefined categories.

Usage:
    python manage.py seed_job_categories
    python manage.py seed_job_categories --clear  # wipe first
"""
from django.core.management.base import BaseCommand
from apps.cv_analyzer.models import JobCategory
from apps.cv_analyzer.skills_data import JOB_CATEGORIES_SEED


class Command(BaseCommand):
    help = "Seed JobCategory table with predefined role profiles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing categories before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = JobCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing categories."))

        created = 0
        updated = 0
        for data in JOB_CATEGORIES_SEED:
            obj, is_new = JobCategory.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "required_skills": data["required_skills"],
                },
            )
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — {created} created, {updated} updated. "
                f"Total categories: {JobCategory.objects.count()}"
            )
        )
