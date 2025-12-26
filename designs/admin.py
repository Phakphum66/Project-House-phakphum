from django.contrib import admin

from .models import HouseDesign


@admin.register(HouseDesign)
class HouseDesignAdmin(admin.ModelAdmin):
	list_display = ("title", "owner", "created_at")
	search_fields = ("title", "description", "owner__username")
	list_filter = ("created_at",)
	readonly_fields = ("created_at",)
