"""
URL patterns for CV Analyzer.
"""
from django.urls import path
from .views import CVUploadView, CVStatusView, CVListView, CVAnalysisView, CompanyMatchView

urlpatterns = [
    path("upload/", CVUploadView.as_view(), name="cv-upload"),
    path("list/", CVListView.as_view(), name="cv-list"),
    path("<uuid:cv_id>/status/", CVStatusView.as_view(), name="cv-status"),
    path("<uuid:cv_id>/analysis/", CVAnalysisView.as_view(), name="cv-analysis"),
    path("<uuid:cv_id>/company-match/", CompanyMatchView.as_view(), name="cv-company-match"),
]
