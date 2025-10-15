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
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'school_id': user.school_id,
                'classroom_id': user.classroom_id,
            }
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
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'school_id', 'classroom_id', 'is_active', 'classroom_name', 'school_name']
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