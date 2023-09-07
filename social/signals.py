from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile, Friend

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_for_new_user(sender, **kwargs):
    if kwargs['created']:
        user = UserProfile.objects.create(user=kwargs['instance'])
        Friend.objects.create(user=user)
