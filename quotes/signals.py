from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Quote


def _admin_recipients() -> list[str]:
    User = get_user_model()
    emails = [email for email in User.objects.filter(is_superuser=True).values_list("email", flat=True) if email]
    return emails or [settings.DEFAULT_FROM_EMAIL]


@receiver(post_save, sender=Quote)
def notify_admin_on_quote_create(sender, instance: Quote, created: bool, **kwargs):
    if not created:
        return
    subject = "New Quote Requested"
    message = (
        f"A new quote was requested for design '{instance.reference_name}'.\n"
        f"Requested by: {instance.requested_by.get_username()}"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, _admin_recipients())
