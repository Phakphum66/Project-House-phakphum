from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView

from designs.models import HouseDesign
from quotes.models import Quote

from .forms import CatalogDesignForm
from .models import CatalogDesign


class CatalogDesignListView(ListView):
    model = CatalogDesign
    template_name = "catalog/catalog_list.html"
    context_object_name = "designs"
    paginate_by = 9

    def get_queryset(self):
        queryset = (
            CatalogDesign.objects.all()
            .prefetch_related("gallery_images")
            .annotate(quotes_count=Count("quotes", distinct=True))
        )
        params = self.request.GET
        search = params.get("q", "").strip()
        price_min = params.get("price_min")
        price_max = params.get("price_max")
        area_min = params.get("area_min")
        area_max = params.get("area_max")
        bedrooms = params.get("bedrooms")

        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(concept__icontains=search))
        # Handle Dashboard Presets (Budget)
        budget = params.get("budget")
        if budget == "3m":
            queryset = queryset.filter(base_price__lte=3000000)
        elif budget == "3-5m":
            queryset = queryset.filter(base_price__gte=3000000, base_price__lte=5000000)
        elif budget == "5-10m":
            queryset = queryset.filter(base_price__gte=5000000, base_price__lte=10000000)
        elif budget == "10m+":
            queryset = queryset.filter(base_price__gte=10000000)

        # Handle Dashboard Presets (Area)
        area = params.get("area")
        if area == "s":
            queryset = queryset.filter(area_sqm__lt=150)
        elif area == "m":
            queryset = queryset.filter(area_sqm__gte=150, area_sqm__lte=250)
        elif area == "l":
            queryset = queryset.filter(area_sqm__gt=250)

        # Handle Style
        style = params.get("style")
        if style:
            queryset = queryset.filter(style=style)

        # Fallback/Advanced Filters (Manual inputs)
        if price_min:
            try:
                queryset = queryset.filter(base_price__gte=float(price_min))
            except ValueError:
                pass
        if price_max:
            try:
                queryset = queryset.filter(base_price__lte=float(price_max))
            except ValueError:
                pass
        if area_min:
            try:
                queryset = queryset.filter(area_sqm__gte=int(area_min))
            except ValueError:
                pass
        if area_max:
            try:
                queryset = queryset.filter(area_sqm__lte=int(area_max))
            except ValueError:
                pass
        if bedrooms:
            try:
                queryset = queryset.filter(bedrooms__gte=int(bedrooms))
            except ValueError:
                pass

        sort = params.get("sort", "featured")
        if sort == "price_asc":
            queryset = queryset.order_by("base_price")
        elif sort == "price_desc":
            queryset = queryset.order_by("-base_price")
        elif sort == "popularity":
            queryset = queryset.order_by("-quotes_count", "name")
        else:
            queryset = queryset.order_by("-is_featured", "name")

        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        params_copy = self.request.GET.copy()
        if "page" in params_copy:
            params_copy.pop("page")
        context["query_string"] = params_copy.urlencode()
        context["filters"] = {
            "q": self.request.GET.get("q", ""),
            "price_min": self.request.GET.get("price_min", ""),
            "price_max": self.request.GET.get("price_max", ""),
            "area_min": self.request.GET.get("area_min", ""),
            "area_max": self.request.GET.get("area_max", ""),
            "bedrooms": self.request.GET.get("bedrooms", ""),
            "sort": self.request.GET.get("sort", "featured"),
        }
        context["bedroom_options"] = ("2", "3", "4", "5")
        return context


class CatalogDesignDetailView(DetailView):
    model = CatalogDesign
    template_name = "catalog/design_detail.html"
    context_object_name = "design"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["related_designs"] = (
            CatalogDesign.objects.exclude(pk=self.object.pk)
            .order_by("-is_featured", "name")[:3]
        )
        return context


class CatalogDesignQuoteView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, slug: str, *args: Any, **kwargs: Any) -> HttpResponse:
        design = get_object_or_404(CatalogDesign, slug=slug)
        quote, created = Quote.objects.get_or_create(
            requested_by=request.user,
            catalog_design=design,
            defaults={
                "price": design.base_price,
                "status": Quote.Status.DRAFT,
            },
        )
        if not created and quote.price is None:
            quote.price = design.base_price
            quote.save(update_fields=["price"])
        messages.success(request, "เพิ่มแบบบ้านจากแค็ตตาล็อกไปยังใบเสนอราคาของคุณแล้ว")
        return redirect(reverse("quotes:list"))


class CatalogDesignCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CatalogDesign
    form_class = CatalogDesignForm
    template_name = "catalog/catalog_form.html"

    def test_func(self) -> bool:
        return self.request.user.is_superuser

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        self.prefill_source: HouseDesign | None = None
        if self.request.method == "GET":
            source_id = self.request.GET.get("source_design")
            if source_id:
                self.prefill_source = HouseDesign.objects.filter(pk=source_id).first()
                if self.prefill_source:
                    kwargs["source_design"] = self.prefill_source
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["design_sources"] = (
            HouseDesign.objects.select_related("owner").order_by("-created_at")[:6]
        )
        context["prefill_source"] = getattr(self, "prefill_source", None)
        return context

    def form_valid(self, form: CatalogDesignForm) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, "เพิ่มแบบบ้านลงในแค็ตตาล็อกเรียบร้อยแล้ว")
        return response

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class CatalogDesignDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CatalogDesign
    template_name = "catalog/catalog_design_confirm_delete.html"
    success_url = reverse_lazy("catalog:list")
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def test_func(self) -> bool:
        return self.request.user.is_superuser

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "ลบแบบบ้านเรียบร้อยแล้ว")
        return super().delete(request, *args, **kwargs)
