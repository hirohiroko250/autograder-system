from django.contrib import admin
from .models import TestScheduleInfo

@admin.register(TestScheduleInfo)
class TestScheduleInfoAdmin(admin.ModelAdmin):
    list_display = ['year', 'period', 'planned_date', 'actual_date', 'deadline', 'status']
    list_filter = ['year', 'period', 'status']
    search_fields = ['year']
    ordering = ['-year', 'period']