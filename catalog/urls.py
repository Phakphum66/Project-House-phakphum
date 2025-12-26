from django.urls import path

from .views import (
    CatalogDesignCreateView,
    CatalogDesignDeleteView,
    CatalogDesignDetailView,
    CatalogDesignListView,
    CatalogDesignQuoteView,
)

app_name = "catalog"

urlpatterns = [
    path("", CatalogDesignListView.as_view(), name="list"),
    path("create/", CatalogDesignCreateView.as_view(), name="create"),
    path("<slug:slug>/", CatalogDesignDetailView.as_view(), name="design_detail"),
    path("<slug:slug>/quote/", CatalogDesignQuoteView.as_view(), name="get_quote"),
    path("<slug:slug>/delete/", CatalogDesignDeleteView.as_view(), name="delete"),
]
