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


class Product(models.Model):
    vendor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'vendor'})
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    affiliate = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='affiliate_orders')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.buyer.username}"


class Referral(models.Model):
    affiliate = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referrals')
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    commission_earned = models.DecimalField(max_digits=10, decimal_places=2)
    is_approved = models.BooleanField(default=False)  # ✅ Admin approval
    is_paid = models.BooleanField(default=False)      # ✅ Payout tracking
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Referral by {self.affiliate.username} - {self.order.product.name}"
       
