from rest_framework import serializers
from .models import TestSchedule, TestDefinition, QuestionGroup, Question, AnswerKey

class TestScheduleSerializer(serializers.ModelSerializer):
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    
    class Meta:
        model = TestSchedule
        fields = '__all__'
    
    def get_start_date(self, obj):
        """実施開始日を取得 (actual_date > planned_date)"""
        return obj.actual_date or obj.planned_date
    
    def get_end_date(self, obj):
        """実施終了日を取得 (deadline_atの日付部分)"""
        return obj.deadline_at.date() if obj.deadline_at else None

class QuestionSerializer(serializers.ModelSerializer):
    group_title = serializers.CharField(source='group.title', read_only=True)
    
    class Meta:
        model = Question
        fields = '__all__'

class QuestionGroupSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuestionGroup
        fields = '__all__'

class TestDefinitionSerializer(serializers.ModelSerializer):
    schedule_info = TestScheduleSerializer(source='schedule', read_only=True)
    grade_level_display = serializers.CharField(source='get_grade_level_display', read_only=True)
    subject_display = serializers.CharField(source='get_subject_display', read_only=True)
    question_groups = QuestionGroupSerializer(many=True, read_only=True)
    
    class Meta:
        model = TestDefinition
        fields = '__all__'

class AnswerKeySerializer(serializers.ModelSerializer):
    question_info = QuestionSerializer(source='question', read_only=True)
    
    class Meta:
        model = AnswerKey
        fields = '__all__'