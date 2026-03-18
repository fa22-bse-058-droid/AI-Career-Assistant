"""
URL patterns for Jobs app.
"""
from django.urls import path
from .views import (
    JobListView,
    JobDetailView,
    MyMatchesView,
    JobApplicationListCreateView,
    JobApplicationDetailView,
    SavedJobListView,
    SaveJobView,
    ScraperRunListView,
)

urlpatterns = [
    path("", JobListView.as_view(), name="job-list"),
    path("<uuid:pk>/", JobDetailView.as_view(), name="job-detail"),
    path("matches/", MyMatchesView.as_view(), name="job-matches"),
    path("applications/", JobApplicationListCreateView.as_view(), name="job-applications"),
    path("applications/<uuid:pk>/", JobApplicationDetailView.as_view(), name="job-application-detail"),
    path("saved/", SavedJobListView.as_view(), name="saved-jobs"),
    path("<uuid:job_id>/save/", SaveJobView.as_view(), name="save-job"),
    path("scraper-runs/", ScraperRunListView.as_view(), name="scraper-runs"),
]
