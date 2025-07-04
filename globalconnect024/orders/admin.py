from django.contrib import admin
from .models import Order, Referral

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['product', 'buyer', 'affiliate', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['product__name', 'buyer__username', 'affiliate__username']
    ordering = ['-created_at']
    autocomplete_fields = ['product', 'buyer', 'affiliate']  # ✅ Smart search for FK fields
    date_hierarchy = 'created_at'  # ✅ Drilldown by date

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['affiliate', 'order', 'commission_earned', 'is_approved', 'is_paid', 'created_at']
    list_filter = ['is_approved', 'is_paid', 'created_at']
    search_fields = ['affiliate__username', 'order__product__name']
    ordering = ['-created_at']
    autocomplete_fields = ['affiliate', 'order']  # ✅ Smart search
    date_hierarchy = 'created_at'  # ✅ Date drilldown
