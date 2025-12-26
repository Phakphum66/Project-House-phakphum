from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from designs.models import HouseDesign


class EstimateInquiry(models.Model):
	class MaterialGrade(models.TextChoices):
		ECONOMY = 'economy', 'Economy'
		STANDARD = 'standard', 'Standard'
		LUXURY = 'luxury', 'Luxury'

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='estimate_inquiries',
	)
	name = models.CharField(max_length=255)
	phone = models.CharField(max_length=50)
	email = models.EmailField()
	land_size = models.PositiveIntegerField()
	house_size = models.PositiveIntegerField()
	material_grade = models.CharField(
		max_length=20,
		choices=MaterialGrade.choices,
	)
	floors = models.PositiveSmallIntegerField()
	estimate_min = models.DecimalField(max_digits=14, decimal_places=2)
	estimate_max = models.DecimalField(max_digits=14, decimal_places=2)
	submitted_at = models.DateTimeField(auto_now_add=True)
	handled = models.BooleanField(default=False)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ['-submitted_at']

	def __str__(self) -> str:
		return f"Estimate inquiry from {self.name} ({self.email})"

	@property
	def material_grade_label(self) -> str:
		return self.get_material_grade_display()


class Quote(models.Model):
	class Status(models.TextChoices):
		DRAFT = 'draft', 'Draft'
		PENDING = 'pending', 'Pending'
		APPROVED = 'approved', 'Approved'

	design = models.ForeignKey(
		HouseDesign,
		on_delete=models.CASCADE,
		related_name='quotes',
		null=True,
		blank=True,
	)
	requested_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='quotes',
	)
	catalog_design = models.ForeignKey(
		'catalog.CatalogDesign',
		on_delete=models.CASCADE,
		related_name='quotes',
		null=True,
		blank=True,
	)
	price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	status = models.CharField(
		max_length=20,
		choices=Status.choices,
		default=Status.PENDING,
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']
		constraints = [
			models.UniqueConstraint(fields=['design', 'requested_by'], name='unique_quote_design_user'),
			models.UniqueConstraint(fields=['catalog_design', 'requested_by'], name='unique_quote_catalog_user'),
		]

	def __str__(self) -> str:
		return f"Quote for {self.reference_name} ({self.get_status_display()})"

	def clean(self):
		super().clean()
		if not self.design and not self.catalog_design:
			raise ValidationError({
				'design': 'Select a custom design or choose a catalog design.',
				'catalog_design': 'Select a catalog design or choose a custom design.',
			})
		if self.design and self.catalog_design:
			raise ValidationError('A quote cannot reference both a custom design and a catalog design.')

	def save(self, *args, **kwargs):
		self.full_clean()
		return super().save(*args, **kwargs)

	@property
	def reference_name(self) -> str:
		if self.design:
			return self.design.title
		if self.catalog_design:
			return self.catalog_design.name
		return 'Unnamed Design'

	@property
	def reference_description(self) -> str:
		if self.design:
			return self.design.description
		if self.catalog_design:
			return self.catalog_design.concept
		return ''

	@property
	def reference_code(self) -> str:
		if self.design_id:
			return f"HD-{self.design_id:04d}"
		if self.catalog_design_id:
			return f"CAT-{self.catalog_design_id:04d}"
		return 'N/A'

	@property
	def is_catalog_source(self) -> bool:
		return bool(self.catalog_design_id and not self.design_id)
