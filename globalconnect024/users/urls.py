# accounts/urls.py
from django.urls import path
from .views import RegisterView, ActivateAccount
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/activate/<uidb64>/<token>/', ActivateAccount.as_view(), name='activate'),
]
