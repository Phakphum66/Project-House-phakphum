from django.contrib import admin

from .models import EstimateInquiry, Quote


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
	list_display = ("reference_label", "requested_by", "status", "price", "created_at")
	list_filter = ("status", "created_at", "catalog_design")
	search_fields = ("design__title", "catalog_design__name", "requested_by__username")
	autocomplete_fields = ("design", "catalog_design", "requested_by")
	list_select_related = ("design", "catalog_design", "requested_by")

	@admin.display(description="แบบบ้าน")
	def reference_label(self, obj: Quote) -> str:
		return obj.reference_name


@admin.register(EstimateInquiry)
class EstimateInquiryAdmin(admin.ModelAdmin):
	list_display = (
		"name",
		"email",
		"phone",
		"material_grade",
		"house_size",
		"floors",
		"submitted_at",
		"handled",
	)
	list_filter = ("handled", "material_grade", "submitted_at")
	search_fields = ("name", "email", "phone")
	readonly_fields = ("submitted_at", "user", "estimate_min", "estimate_max")
