from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Displayed columns in the user list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')

    # Fields you can search by
    search_fields = ('username', 'email', 'first_name', 'last_name')

    # Filters on the right sidebar
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    # Field sections when editing a user
    fieldsets = (
        (_('Login Info'), {'fields': ('username', 'password')}),
        (_('Personal Info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important Dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Fields shown when creating a user via admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    ordering = ('username',)
