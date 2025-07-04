from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    # Auth
    RegisterView,
    ActivateAccount,
    ResendActivationEmail,
    LogoutView,
    CurrentUserView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UpdateProfileView,
    EmailOrUsernameTokenObtainPairView,

    # Affiliate
    affiliate_summary,
    affiliate_referrals,

    # Admin
    admin_user_list,
    toggle_user_status,
    admin_product_list,
    toggle_product_visibility,
    admin_commission_logs,
    approve_commission,
    mark_commission_paid,
    system_logs,
)

urlpatterns = [
    # 🔐 Authentication & Registration
    path('login/', EmailOrUsernameTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('auth/activate/<uidb64>/<token>/', ActivateAccount.as_view(), name='activate'),
    path('registration/resend-email/', ResendActivationEmail.as_view(), name='resend_activation_email'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # 👤 Profile Management
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('update/', UpdateProfileView.as_view(), name='update_profile'),

    # 🔑 Password Reset
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # 📊 Affiliate Dashboard
    path('affiliate/summary/', affiliate_summary, name='affiliate_summary'),
    path('affiliate/referrals/', affiliate_referrals, name='affiliate_referrals'),

    # 🛠️ Admin Endpoints
    path('admin/users/', admin_user_list, name='admin_user_list'),
    path('admin/users/<int:user_id>/status/', toggle_user_status, name='toggle_user_status'),
    path('admin/products/', admin_product_list, name='admin_product_list'),
    path('admin/products/<int:product_id>/toggle/', toggle_product_visibility, name='toggle_product_visibility'),
    path('admin/commissions/', admin_commission_logs, name='admin_commission_logs'),
    path('admin/commissions/<int:referral_id>/approve/', approve_commission, name='approve_commission'),
    path('admin/commissions/<int:referral_id>/payout/', mark_commission_paid, name='payout_commission'),
    path('admin/system-logs/', system_logs, name='system_logs'),
]
