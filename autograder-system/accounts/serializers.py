from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import User

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['school_id'] = user.school_id
        token['classroom_id'] = user.classroom_id
        token['role'] = user.role
        return token

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('認証に失敗しました')

        refresh = self.get_token(user)

        # 教室管理者の場合、権限情報を取得
        permissions = None
        if user.role == 'classroom_admin' and user.classroom_id:
            from classrooms.models import Classroom, ClassroomPermission
            try:
                classroom = Classroom.objects.get(classroom_id=user.classroom_id)
                try:
                    permission = classroom.permissions
                    permissions = {
                        'can_register_students': permission.can_register_students,
                        'can_input_scores': permission.can_input_scores,
                        'can_view_reports': permission.can_view_reports,
                    }
                except ClassroomPermission.DoesNotExist:
                    # デフォルト権限
                    permissions = {
                        'can_register_students': True,
                        'can_input_scores': True,
                        'can_view_reports': True,
                    }
            except Classroom.DoesNotExist:
                pass

        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'school_id': user.school_id,
            'classroom_id': user.classroom_id,
        }

        if permissions is not None:
            user_data['permissions'] = permissions

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data
        }

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('現在のパスワードが正しくありません')
        return value

class UserSerializer(serializers.ModelSerializer):
    classroom_name = serializers.SerializerMethodField()
    school_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'school_id', 'classroom_id', 'is_active', 'classroom_name', 'school_name', 'permissions']
        read_only_fields = ['id', 'username']

    def get_classroom_name(self, obj):
        if obj.role == 'classroom_admin' and obj.classroom_id:
            from classrooms.models import Classroom
            try:
                classroom = Classroom.objects.get(classroom_id=obj.classroom_id)
                return classroom.name
            except Classroom.DoesNotExist:
                return None
        return None

    def get_school_name(self, obj):
        if obj.school_id:
            from schools.models import School
            try:
                school = School.objects.get(school_id=obj.school_id)
                return school.name
            except School.DoesNotExist:
                return None
        return None

    def get_permissions(self, obj):
        """教室管理者の場合、権限情報を取得"""
        if obj.role == 'classroom_admin' and obj.classroom_id:
            from classrooms.models import Classroom, ClassroomPermission
            try:
                classroom = Classroom.objects.get(classroom_id=obj.classroom_id)
                try:
                    permission = classroom.permissions
                    return {
                        'can_register_students': permission.can_register_students,
                        'can_input_scores': permission.can_input_scores,
                        'can_view_reports': permission.can_view_reports,
                    }
                except ClassroomPermission.DoesNotExist:
                    # デフォルト権限
                    return {
                        'can_register_students': True,
                        'can_input_scores': True,
                        'can_view_reports': True,
                    }
            except Classroom.DoesNotExist:
                pass
        return None