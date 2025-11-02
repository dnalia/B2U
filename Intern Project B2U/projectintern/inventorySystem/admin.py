from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, TechRefresh, AssignedTask, Request, Notification

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_superuser')

admin.site.register(User, CustomUserAdmin)

# Register TechRefresh only once
@admin.register(TechRefresh)
class TechRefreshAdmin(admin.ModelAdmin):
    list_display = ('engineer_name', 'user_name', 'status')

admin.site.register(AssignedTask)
admin.site.register(Request)
admin.site.register(Notification)