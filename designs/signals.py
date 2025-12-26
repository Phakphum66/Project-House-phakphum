from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import HouseDesign


def _admin_recipients() -> list[str]:
    User = get_user_model()
    emails = [email for email in User.objects.filter(is_superuser=True).values_list("email", flat=True) if email]
    return emails or [settings.DEFAULT_FROM_EMAIL]


@receiver(post_save, sender=HouseDesign)
def notify_admin_on_design_create(sender, instance: HouseDesign, created: bool, **kwargs):
    if not created:
        return
    subject = "New House Design Submitted"
    message = (
        f"A new house design titled '{instance.title}' was created by {instance.owner.get_username()}\n"
        f"Description: {instance.description[:200]}"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, _admin_recipients())
