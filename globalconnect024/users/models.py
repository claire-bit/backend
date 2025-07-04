from django.db import models 
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Affiliate'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin'),  # optional
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    promotion_methods = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Global User'
        verbose_name_plural = 'Global Users'
