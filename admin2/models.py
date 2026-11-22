from django.db import models

# Create your models here.

class Review(models.Model):
    name        = models.CharField(max_length=100)
    review      = models.TextField(max_length=2000)
    created_at  = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} · {self.created_at:%Y-%m-%d}"