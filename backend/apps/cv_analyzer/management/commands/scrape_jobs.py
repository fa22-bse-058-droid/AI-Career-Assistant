from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Scrape jobs"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("scrape_jobs command executed"))