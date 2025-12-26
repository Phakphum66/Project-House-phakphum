from django.urls import path

from .views import (
    ConstructionProjectCreateView,
    ConstructionProjectDetailView,
    ConstructionProjectDeleteView,
    ConstructionProjectListView,
    ConstructionProjectUpdateView,
    ProgressUpdateCreateView,
)

app_name = "construction"

urlpatterns = [
    path("", ConstructionProjectListView.as_view(), name="list"),
    path("create/", ConstructionProjectCreateView.as_view(), name="create"),
    path("<int:pk>/", ConstructionProjectDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", ConstructionProjectUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", ConstructionProjectDeleteView.as_view(), name="delete"),
    path("<int:project_pk>/updates/new/", ProgressUpdateCreateView.as_view(), name="progress-create"),
]
