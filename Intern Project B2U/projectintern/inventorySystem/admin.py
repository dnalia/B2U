from django.contrib import admin
from .models import User, TechRefresh

# --- Custom display for User model ---
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'role')

# --- Custom display for TechRefresh model ---
@admin.register(TechRefresh)
class TechRefreshAdmin(admin.ModelAdmin):
    list_display = (
        'engineer_name', 'user_name', 'location',
        'status', 'format_status', 'upload_status'
    )
    list_filter = ('status', 'format_status', 'upload_status')
    search_fields = ('engineer_name', 'user_name', 'location')