from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet  # ✅ Make sure this is imported

router = DefaultRouter()
router.register('', ProductViewSet, basename='products')

urlpatterns = [
    path('', include(router.urls)),  # ✅ Enables /products/, /products/<id>/ etc.
]
