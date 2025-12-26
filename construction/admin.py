from django.contrib import admin

from .models import ConstructionProject, ProgressUpdate


class ProgressUpdateInline(admin.TabularInline):
	model = ProgressUpdate
	extra = 0
	fields = ("stage_name", "update_date", "description", "site_image")


@admin.register(ConstructionProject)
class ConstructionProjectAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"owner",
		"quote",
		"start_date",
		"expected_end_date",
		"total_progress",
		"created_at",
	)
	list_filter = ("start_date", "expected_end_date", "total_progress")
	search_fields = ("owner__username", "quote__design__title")
	readonly_fields = ("created_at", "updated_at")
	autocomplete_fields = ("owner", "quote")
	inlines = [ProgressUpdateInline]


@admin.register(ProgressUpdate)
class ProgressUpdateAdmin(admin.ModelAdmin):
	list_display = ("project", "stage_name", "update_date", "created_at")
	list_filter = ("update_date",)
	search_fields = ("project__owner__username", "stage_name")
