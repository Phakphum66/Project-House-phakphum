from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ProgressUpdate


@receiver(post_save, sender=ProgressUpdate)
def notify_user_on_progress_update(sender, instance: ProgressUpdate, created: bool, **kwargs):
    if not created:
        return
    owner = instance.project.owner
    recipient_list = [owner.email] if owner.email else [settings.DEFAULT_FROM_EMAIL]
    subject = f"Construction Update: {instance.stage_name}"
    message = (
        f"Your construction project has a new update.\n"
        f"Stage: {instance.stage_name}\n"
        f"Date: {instance.update_date}\n"
        f"Details: {instance.description[:500]}"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
