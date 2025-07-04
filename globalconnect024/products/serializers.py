# products/serializers.py
from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.SerializerMethodField()  # ✅ new field

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'image', 'stock', 'approved', 'vendor_name']
        read_only_fields = ['id', 'vendor', 'approved']

    image = serializers.ImageField(required=False, allow_null=True)

    def get_vendor_name(self, obj):
        return obj.vendor.first_name or obj.vendor.username if obj.vendor else None
