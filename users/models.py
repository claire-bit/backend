# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model


class CustomUser(AbstractUser):
    class Meta:
        verbose_name = 'Global User'
        verbose_name_plural = 'Global Users'


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('scheduled', 'Scheduled'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    tags = models.JSONField(default=list)  # Or use ManyToMany if you have a Tag model
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    featured_image = models.URLField(blank=True)
    publish_date = models.DateField(null=True, blank=True)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.TextField(max_length=160, blank=True)

    def __str__(self):
        return self.title
