# orders/urls.py

from django.urls import path
from .views import checkout, check_payment_status, mpesa_callback

urlpatterns = [
    path("checkout/", checkout, name="checkout"),
    path("check-status/<int:order_id>/", check_payment_status, name="check_status"),
    path("mpesa/callback/", mpesa_callback),
]