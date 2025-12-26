from django.contrib import admin

from .models import CatalogDesign, CatalogDesignImage


class CatalogDesignImageInline(admin.TabularInline):
    model = CatalogDesignImage
    extra = 1
    fields = ("image", "caption", "ordering")


@admin.register(CatalogDesign)
class CatalogDesignAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "base_price",
        "area_sqm",
        "bedrooms",
        "bathrooms",
        "is_featured",
        "created_at",
    )
    list_filter = ("is_featured", "bedrooms", "bathrooms", "created_at")
    search_fields = ("name", "concept")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CatalogDesignImageInline]


@admin.register(CatalogDesignImage)
class CatalogDesignImageAdmin(admin.ModelAdmin):
    list_display = ("design", "ordering", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("design__name", "caption")
    autocomplete_fields = ("design",)
