from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Product
from .serializers import ProductSerializer
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['stock', 'approved']  # ✅ Allows ?stock=... & ?approved=...
    ordering_fields = ['price', 'stock', 'name']  # ✅ Allows ?ordering=price

    def get_queryset(self):
        user = self.request.user

        if user.role == 'vendor':
            return Product.objects.filter(vendor=user)
        elif user.role == 'admin' or user.is_superuser:
            return Product.objects.all()
        else:
            return Product.objects.filter(approved=True, stock__gt=0)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'vendor':
            raise PermissionDenied("Only approved vendors can add products.")
        serializer.save(vendor=user, approved=True)  # Auto-approve for now

    def perform_update(self, serializer):
        user = self.request.user
        instance = serializer.instance

        if user.role == 'vendor' and instance.vendor != user:
            raise PermissionDenied("You can only edit your own products.")

        if user.role == 'vendor':
            serializer.validated_data.pop('approved', None)

        serializer.save()


# class ProductViewSet(viewsets.ModelViewSet):
#     serializer_class = ProductSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         user = self.request.user

#         if user.role == 'vendor':
#             return Product.objects.filter(vendor=user)
#         elif user.role == 'admin' or user.is_superuser:
#             return Product.objects.all()
#         else:
#             return Product.objects.none()

#     def perform_create(self, serializer):
#         user = self.request.user
#         if user.role != 'vendor':
#             raise PermissionDenied("Only approved vendors can add products.")
#         serializer.save(vendor=user, approved=False)  # ✅ new products are unapproved by default

#     def perform_update(self, serializer):
#         user = self.request.user
#         instance = serializer.instance

#         if user.role == 'vendor' and instance.vendor != user:
#             raise PermissionDenied("You can only edit your own products.")
        
#         # Prevent vendors from modifying `approved` status
#         if user.role == 'vendor':
#             serializer.validated_data.pop('approved', None)
        
#         serializer.save()