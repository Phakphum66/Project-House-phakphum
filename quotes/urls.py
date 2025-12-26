from django.urls import path

from .views import (
    QuoteCreateView,
    QuoteDetailView,
    QuoteListView,
    QuoteUpdateView,
    QuoteDeleteView,
    create_estimate_inquiry,
    download_contract_pdf,
)

app_name = "quotes"

urlpatterns = [
    path("", QuoteListView.as_view(), name="list"),
    path("create/", QuoteCreateView.as_view(), name="create"),
    path("<int:pk>/", QuoteDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", QuoteUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", QuoteDeleteView.as_view(), name="delete"),
    path("<int:quote_id>/contract/pdf/", download_contract_pdf, name="contract-pdf"),
    path("estimator/inquiry/", create_estimate_inquiry, name="estimator_inquiry"),
]
