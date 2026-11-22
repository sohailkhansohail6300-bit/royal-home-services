from django.contrib import admin
from .models import EmployeeRegistration
# Register your models here.

admin.site.register(EmployeeRegistration)

class EmployeeRegistrationAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'department', 'em_location', 'created_at')
    search_fields = ('username', 'email', 'phone_number', 'department')
    list_filter = ('department','em_location', 'created_at')
