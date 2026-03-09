"""
URL patterns for chatbot REST API.
"""
from django.urls import path
from .views import ConversationListView, ConversationDetailView, ConversationHistoryView

urlpatterns = [
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path("conversations/<uuid:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("conversations/<uuid:pk>/history/", ConversationHistoryView.as_view(), name="conversation-history"),
]
