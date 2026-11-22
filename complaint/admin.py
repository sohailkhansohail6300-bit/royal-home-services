from django.contrib import admin
from .models import CustomerComplaint
# Register your models here.
admin.site.register(CustomerComplaint)
class CustomerComplaintAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'email_address', 'date_of_service', 'service_address', 'service_details', 'service_type', 'technician_name', 'what_went_wrong', 'desired_resolution', 'additional_details', 'followup_preference', 'created_at')
    search_fields = ('full_name', 'phone_number', 'email_address', 'service_address', 'service_details', 'service_type', 'technician_name')
    list_filter = ('service_type','date_of_service','created_at')
