"""
Mock Interview URL patterns.
"""
from django.urls import path
from .views import (
    StartSessionView, SubmitResponseView, CompleteSessionView,
    SessionDetailView, SessionListView, GeneratePDFReportView,
)

urlpatterns = [
    path("sessions/", SessionListView.as_view(), name="interview-session-list"),
    path("sessions/start/", StartSessionView.as_view(), name="interview-start"),
    path("sessions/<uuid:pk>/", SessionDetailView.as_view(), name="interview-session-detail"),
    path("sessions/<uuid:session_id>/respond/", SubmitResponseView.as_view(), name="interview-respond"),
    path("sessions/<uuid:session_id>/complete/", CompleteSessionView.as_view(), name="interview-complete"),
    path("sessions/<uuid:session_id>/report/", GeneratePDFReportView.as_view(), name="interview-report"),
]
