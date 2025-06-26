# models.py
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    class Meta:
        verbose_name = 'Global User'
        verbose_name_plural = 'Global Users'
