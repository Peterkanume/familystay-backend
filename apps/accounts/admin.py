from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'email_verified', 'phone_verified', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'email_verified', 'phone_verified', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Verification', {
            'fields': ('role', 'phone_number', 'profile_picture', 'email_verified', 'phone_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Verification', {
            'fields': ('role', 'phone_number')
        }),
    )
    
    list_select_related = ()
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    actions = ['verify_email', 'verify_phone', 'activate_users', 'deactivate_users']
    
    def verify_email(self, request, queryset):
        queryset.update(email_verified=True)
    verify_email.short_description = 'Mark selected users as email verified'
    
    def verify_phone(self, request, queryset):
        queryset.update(phone_verified=True)
    verify_phone.short_description = 'Mark selected users as phone verified'
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = 'Deactivate selected users'
