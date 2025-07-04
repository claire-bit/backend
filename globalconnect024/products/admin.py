from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'price', 'stock', 'approved', 'is_active', 'created_at']
    list_filter = ['approved', 'is_active', 'vendor', 'created_at']
    search_fields = ['name', 'description', 'vendor__username']
    ordering = ['-created_at']
    list_editable = ['approved', 'is_active', 'stock']
