# users/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    ActivateAccount,
    ResendActivationEmail,
    LogoutView,
    CurrentUserView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UpdateProfileView,
    affiliate_summary,
    affiliate_referrals,
)

urlpatterns = [
    # ✅ JWT Authentication
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ✅ Registration & Activation
    path('register/', RegisterView.as_view(), name='register'),
    path('auth/activate/<uidb64>/<token>/', ActivateAccount.as_view(), name='activate'),
    path('registration/resend-email/', ResendActivationEmail.as_view(), name='resend_activation_email'),

    # ✅ Logout
    path('logout/', LogoutView.as_view(), name='logout'),

    # ✅ Profile Management
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('update/', UpdateProfileView.as_view(), name='update_profile'),

    # ✅ Password Reset
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # ✅ Affiliate Dashboard Endpoints
    path('affiliate/summary/', affiliate_summary, name='affiliate_summary'),
    path('affiliate/referrals/', affiliate_referrals, name='affiliate_referrals'),
]
