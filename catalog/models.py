from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class CatalogDesign(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    concept = models.TextField()
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    area_sqm = models.PositiveIntegerField()
    bedrooms = models.PositiveSmallIntegerField()
    bathrooms = models.PositiveSmallIntegerField()
    dimensions = models.CharField(max_length=120)
    cover_image = models.ImageField(upload_to="catalog/covers/")
    floor_plan_image = models.ImageField(upload_to="catalog/floor_plans/", blank=True, null=True)
    class Style(models.TextChoices):
        MODERN = "modern", "Modern"
        NORDIC = "nordic", "Nordic"
        CONTEMPORARY = "contemporary", "Contemporary"
        LUXURY = "luxury", "Luxury"
        TROPICAL = "tropical", "Tropical"
        OTHER = "other", "Other"

    style = models.CharField(
        max_length=20,
        choices=Style.choices,
        default=Style.MODERN,
        verbose_name="House Style",
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "name"]
        verbose_name = "Catalog Design"
        verbose_name_plural = "Catalog Designs"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        # Ensure slug is generated and non-empty. If name slugifies to empty, fallback to unique token.
        if not self.slug or not str(self.slug).strip():
            base_slug = slugify(self.name or "")
            if not base_slug:
                # Fallback when name is empty or slugifies to empty: use deterministic base with random token.
                import uuid
                base_slug = f"design-{uuid.uuid4().hex[:8]}"
            slug = base_slug
            suffix = 1
            while CatalogDesign.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        from django.urls import reverse

        return reverse("catalog:design_detail", kwargs={"slug": self.slug})

    @property
    def badge_label(self) -> str | None:
        if self.is_featured:
            return "Best Seller"
        if self.created_at and (timezone.now() - self.created_at) <= timedelta(days=30):
            return "New Arrival"
        return None


class CatalogDesignImage(models.Model):
    design = models.ForeignKey(
        CatalogDesign,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image = models.ImageField(upload_to="catalog/gallery/")
    caption = models.CharField(max_length=255, blank=True)
    ordering = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_catalog_images",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordering", "id"]
        verbose_name = "Catalog Design Image"
        verbose_name_plural = "Catalog Design Images"

    def __str__(self) -> str:
        return f"Image for {self.design.name}"
