"""
Resource Hub URLs.
"""
from django.urls import path
from .views import ResourceListView, RecommendedResourcesView

urlpatterns = [
    path("", ResourceListView.as_view(), name="resource-list"),
    path("recommended/", RecommendedResourcesView.as_view(), name="resource-recommended"),
]
