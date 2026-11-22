from django.contrib import admin
from .models import Review

# Register your models here.
from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('name', 'review')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    list_per_page = 20
    date_hierarchy = 'created_at'