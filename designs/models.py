from django.conf import settings
from django.db import models


class HouseDesign(models.Model):
	title = models.CharField(max_length=200)
	description = models.TextField()
	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='house_designs',
	)
	cover_image = models.ImageField(
		upload_to='designs/covers/',
		blank=True,
		null=True,
	)
	floor_plan = models.FileField(
		upload_to='designs/floor_plans/',
		blank=True,
		null=True,
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self) -> str:
		return self.title
