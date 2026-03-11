"""
URL patterns for Jobs app.
"""
from django.urls import path
from .views import JobListView, JobDetailView, MyMatchesView, BookmarkJobView

urlpatterns = [
    path("", JobListView.as_view(), name="job-list"),
    path("<uuid:pk>/", JobDetailView.as_view(), name="job-detail"),
    path("matches/", MyMatchesView.as_view(), name="job-matches"),
    path("<uuid:job_id>/bookmark/", BookmarkJobView.as_view(), name="job-bookmark"),
]
