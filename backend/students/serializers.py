from rest_framework import serializers
from .models import Student, StudentEnrollment

class StudentSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    year = serializers.IntegerField(write_only=True, required=False)
    period = serializers.CharField(write_only=True, required=False)
    latest_enrollment = serializers.SerializerMethodField()
    student_id = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Student
        fields = ['id', 'student_id', 'classroom', 'classroom_name', 'name', 'grade', 'is_active', 'created_at', 'updated_at', 'year', 'period', 'latest_enrollment']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_latest_enrollment(self, obj):
        latest = obj.enrollments.filter(is_active=True).order_by('-year', '-period').first()
        if latest:
            return {
                'year': str(latest.year),
                'period': latest.period
            }
        return None

    def create(self, validated_data):
        from .utils import generate_student_id

        year = validated_data.pop('year', None)
        period = validated_data.pop('period', None)

        # student_idが指定されていない場合、自動生成
        if 'student_id' not in validated_data or not validated_data.get('student_id'):
            classroom = validated_data.get('classroom')
            if classroom:
                validated_data['student_id'] = generate_student_id(classroom)

        student = Student.objects.create(**validated_data)

        # 年度と期間が指定されている場合、StudentEnrollmentを作成
        if year and period:
            StudentEnrollment.objects.create(
                student=student,
                year=year,
                period=period
            )

        return student

class StudentEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    classroom_name = serializers.CharField(source='student.classroom.name', read_only=True)
    
    class Meta:
        model = StudentEnrollment
        fields = ['id', 'student', 'student_name', 'student_id', 'classroom_name', 'year', 'period', 'is_active', 'enrolled_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'enrolled_at', 'created_at', 'updated_at']

class StudentImportSerializer(serializers.Serializer):
    file = serializers.FileField()
    year = serializers.IntegerField(required=False)
    period = serializers.CharField(required=False)
    
    def validate_file(self, value):
        if not value.name.endswith('.xlsx'):
            raise serializers.ValidationError('xlsx ファイルのみ対応しています')
        return value