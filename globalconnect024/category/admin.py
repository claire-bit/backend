from django.contrib import admin
from .models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'icon')
    list_filter = ('vendor',)
    search_fields = ('name',)
