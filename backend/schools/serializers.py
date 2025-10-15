from rest_framework import serializers
from .models import School

class SchoolSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = School
        fields = [
            'id', 'school_id', 'name', 'email', 'phone', 'address', 
            'membership_type', 'can_register_students', 'can_input_scores', 'can_view_reports',
            'permissions', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_permissions(self, obj):
        """権限設定をオブジェクト形式で返す（フロントエンド互換性のため）"""
        return {
            'can_register_students': obj.can_register_students,
            'can_input_scores': obj.can_input_scores,
            'can_view_reports': obj.can_view_reports,
        }