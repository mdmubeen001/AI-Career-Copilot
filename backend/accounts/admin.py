from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Profile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.
    """
    ordering = ('email',)
    list_display = ('email', 'username', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'first_name', 'last_name')}),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password'),
            },
        ),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for User Profile.
    """
    list_display = ('user', 'full_name', 'degree', 'college', 'graduation_year', 'created_at')
    search_fields = ('user__email', 'full_name', 'college', 'degree', 'career_goal')
    list_filter = ('degree', 'graduation_year', 'created_at')
