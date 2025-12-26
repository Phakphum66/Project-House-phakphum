from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from quotes.models import Quote


class ConstructionProject(models.Model):
	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='construction_projects',
	)
	quote = models.OneToOneField(
		Quote,
		on_delete=models.SET_NULL,
		related_name='project',
		blank=True,
		null=True,
	)
	start_date = models.DateField()
	expected_end_date = models.DateField()
	total_progress = models.PositiveIntegerField(
		default=0,
		validators=[MinValueValidator(0), MaxValueValidator(100)],
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self) -> str:
		if self.quote:
			return f"Project for {self.quote.reference_name}"
		return f"Project for {self.owner.get_username()}"


class ProgressUpdate(models.Model):
	project = models.ForeignKey(
		ConstructionProject,
		on_delete=models.CASCADE,
		related_name='updates',
	)
	stage_name = models.CharField(max_length=120)
	description = models.TextField()
	site_image = models.ImageField(
		upload_to='construction/updates/',
		blank=True,
		null=True,
	)
	update_date = models.DateField(default=timezone.now)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-update_date', '-created_at']

	def __str__(self) -> str:
		return f"{self.stage_name} update for {self.project}"
