"""
URL patterns for Jobs app.
"""
from django.urls import path
from .views import (
    JobListView,
    JobDetailView,
    UserMatchesView,
    SaveJobView,
    TriggerScrapeView,
    ScraperStatusView,
    TriggerMatchComputeView,
)

urlpatterns = [
    path("", JobListView.as_view(), name="job-list"),
    path("matches/", UserMatchesView.as_view(), name="job-matches"),
    path("matches/compute/", TriggerMatchComputeView.as_view(), name="job-matches-compute"),
    path("scrape/trigger/", TriggerScrapeView.as_view(), name="job-scrape-trigger"),
    path("scrape/status/", ScraperStatusView.as_view(), name="job-scrape-status"),
    path("<uuid:pk>/", JobDetailView.as_view(), name="job-detail"),
    path("<uuid:pk>/save/", SaveJobView.as_view(), name="job-save"),
]
