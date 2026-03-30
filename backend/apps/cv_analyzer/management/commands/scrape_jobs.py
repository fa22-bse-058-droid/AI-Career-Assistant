"""
Management command: scrape_jobs

Orchestrates job scrapers and persists results to JobListing / ScraperRun.
"""
import logging

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger("apps.jobs.management.scrape_jobs")

ALL_SOURCES = "all"


def _get_scraper_map():
    """Return the source-key → ScraperClass mapping (imported lazily)."""
    from apps.jobs.scrapers import (
        ArbeitnowScraper,
        IndeedScraper,
        LinkedInScraper,
        RemoteOkScraper,
        RemotiveScraper,
        RozeeScraper,
        WeWorkRemotelyScraper,
    )

    return {
        "arbeitnow": ArbeitnowScraper,
        "indeed": IndeedScraper,
        "linkedin": LinkedInScraper,
        "remote_ok": RemoteOkScraper,
        "remotive": RemotiveScraper,
        "rozee": RozeeScraper,
        "weworkremotely": WeWorkRemotelyScraper,
    }


class Command(BaseCommand):
    help = "Scrape job listings from configured sources and save them to the database."

    def add_arguments(self, parser):
        scraper_keys = sorted(_get_scraper_map())
        parser.add_argument(
            "--source",
            default=ALL_SOURCES,
            help=(
                f"Source to scrape ({', '.join(scraper_keys)}, or {ALL_SOURCES!r}). "
                f"Default: {ALL_SOURCES!r}."
            ),
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            metavar="N",
            help="Maximum total number of jobs to save across all sources.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Simulate scraping without writing any data to the database.",
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        source_arg = options["source"].lower().strip()
        limit = options["limit"]
        dry_run = options["dry_run"]
        verbosity = options["verbosity"]

        scraper_map = _get_scraper_map()
        valid_sources = list(scraper_map.keys())

        if source_arg == ALL_SOURCES:
            sources_to_run = valid_sources
        elif source_arg in scraper_map:
            sources_to_run = [source_arg]
        else:
            raise CommandError(
                f"Unknown source {source_arg!r}. "
                f"Valid options: {', '.join(sorted(valid_sources + [ALL_SOURCES]))}."
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN — no data will be written to the database."
                )
            )

        total = {"fetched": 0, "created": 0, "updated": 0, "skipped": 0, "errors": 0}
        failed_sources = []
        remaining = limit  # None = unlimited

        for source_key in sources_to_run:
            if remaining is not None and remaining <= 0:
                if verbosity >= 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Limit of {limit} reached — "
                            f"skipping remaining sources."
                        )
                    )
                break

            if verbosity >= 2:
                self.stdout.write(f"  [{source_key}] Starting …")

            try:
                scraper = scraper_map[source_key]()
                stats = self._run_single_source(
                    scraper,
                    source_key,
                    dry_run=dry_run,
                    limit=remaining,
                    verbosity=verbosity,
                )
            except Exception as exc:
                failed_sources.append(source_key)
                total["errors"] += 1
                msg = f"[{source_key}] Unhandled error: {exc}"
                logger.exception(msg)
                self.stderr.write(self.style.ERROR(msg))
                continue

            for key in total:
                total[key] += stats[key]

            if remaining is not None:
                remaining -= stats["created"] + stats["updated"]

            if verbosity >= 2:
                self.stdout.write(
                    f"  [{source_key}] done — "
                    f"fetched={stats['fetched']}  "
                    f"created={stats['created']}  "
                    f"updated={stats['updated']}  "
                    f"skipped={stats['skipped']}  "
                    f"errors={stats['errors']}"
                )

        self._print_summary(
            sources_to_run,
            total,
            dry_run=dry_run,
            failed_sources=failed_sources,
        )

        # Exit non-zero only on total failure
        if failed_sources and len(failed_sources) == len(sources_to_run):
            raise CommandError("All scrapers failed — no jobs were collected.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_single_source(self, scraper, source_key, *, dry_run, limit, verbosity):
        """
        Execute one scraper and return a stats dict:
          fetched / created / updated / skipped / errors.

        save_job is always wrapped with a local tracking shim so that the
        command has accurate counts regardless of what the scraper's own
        ScraperRun counters say.  When *limit* is set, the shim also stops
        saving new jobs once the budget is exhausted (excess attempts are
        counted as skipped).

        In dry-run mode the shim short-circuits before any DB write, and the
        scraper's lifecycle methods (start_run / end_run / log_error) are
        replaced with no-ops so that no ScraperRun record is created.
        """
        stats = {"fetched": 0, "created": 0, "updated": 0, "skipped": 0, "errors": 0}
        saved_count = [0]
        # Capture the original bound save_job *before* replacing it so the
        # closure can delegate to it for real DB writes.
        _original_save_job = scraper.save_job

        def _tracking_save_job(data):
            url = (data.get("url") or "").strip()
            if not url:
                return None, False

            # Enforce per-command limit
            if limit is not None and saved_count[0] >= limit:
                stats["skipped"] += 1
                return None, False

            # Dry-run: count the would-be creation without touching the DB
            if dry_run:
                stats["fetched"] += 1
                stats["created"] += 1
                return None, True

            # Real DB write via the original BaseScraper.save_job
            job, created = _original_save_job(data)
            if job is not None:
                saved_count[0] += 1
                stats["fetched"] += 1
                if created:
                    stats["created"] += 1
                else:
                    stats["updated"] += 1
            return job, created

        scraper.save_job = _tracking_save_job

        # ---- Dry-run path: skip ScraperRun creation ----
        if dry_run:
            scraper.start_run = lambda *a, **kw: None
            scraper.end_run = lambda *a, **kw: None
            scraper.log_error = lambda msg: logger.info(
                "[dry-run][%s] %s", source_key, msg
            )
            try:
                scraper.fetch_jobs()
            except Exception as exc:
                stats["errors"] += 1
                logger.exception(
                    "[dry-run][%s] fetch_jobs raised: %s", source_key, exc
                )
            return stats

        # ---- Real run path ----
        scraper_run = scraper.run(triggered_by="manual")

        if scraper_run:
            from apps.jobs.models import ScraperRun

            # Add scraper-tracked skips (existing-URL skips via job_exists())
            stats["skipped"] += scraper_run.jobs_skipped
            stats["errors"] = len(scraper_run.errors or [])

            # Upgrade status to PARTIAL when the run completed but logged errors
            if (
                scraper_run.status == ScraperRun.StatusChoice.COMPLETED
                and scraper_run.errors
            ):
                scraper_run.status = ScraperRun.StatusChoice.PARTIAL
                scraper_run.save(update_fields=["status"])

        return stats

    def _print_summary(self, sources, total, *, dry_run, failed_sources):
        separator = "─" * 52
        prefix = "[DRY RUN] " if dry_run else ""

        self.stdout.write(separator)
        self.stdout.write(
            f"{prefix}Scrape summary — {len(sources)} source(s) requested:"
        )
        self.stdout.write(f"  Fetched : {total['fetched']}")
        self.stdout.write(f"  Created : {total['created']}")
        self.stdout.write(f"  Updated : {total['updated']}")
        self.stdout.write(f"  Skipped : {total['skipped']}")
        self.stdout.write(f"  Errors  : {total['errors']}")
        if failed_sources:
            self.stderr.write(
                self.style.ERROR(
                    f"  Failed sources : {', '.join(failed_sources)}"
                )
            )
        self.stdout.write(separator)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Dry run complete — no changes made.")
            )
        elif not failed_sources:
            self.stdout.write(self.style.SUCCESS("Done."))
        elif len(failed_sources) < len(sources):
            self.stdout.write(
                self.style.WARNING("Completed with partial failures.")
            )