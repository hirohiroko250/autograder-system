from rest_framework import serializers
from .models import TestScheduleInfo

class TestScheduleInfoSerializer(serializers.ModelSerializer):
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TestScheduleInfo
        fields = [
            'id', 'year', 'period', 'period_display', 'planned_date', 
            'actual_date', 'deadline', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']