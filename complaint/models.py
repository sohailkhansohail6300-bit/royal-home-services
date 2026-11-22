from django.db import models

# Create your models here.

class CustomerComplaint(models.Model):
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    email_address = models.EmailField()
    date_of_service = models.DateField()
    service_address = models.CharField(max_length=255)
    service_details = models.TextField()
    service_type = models.CharField(max_length=100)
    technician_name = models.CharField(max_length=150, blank=True)
    what_went_wrong = models.TextField()
    desired_resolution = models.TextField()
    additional_details = models.TextField(blank=True)
    followup_preference = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name