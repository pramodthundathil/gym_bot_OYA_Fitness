from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Subscription

@receiver(post_save, sender=Subscription)
def update_member_status(sender, instance, **kwargs):
    if instance.Member:
        instance.Member.update_active_status()