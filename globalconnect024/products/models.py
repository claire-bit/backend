from django.db import models
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()  # ✅ Get the custom user model

class Product(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    approved = models.BooleanField(default=True)  # ✅ Admin approval

    def __str__(self):
        return self.name


# , null=True, blank=True)