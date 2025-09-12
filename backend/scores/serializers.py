from rest_framework import serializers
from .models import (
    Score, TestResult, CommentTemplate, QuestionScore, TestAttendance,
    StudentComment, TestComment, CommentTemplateV2, PastDataImport, IndividualProblem, IndividualProblemScore
)
from students.serializers import StudentSerializer
from tests.serializers import TestDefinitionSerializer

class ScoreSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    test_name = serializers.CharField(source='test.name', read_only=True)
    question_title = serializers.CharField(source='question.group.title', read_only=True)
    
    class Meta:
        model = Score
        fields = '__all__'

class TestResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    test_name = serializers.CharField(source='test.name', read_only=True)
    school_name = serializers.CharField(source='student.classroom.school.name', read_only=True)
    classroom_name = serializers.CharField(source='student.classroom.name', read_only=True)
    
    class Meta:
        model = TestResult
        fields = '__all__'

class CommentTemplateSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    subject_display = serializers.CharField(source='get_subject_display', read_only=True)
    
    class Meta:
        model = CommentTemplate
        fields = '__all__'



class QuestionScoreSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    test_name = serializers.CharField(source='test.name', read_only=True)
    question_number = serializers.IntegerField(source='question.question_number', read_only=True)
    question_title = serializers.CharField(source='question.question_text', read_only=True)
    max_score = serializers.IntegerField(source='question.max_score', read_only=True)
    group_number = serializers.IntegerField(source='question.group.group_number', read_only=True)
    
    class Meta:
        model = QuestionScore
        fields = '__all__'
        read_only_fields = ['is_correct']


class TestAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    test_name = serializers.CharField(source='test.name', read_only=True)
    attendance_status_display = serializers.CharField(source='get_attendance_status_display', read_only=True)
    is_present = serializers.BooleanField(read_only=True)
    can_take_full_test = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TestAttendance
        fields = '__all__'


class DetailedScoreInputSerializer(serializers.Serializer):
    """問題ごとの詳細スコア入力用シリアライザー"""
    test_id = serializers.IntegerField()
    student_id = serializers.CharField()
    attendance_status = serializers.IntegerField(default=1)
    attendance_reason = serializers.CharField(required=False, allow_blank=True)
    question_scores = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    
    def validate_question_scores(self, value):
        """問題スコアのバリデーション"""
        from tests.models import Question
        
        test_id = self.initial_data.get('test_id')
        if not test_id:
            raise serializers.ValidationError("test_idが必要です")
        
        for item in value:
            question_id = item.get('question_id')
            score = item.get('score')
            
            if not question_id:
                raise serializers.ValidationError("question_idが必要です")
            
            try:
                question = Question.objects.get(id=question_id, group__test_id=test_id)
                if score < 0 or score > question.max_score:
                    raise serializers.ValidationError(
                        f"問題{question.question_number}の得点が範囲外です (0-{question.max_score})"
                    )
            except Question.DoesNotExist:
                raise serializers.ValidationError(f"問題ID {question_id} が見つかりません")
        
        return value


class StudentCommentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    test_name = serializers.CharField(source='test.name', read_only=True, allow_null=True)
    comment_type_display = serializers.CharField(source='get_comment_type_display', read_only=True)
    visibility_display = serializers.CharField(source='get_visibility_display', read_only=True)
    tags_list = serializers.ListField(source='get_tags_list', read_only=True)
    
    class Meta:
        model = StudentComment
        fields = '__all__'
    
    def create(self, validated_data):
        # タグをリストから文字列に変換
        if 'tags' in self.initial_data and isinstance(self.initial_data['tags'], list):
            validated_data['tags'] = ', '.join(self.initial_data['tags'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # タグをリストから文字列に変換
        if 'tags' in self.initial_data and isinstance(self.initial_data['tags'], list):
            validated_data['tags'] = ', '.join(self.initial_data['tags'])
        return super().update(instance, validated_data)


class TestCommentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    test_name = serializers.CharField(source='test.name', read_only=True)
    question_group_title = serializers.CharField(source='question_group.title', read_only=True, allow_null=True)
    question_content = serializers.CharField(source='question.content', read_only=True, allow_null=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    
    class Meta:
        model = TestComment
        fields = '__all__'


class CommentTemplateV2Serializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    applicable_scope_display = serializers.CharField(source='get_applicable_scope_display', read_only=True)
    
    class Meta:
        model = CommentTemplateV2
        fields = '__all__'


class PastDataImportSerializer(serializers.ModelSerializer):
    import_type_display = serializers.CharField(source='get_import_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    school_name = serializers.CharField(source='target_school.name', read_only=True, allow_null=True)
    progress_percentage = serializers.FloatField(read_only=True)
    
    class Meta:
        model = PastDataImport
        fields = '__all__'


class IndividualProblemSerializer(serializers.ModelSerializer):
    test_name = serializers.CharField(source='test.name', read_only=True)
    
    class Meta:
        model = IndividualProblem
        fields = '__all__'


class IndividualProblemScoreSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    test_name = serializers.CharField(source='test.name', read_only=True)
    problem_number = serializers.IntegerField(source='problem.problem_number', read_only=True)
    problem_max_score = serializers.IntegerField(source='problem.max_score', read_only=True)
    
    class Meta:
        model = IndividualProblemScore
        fields = '__all__'
    
    def validate_score(self, value):
        """スコアのバリデーション"""
        if value < 0:
            raise serializers.ValidationError("得点は0以上である必要があります。")
        return value
    
    def validate(self, data):
        """問題に対する得点の上限チェック"""
        if 'problem' in data and 'score' in data:
            problem = data['problem']
            score = data['score']
            if score > problem.max_score:
                raise serializers.ValidationError(
                    f"問題{problem.problem_number}の得点が満点（{problem.max_score}点）を超えています。"
                )
        return data