from rest_framework import serializers
from .models import Classroom, ClassroomPermission
from students.models import Student

class ClassroomPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomPermission
        fields = ['can_register_students', 'can_input_scores', 'can_view_reports']

class ClassroomSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    membership_type_display = serializers.CharField(source='school.get_membership_type_display', read_only=True)
    student_count = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = Classroom
        fields = [
            'id', 'classroom_id', 'school', 'school_name', 'name', 
            'membership_type_display', 'student_count', 'permissions',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_student_count(self, obj):
        """この教室の生徒数を取得"""
        return Student.objects.filter(classroom=obj).count()
    
    def get_permissions(self, obj):
        """教室の権限設定を取得"""
        try:
            permission = obj.permissions
            return ClassroomPermissionSerializer(permission).data
        except ClassroomPermission.DoesNotExist:
            # デフォルト権限を返す
            return {
                'can_register_students': True,
                'can_input_scores': True,
                'can_view_reports': True,
            }
    
    def update(self, instance, validated_data):
        """権限データも更新できるようにする"""
        permissions_data = validated_data.pop('permissions', None)
        
        # 基本情報を更新
        instance = super().update(instance, validated_data)
        
        # 権限データがある場合は更新
        if permissions_data is not None:
            permission, created = ClassroomPermission.objects.get_or_create(
                classroom=instance,
                defaults=permissions_data
            )
            if not created:
                for key, value in permissions_data.items():
                    setattr(permission, key, value)
                permission.save()
        
        return instance
    
    def validate(self, data):
        # 作成時のみschoolが必要（Viewで自動設定）
        return data