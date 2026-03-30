"""
Tests for the scrape_jobs management command.

Coverage:
  - option handling  (unknown source, specific source, all sources)
  - dry-run behaviour
  - error handling   (partial vs total failure)
  - summary output
  - upsert DB tests  (create + update)   [require @pytest.mark.django_db]
"""
import pytest
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError

# Patch target for the scraper-map factory inside the command module
SCRAPER_MAP_PATCH = (
    "apps.cv_analyzer.management.commands.scrape_jobs._get_scraper_map"
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_scraper_run(
    *,
    jobs_found=0,
    jobs_added=0,
    jobs_updated=0,
    jobs_skipped=0,
    errors=None,
    status="completed",
):
    """Return a lightweight mock that behaves like a ScraperRun instance."""
    run = MagicMock()
    run.jobs_found = jobs_found
    run.jobs_added = jobs_added
    run.jobs_updated = jobs_updated
    run.jobs_skipped = jobs_skipped
    run.errors = errors if errors is not None else []
    run.status = status
    return run


def _make_scraper(run=None):
    """Return a mock scraper whose run() returns *run* (or an empty default)."""
    scraper = MagicMock()
    scraper.run.return_value = run if run is not None else _make_scraper_run()
    return scraper


# ---------------------------------------------------------------------------
# Option-handling tests
# ---------------------------------------------------------------------------


class TestScrapeJobsOptions:
    @patch(SCRAPER_MAP_PATCH)
    def test_unknown_source_raises_command_error(self, mock_map):
        mock_map.return_value = {"remotive": MagicMock()}
        with pytest.raises(CommandError, match="Unknown source"):
            call_command("scrape_jobs", "--source", "bogus_source")

    @patch(SCRAPER_MAP_PATCH)
    def test_specific_source_runs_only_that_scraper(self, mock_map):
        remotive_scraper = _make_scraper(_make_scraper_run(jobs_added=2, jobs_found=2))
        RemotiveClass = MagicMock(return_value=remotive_scraper)
        IndeedClass = MagicMock()  # should NOT be instantiated

        mock_map.return_value = {
            "remotive": RemotiveClass,
            "indeed": IndeedClass,
        }

        call_command("scrape_jobs", "--source", "remotive")

        RemotiveClass.assert_called_once()
        IndeedClass.assert_not_called()
        remotive_scraper.run.assert_called_once_with(triggered_by="manual")

    @patch(SCRAPER_MAP_PATCH)
    def test_all_sources_runs_every_scraper(self, mock_map):
        classes = {}
        for name in ("rozee", "remotive", "indeed"):
            cls = MagicMock(return_value=_make_scraper())
            classes[name] = cls
        mock_map.return_value = classes

        call_command("scrape_jobs")  # default --source all

        for cls in classes.values():
            cls.assert_called_once()

    @patch(SCRAPER_MAP_PATCH)
    def test_limit_skips_remaining_sources_when_budget_exhausted(self, mock_map):
        """Once the limit is reached after the first source, others are skipped."""
        scraper1 = MagicMock()
        # The original save_job must return a (job, created) tuple so the
        # tracking shim can unpack it correctly.
        scraper1.save_job.return_value = (MagicMock(), True)

        def fake_run_src1(triggered_by="scheduled"):
            # Simulate 3 jobs being processed (triggers the tracking shim
            # 3 times and exhausts the budget of 3).
            scraper1.save_job({"url": "https://example.com/1", "title": "J1"})
            scraper1.save_job({"url": "https://example.com/2", "title": "J2"})
            scraper1.save_job({"url": "https://example.com/3", "title": "J3"})
            return _make_scraper_run(jobs_found=3, jobs_added=3)

        scraper1.run.side_effect = fake_run_src1
        scraper2 = _make_scraper()
        Class1 = MagicMock(return_value=scraper1)
        Class2 = MagicMock(return_value=scraper2)

        mock_map.return_value = {"src1": Class1, "src2": Class2}

        call_command("scrape_jobs", "--limit", "3")

        Class1.assert_called_once()
        # src2 must not run because the entire budget was consumed by src1
        scraper2.run.assert_not_called()


# ---------------------------------------------------------------------------
# Dry-run tests
# ---------------------------------------------------------------------------


class TestScrapeJobsDryRun:
    @patch(SCRAPER_MAP_PATCH)
    def test_dry_run_banner_in_output(self, mock_map):
        scraper = MagicMock()
        scraper.fetch_jobs.return_value = 0
        mock_map.return_value = {"remotive": MagicMock(return_value=scraper)}

        out = StringIO()
        call_command("scrape_jobs", "--source", "remotive", "--dry-run", stdout=out)

        assert "DRY RUN" in out.getvalue()

    @patch(SCRAPER_MAP_PATCH)
    def test_dry_run_calls_fetch_jobs_not_run(self, mock_map):
        scraper = MagicMock()
        scraper.fetch_jobs.return_value = 0
        mock_map.return_value = {"remotive": MagicMock(return_value=scraper)}

        call_command("scrape_jobs", "--source", "remotive", "--dry-run")

        scraper.fetch_jobs.assert_called_once()
        scraper.run.assert_not_called()

    @patch(SCRAPER_MAP_PATCH)
    def test_dry_run_counts_jobs_via_patched_save_job(self, mock_map):
        """save_job calls made inside fetch_jobs are counted but not written to DB."""
        scraper = MagicMock()

        def fake_fetch_jobs():
            # Simulate the scraper calling self.save_job for each job it finds.
            # By this point the command has already replaced scraper.save_job
            # with its dry-run shim, so these calls hit the shim.
            scraper.save_job({"url": "https://example.com/j/1", "title": "Dev"})
            scraper.save_job({"url": "https://example.com/j/2", "title": "QA"})
            return 2  # 2 jobs found

        scraper.fetch_jobs.side_effect = fake_fetch_jobs
        mock_map.return_value = {"remotive": MagicMock(return_value=scraper)}

        out = StringIO()
        call_command("scrape_jobs", "--source", "remotive", "--dry-run", stdout=out)

        # The summary should report 2 would-be creations
        assert "2" in out.getvalue()

    @patch(SCRAPER_MAP_PATCH)
    def test_dry_run_fetch_error_is_handled_gracefully(self, mock_map):
        scraper = MagicMock()
        scraper.fetch_jobs.side_effect = RuntimeError("network failure")
        mock_map.return_value = {"remotive": MagicMock(return_value=scraper)}

        out = StringIO()
        err = StringIO()
        # Should not raise CommandError — fetch_jobs error in dry-run is counted
        # as an error but does not abort the command (it is not a "failed source").
        call_command(
            "scrape_jobs", "--source", "remotive", "--dry-run",
            stdout=out, stderr=err,
        )
        # Reaches here without raising

    @patch(SCRAPER_MAP_PATCH)
    def test_dry_run_summary_shows_dry_run_complete(self, mock_map):
        scraper = MagicMock()
        scraper.fetch_jobs.return_value = 0
        mock_map.return_value = {"remotive": MagicMock(return_value=scraper)}

        out = StringIO()
        call_command("scrape_jobs", "--source", "remotive", "--dry-run", stdout=out)

        assert "Dry run complete" in out.getvalue()


# ---------------------------------------------------------------------------
# Error-handling tests
# ---------------------------------------------------------------------------


class TestScrapeJobsErrorHandling:
    @patch(SCRAPER_MAP_PATCH)
    def test_failing_source_does_not_abort_others(self, mock_map):
        bad_scraper = MagicMock()
        bad_scraper.run.side_effect = Exception("boom")
        BadClass = MagicMock(return_value=bad_scraper)

        good_scraper = _make_scraper(_make_scraper_run(jobs_added=1, jobs_found=1))
        GoodClass = MagicMock(return_value=good_scraper)

        mock_map.return_value = {"bad": BadClass, "good": GoodClass}

        out = StringIO()
        err = StringIO()
        call_command("scrape_jobs", stdout=out, stderr=err)

        good_scraper.run.assert_called_once()
        assert "bad" in err.getvalue().lower() or "boom" in err.getvalue()

    @patch(SCRAPER_MAP_PATCH)
    def test_all_sources_fail_raises_command_error(self, mock_map):
        bad = MagicMock()
        bad.run.side_effect = Exception("all bad")
        mock_map.return_value = {"only": MagicMock(return_value=bad)}

        with pytest.raises(CommandError, match="All scrapers failed"):
            call_command("scrape_jobs")

    @patch(SCRAPER_MAP_PATCH)
    def test_partial_failure_does_not_raise_command_error(self, mock_map):
        bad_scraper = MagicMock()
        bad_scraper.run.side_effect = Exception("intermittent")
        BadClass = MagicMock(return_value=bad_scraper)

        good_scraper = _make_scraper(_make_scraper_run(jobs_found=2, jobs_added=2))
        GoodClass = MagicMock(return_value=good_scraper)

        mock_map.return_value = {"bad": BadClass, "good": GoodClass}

        out = StringIO()
        # Must not raise — at least one source succeeded
        call_command("scrape_jobs", stdout=out)

    @patch(SCRAPER_MAP_PATCH)
    def test_partial_failure_summary_mentions_failures(self, mock_map):
        bad_scraper = MagicMock()
        bad_scraper.run.side_effect = Exception("intermittent")
        BadClass = MagicMock(return_value=bad_scraper)

        good_scraper = _make_scraper(_make_scraper_run(jobs_found=1, jobs_added=1))
        GoodClass = MagicMock(return_value=good_scraper)

        mock_map.return_value = {"bad": BadClass, "good": GoodClass}

        out = StringIO()
        err = StringIO()
        call_command("scrape_jobs", stdout=out, stderr=err)

        combined = out.getvalue() + err.getvalue()
        assert "partial" in combined.lower() or "failure" in combined.lower()


# ---------------------------------------------------------------------------
# Summary output tests
# ---------------------------------------------------------------------------


class TestScrapeJobsSummaryOutput:
    @patch(SCRAPER_MAP_PATCH)
    def test_summary_labels_present(self, mock_map):
        run = _make_scraper_run(
            jobs_found=10, jobs_added=7, jobs_updated=2, jobs_skipped=1
        )
        mock_map.return_value = {"remotive": MagicMock(return_value=_make_scraper(run))}

        out = StringIO()
        call_command("scrape_jobs", "--source", "remotive", stdout=out)

        output = out.getvalue()
        for label in ("Fetched", "Created", "Updated", "Skipped", "Errors"):
            assert label in output, f"Expected '{label}' in summary"

    @patch(SCRAPER_MAP_PATCH)
    def test_verbosity_2_shows_per_source_line(self, mock_map):
        run = _make_scraper_run(jobs_found=3, jobs_added=3)
        mock_map.return_value = {"remotive": MagicMock(return_value=_make_scraper(run))}

        out = StringIO()
        call_command(
            "scrape_jobs", "--source", "remotive", "--verbosity", "2", stdout=out
        )

        output = out.getvalue()
        assert "remotive" in output
        # Per-source line should contain stats
        assert "fetched=" in output

    @patch(SCRAPER_MAP_PATCH)
    def test_success_message_when_no_failures(self, mock_map):
        mock_map.return_value = {
            "remotive": MagicMock(return_value=_make_scraper())
        }

        out = StringIO()
        call_command("scrape_jobs", "--source", "remotive", stdout=out)

        assert "Done" in out.getvalue()


# ---------------------------------------------------------------------------
# Upsert DB tests  (require a live test database)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScrapeJobsUpsert:
    """
    These tests use a real test database to verify that the command correctly
    creates and updates JobListing records via BaseScraper.save_job().

    The HTTP layer is replaced by a minimal BaseScraper subclass whose
    fetch_jobs() just calls self.save_job() directly, so no network traffic
    is generated.  fake_useragent.UserAgent is patched to avoid any
    outbound request during initialisation.
    """

    @patch("apps.jobs.scrapers.base_scraper.UserAgent")
    @patch(SCRAPER_MAP_PATCH)
    def test_new_job_is_created_in_db(self, mock_map, MockUA):
        MockUA.return_value.random = "TestAgent/1.0"

        from apps.jobs.scrapers.base_scraper import BaseScraper

        class OneShotScraper(BaseScraper):
            def __init__(self):
                super().__init__(source="remotive")

            def fetch_jobs(self):
                self.save_job(
                    {
                        "url": "https://testjobs.example.com/python-dev",
                        "title": "Python Developer",
                        "company": "Acme Corp",
                        "description": "Python role",
                        "source": "remotive",
                    }
                )
                self._increment_run_counter(jobs_found=1, jobs_added=1)
                return 1

        mock_map.return_value = {"remotive": OneShotScraper}

        call_command("scrape_jobs", "--source", "remotive")

        from apps.jobs.models import JobListing

        assert JobListing.objects.filter(
            url="https://testjobs.example.com/python-dev"
        ).exists()
        job = JobListing.objects.get(url="https://testjobs.example.com/python-dev")
        assert job.title == "Python Developer"
        assert job.company == "Acme Corp"

    @patch("apps.jobs.scrapers.base_scraper.UserAgent")
    @patch(SCRAPER_MAP_PATCH)
    def test_existing_job_is_updated_not_duplicated(self, mock_map, MockUA):
        MockUA.return_value.random = "TestAgent/1.0"

        from apps.jobs.models import JobListing
        from apps.jobs.scrapers.base_scraper import BaseScraper

        url = "https://testjobs.example.com/existing-job"
        JobListing.objects.create(
            url=url,
            title="Old Title",
            company="Old Corp",
            description="Old description",
            source="remotive",
        )

        class UpdatingScraper(BaseScraper):
            def __init__(self):
                super().__init__(source="remotive")

            def fetch_jobs(self):
                self.save_job(
                    {
                        "url": url,
                        "title": "New Title",
                        "company": "New Corp",
                        "description": "Updated description",
                        "source": "remotive",
                    }
                )
                self._increment_run_counter(jobs_found=1, jobs_updated=1)
                return 1

        mock_map.return_value = {"remotive": UpdatingScraper}

        call_command("scrape_jobs", "--source", "remotive")

        # Exactly one record with this URL
        assert JobListing.objects.filter(url=url).count() == 1
        job = JobListing.objects.get(url=url)
        assert job.title == "New Title"
        assert job.company == "New Corp"

    @patch("apps.jobs.scrapers.base_scraper.UserAgent")
    @patch(SCRAPER_MAP_PATCH)
    def test_limit_caps_total_jobs_saved(self, mock_map, MockUA):
        MockUA.return_value.random = "TestAgent/1.0"

        from apps.jobs.models import JobListing
        from apps.jobs.scrapers.base_scraper import BaseScraper

        class BulkScraper(BaseScraper):
            def __init__(self):
                super().__init__(source="remotive")

            def fetch_jobs(self):
                for i in range(10):
                    self.save_job(
                        {
                            "url": f"https://bulk.example.com/job/{i}",
                            "title": f"Job {i}",
                            "company": "Bulk Co",
                            "description": "desc",
                            "source": "remotive",
                        }
                    )
                    self._increment_run_counter(jobs_found=1, jobs_added=1)
                return 10

        mock_map.return_value = {"remotive": BulkScraper}

        call_command("scrape_jobs", "--source", "remotive", "--limit", "3")

        assert JobListing.objects.filter(
            url__startswith="https://bulk.example.com/"
        ).count() == 3

    @patch("apps.jobs.scrapers.base_scraper.UserAgent")
    @patch(SCRAPER_MAP_PATCH)
    def test_scraper_run_record_created_for_real_run(self, mock_map, MockUA):
        MockUA.return_value.random = "TestAgent/1.0"

        from apps.jobs.models import ScraperRun
        from apps.jobs.scrapers.base_scraper import BaseScraper

        class EmptyScraper(BaseScraper):
            def __init__(self):
                super().__init__(source="remotive")

            def fetch_jobs(self):
                return 0

        mock_map.return_value = {"remotive": EmptyScraper}

        call_command("scrape_jobs", "--source", "remotive")

        assert ScraperRun.objects.filter(source="remotive").exists()

    @patch("apps.jobs.scrapers.base_scraper.UserAgent")
    @patch(SCRAPER_MAP_PATCH)
    def test_dry_run_does_not_create_job_listings(self, mock_map, MockUA):
        MockUA.return_value.random = "TestAgent/1.0"

        from apps.jobs.models import JobListing
        from apps.jobs.scrapers.base_scraper import BaseScraper

        class DataScraper(BaseScraper):
            def __init__(self):
                super().__init__(source="remotive")

            def fetch_jobs(self):
                self.save_job(
                    {
                        "url": "https://dry.example.com/job/1",
                        "title": "Ghost Job",
                        "company": "Ghost Corp",
                        "description": "Should not be persisted",
                        "source": "remotive",
                    }
                )
                return 1

        mock_map.return_value = {"remotive": DataScraper}

        call_command("scrape_jobs", "--source", "remotive", "--dry-run")

        assert not JobListing.objects.filter(
            url="https://dry.example.com/job/1"
        ).exists()

    @patch("apps.jobs.scrapers.base_scraper.UserAgent")
    @patch(SCRAPER_MAP_PATCH)
    def test_dry_run_does_not_create_scraper_run_record(self, mock_map, MockUA):
        MockUA.return_value.random = "TestAgent/1.0"

        from apps.jobs.models import ScraperRun
        from apps.jobs.scrapers.base_scraper import BaseScraper

        class EmptyScraper(BaseScraper):
            def __init__(self):
                super().__init__(source="remotive")

            def fetch_jobs(self):
                return 0

        mock_map.return_value = {"remotive": EmptyScraper}

        before = ScraperRun.objects.count()
        call_command("scrape_jobs", "--source", "remotive", "--dry-run")

        assert ScraperRun.objects.count() == before

    @patch("apps.jobs.scrapers.base_scraper.UserAgent")
    @patch(SCRAPER_MAP_PATCH)
    def test_fields_populated_on_created_job(self, mock_map, MockUA):
        """At minimum, all required fields are populated after a real scrape."""
        MockUA.return_value.random = "TestAgent/1.0"

        from apps.jobs.models import JobListing
        from apps.jobs.scrapers.base_scraper import BaseScraper

        class FullScraper(BaseScraper):
            def __init__(self):
                super().__init__(source="remotive")

            def fetch_jobs(self):
                self.save_job(
                    {
                        "url": "https://fields.example.com/job/1",
                        "title": "Full Stack Developer",
                        "company": "Tech Co",
                        "location": "Remote",
                        "description": "Python Django React AWS Docker",
                        "source": "remotive",
                        "is_remote": True,
                        "job_type": "remote",
                        "experience_level": "mid",
                    }
                )
                self._increment_run_counter(jobs_found=1, jobs_added=1)
                return 1

        mock_map.return_value = {"remotive": FullScraper}

        call_command("scrape_jobs", "--source", "remotive")

        job = JobListing.objects.get(url="https://fields.example.com/job/1")
        assert job.title == "Full Stack Developer"
        assert job.company == "Tech Co"
        assert job.location == "Remote"
        assert job.is_remote is True
        assert job.job_type == "remote"
        assert job.experience_level == "mid"
        assert job.source == "remotive"
        # Skills should have been auto-extracted from the description
        assert isinstance(job.skills_required, list)
        assert len(job.skills_required) > 0
