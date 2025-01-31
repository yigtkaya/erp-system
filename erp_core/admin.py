from django.contrib import admin
from .models import Customer, Department, User

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'created_at', 'modified_at')
    search_fields = ('code', 'name')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'modified_at')

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff')
    filter_horizontal = ('departments',)
    search_fields = ('username', 'email')

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

admin.site.register(Customer, CustomerAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Department, DepartmentAdmin) 