from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenRefreshView
from users.views import EmailOrUsernameTokenObtainPairView  # ✅ custom login view

urlpatterns = [
    path('admin/', admin.site.urls),

    # ✅ Auth
    path('api/token/', EmailOrUsernameTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ✅ Merge users and admin views here
    path('api/', include('users.urls')),  # 👈 this exposes /api/admin/users/ etc. correctly

    # ✅ Other apps
    path('api/products/', include('products.urls')),
    path('api/', include('category.urls')),
]

# ✅ Serve media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
