from django.urls import path

from .views import (
    HouseDesignCreateView,
    HouseDesignDeleteView,
    HouseDesignDetailView,
    HouseDesignListView,
    HouseDesignUpdateView,
)

app_name = "designs"

urlpatterns = [
    path("", HouseDesignListView.as_view(), name="list"),
    path("create/", HouseDesignCreateView.as_view(), name="create"),
    path("<int:pk>/", HouseDesignDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", HouseDesignUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", HouseDesignDeleteView.as_view(), name="delete"),
]
