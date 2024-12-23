from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import RegisterBlog

class CustomUserAdmin(UserAdmin):
    model = RegisterBlog
    ordering = ['Email']
    list_display = ('First_name', 'Last_name', 'Email', 'name', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('Email', 'name', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Personal Info', {'fields': ('First_name', 'Last_name')}),
    )
    add_fieldsets = (
        (None, {'fields': ('Email', 'password1', 'password2')}),
        ('Personal info', {'fields': ('First_name', 'Last_name')}),
    )

admin.site.register(RegisterBlog, CustomUserAdmin)
