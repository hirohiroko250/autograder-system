from django.db import models
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from students.models import Student
from tests.models import TestDefinition, Question, QuestionGroup
from schools.models import School

class Score(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='scores')
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='scores')
    question_group = models.ForeignKey(QuestionGroup, on_delete=models.CASCADE, related_name='scores', null=True, blank=True)
    score = models.IntegerField(verbose_name='得点')
    attendance = models.BooleanField(default=True, verbose_name='出席')  # 出席=True、欠席=False
    comment = models.TextField(blank=True, verbose_name='コメント')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scores'
        verbose_name = '得点'
        verbose_name_plural = '得点'
        unique_together = ['student', 'test', 'question_group']
        indexes = [
            models.Index(fields=['student', 'test']),
            models.Index(fields=['created_at']),
        ]
    
    def clean(self):
        """バリデーション: 満点以上の点数は無効"""
        from django.core.exceptions import ValidationError
        if self.score < 0:
            raise ValidationError('得点は0以上である必要があります。')
        if self.question_group and self.score > self.question_group.max_score:
            raise ValidationError(f'得点は満点（{self.question_group.max_score}点）以下である必要があります。')
    
    def save(self, *args, **kwargs):
        """保存時にバリデーションを実行"""
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student} - {self.test} - 大問{self.question_group.group_number} - {self.score}点"
    
    @classmethod
    def validate_student_scores(cls, student, test, scores_data):
        """
        生徒の得点データをバリデーションする
        
        Args:
            student: 生徒オブジェクト
            test: テストオブジェクト
            scores_data: {question_group_id: {'score': int, 'attendance': bool}, ...}
        
        Returns:
            {
                'valid': bool,
                'warnings': [str],
                'errors': [str]
            }
        """
        warnings = []
        errors = []
        
        # 出席情報を取得（最初の大問の出席情報を基準とする）
        first_score_data = list(scores_data.values())[0] if scores_data else {}
        attendance = first_score_data.get('attendance', True)
        
        # 合計点を計算
        total_score = sum(data.get('score', 0) for data in scores_data.values())
        
        # パターン1: 合計点が100点を超える場合
        if total_score > 100:
            warnings.append(f"合計点が100点を超えています: {total_score}点")
        
        # パターン2: 出席しているのに得点が未入力の場合
        if attendance:
            for group_id, data in scores_data.items():
                if data.get('score') is None or data.get('score') == '':
                    warnings.append(f"出席しているのに得点が未入力です（大問{group_id}）")
        
        return {
            'valid': len(errors) == 0,
            'warnings': warnings,
            'errors': errors
        }

class TestResult(models.Model):
    """テスト結果の集計テーブル"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_results')
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='test_results')
    total_score = models.IntegerField()
    correct_rate = models.DecimalField(max_digits=5, decimal_places=2)  # 正答率（%）
    
    # 一時的順位（締切前）
    school_rank_temporary = models.IntegerField(null=True, blank=True, verbose_name='塾内順位（一時）')
    national_rank_temporary = models.IntegerField(null=True, blank=True, verbose_name='全国順位（一時）')
    school_total_temporary = models.IntegerField(default=0, verbose_name='塾内受験者数（一時）')
    national_total_temporary = models.IntegerField(default=0, verbose_name='全国受験者数（一時）')
    
    # 確定後順位（締切後）
    school_rank_final = models.IntegerField(null=True, blank=True, verbose_name='塾内順位（確定）')
    national_rank_final = models.IntegerField(null=True, blank=True, verbose_name='全国順位（確定）')
    school_total_final = models.IntegerField(default=0, verbose_name='塾内受験者数（確定）')
    national_total_final = models.IntegerField(default=0, verbose_name='全国受験者数（確定）')
    
    # 後方互換性のための従来フィールド（一時的順位を参照）
    school_rank = models.IntegerField(null=True, blank=True)  # 塾内順位（後方互換）
    national_rank = models.IntegerField(null=True, blank=True)  # 全国順位（後方互換）
    school_total_students = models.IntegerField(default=0)  # 塾内受験者数（後方互換）
    national_total_students = models.IntegerField(default=0)  # 全国受験者数（後方互換）
    
    # 新しい順位システム（学年別・段階別）
    grade_rank = models.IntegerField(null=True, blank=True, verbose_name='学年内順位')
    grade_total = models.IntegerField(default=0, verbose_name='学年内受験者数')
    
    # 小学生全体/中学生全体の順位
    school_category_rank = models.IntegerField(null=True, blank=True, verbose_name='小中区分内順位')
    school_category_total = models.IntegerField(default=0, verbose_name='小中区分内受験者数')
    
    # 全国順位（全学年・全テスト）
    national_rank = models.IntegerField(null=True, blank=True, verbose_name='全国順位')
    national_total = models.IntegerField(default=0, verbose_name='全国受験者数')
    
    # 偏差値（学年別）
    grade_deviation_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='学年内偏差値')
    
    # 確定フラグ
    is_rank_finalized = models.BooleanField(default=True, verbose_name='順位確定済み')  # デフォルトを確定に変更
    rank_finalized_at = models.DateTimeField(null=True, blank=True, verbose_name='順位確定日時')
    
    comment = models.TextField(blank=True)  # 自動生成コメント
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_results'
        verbose_name = 'テスト結果'
        verbose_name_plural = 'テスト結果'
        unique_together = ['student', 'test']
        indexes = [
            models.Index(fields=['test', 'total_score']),
            models.Index(fields=['student']),
        ]
    
    def save(self, *args, **kwargs):
        """保存時に後方互換性フィールドを更新"""
        # 一時的順位を後方互換フィールドにコピー
        self.school_rank = self.school_rank_temporary
        self.national_rank = self.national_rank_temporary
        self.school_total_students = self.school_total_temporary
        self.national_total_students = self.national_total_temporary
        
        super().save(*args, **kwargs)
    
    def get_current_school_rank_display(self):
        """現在有効な塾内順位を表示用で取得"""
        if self.is_rank_finalized and self.school_rank_final:
            return f"{self.school_rank_final}/{self.school_total_final}"
        elif self.school_rank_temporary:
            return f"{self.school_rank_temporary}/{self.school_total_temporary}"
        return "未算出"
    
    def get_current_national_rank_display(self):
        """現在有効な全国順位を表示用で取得"""
        if self.is_rank_finalized and self.national_rank_final:
            return f"{self.national_rank_final}/{self.national_total_final}"
        elif self.national_rank_temporary:
            return f"{self.national_rank_temporary}/{self.national_total_temporary}"
        return "未算出"
    
    def get_current_school_rank(self):
        """現在有効な塾内順位を取得"""
        if self.is_rank_finalized and self.school_rank_final:
            return self.school_rank_final, self.school_total_final
        return self.school_rank_temporary, self.school_total_temporary
    
    def get_current_national_rank(self):
        """現在有効な全国順位を取得"""
        if self.is_rank_finalized and self.national_rank_final:
            return self.national_rank_final, self.national_total_final
        return self.national_rank_temporary, self.national_total_temporary
    
    def finalize_ranks(self):
        """順位を確定させる"""
        from django.utils import timezone
        
        self.school_rank_final = self.school_rank_temporary
        self.national_rank_final = self.national_rank_temporary
        self.school_total_final = self.school_total_temporary
        self.national_total_final = self.national_total_temporary
        self.is_rank_finalized = True
        self.rank_finalized_at = timezone.now()
        self.save()
    
    def is_test_deadline_passed(self):
        """テストの締切が過ぎているかチェック"""
        from django.utils import timezone
        return timezone.now() > self.test.schedule.deadline_at
    
    def __str__(self):
        return f"{self.student} - {self.test} - {self.total_score}点"

class CommentTemplate(models.Model):
    SUBJECTS = [
        ('japanese', '国語'),
        ('math', '算数'),
    ]
    
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='comment_templates', null=True, blank=True)  # Nullの場合はデフォルトテンプレート
    subject = models.CharField(max_length=20, choices=SUBJECTS)
    score_range_min = models.IntegerField()
    score_range_max = models.IntegerField()
    template_text = models.TextField()
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)  # デフォルトテンプレートかどうか
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comment_templates'
        verbose_name = 'コメントテンプレート'
        verbose_name_plural = 'コメントテンプレート'
        indexes = [
            models.Index(fields=['school', 'subject']),
            models.Index(fields=['is_default', 'subject']),
        ]
    
    def __str__(self):
        if self.school:
            return f"{self.school} - {self.get_subject_display()} - {self.score_range_min}-{self.score_range_max}点"
        return f"デフォルト - {self.get_subject_display()} - {self.score_range_min}-{self.score_range_max}点"

class SchoolStatistics(models.Model):
    """塾ごとの統計情報"""
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='statistics')
    total_students = models.IntegerField(default=0)
    active_students = models.IntegerField(default=0)
    total_classrooms = models.IntegerField(default=0)
    active_classrooms = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'school_statistics'
        verbose_name = '塾統計'
        verbose_name_plural = '塾統計'
    
    def __str__(self):
        return f"{self.school.name} - 生徒数: {self.active_students}名"

class TestSummary(models.Model):
    """テスト集計結果を保存するモデル"""
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='summaries')
    year = models.IntegerField(verbose_name='年度')
    period = models.CharField(max_length=10, verbose_name='時期')
    subject = models.CharField(max_length=20, verbose_name='科目')
    
    # 全体統計
    total_students = models.IntegerField(default=0, verbose_name='総受験者数')
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='平均点')
    average_correct_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='平均正答率')
    max_score = models.IntegerField(default=100, verbose_name='満点')
    
    # 学年別統計（JSONフィールドで保存）
    grade_statistics = models.JSONField(default=dict, verbose_name='学年別統計')
    
    # 塾別統計（JSONフィールドで保存）  
    school_statistics = models.JSONField(default=dict, verbose_name='塾別統計')
    
    # 集計実行日時
    calculated_at = models.DateTimeField(auto_now_add=True, verbose_name='集計日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'test_summaries'
        verbose_name = 'テスト集計結果'
        verbose_name_plural = 'テスト集計結果'
        unique_together = ['test']
        indexes = [
            models.Index(fields=['year', 'period', 'subject']),
            models.Index(fields=['calculated_at']),
        ]
    
    def __str__(self):
        period_display = {'spring': '春季', 'summer': '夏季', 'winter': '冬季'}.get(self.period, self.period)
        subject_display = {'japanese': '国語', 'math': '算数'}.get(self.subject, self.subject)
        return f"{self.year}年度{period_display} {subject_display} 集計結果"

class SchoolTestSummary(models.Model):
    """塾別テスト集計結果の詳細"""
    test_summary = models.ForeignKey(TestSummary, on_delete=models.CASCADE, related_name='school_details')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='test_summaries')
    
    # 塾の統計
    student_count = models.IntegerField(default=0, verbose_name='受験者数')
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='平均点')
    average_correct_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='平均正答率')
    rank_among_schools = models.IntegerField(null=True, blank=True, verbose_name='塾間順位')
    
    # 学年別詳細（JSONフィールド）
    grade_details = models.JSONField(default=dict, verbose_name='学年別詳細')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'school_test_summaries'
        verbose_name = '塾別テスト集計'
        verbose_name_plural = '塾別テスト集計'
        unique_together = ['test_summary', 'school']
    
    def __str__(self):
        return f"{self.test_summary} - {self.school.name}"


class IndividualProblem(models.Model):
    """個別問題モデル（1-10などのシンプルな問題）"""
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='individual_problems', verbose_name='テスト')
    problem_number = models.IntegerField(verbose_name='問題番号')  # 1, 2, 3, ..., 10
    max_score = models.IntegerField(default=10, verbose_name='満点')
    description = models.CharField(max_length=200, blank=True, verbose_name='説明')
    
    class Meta:
        db_table = 'individual_problems'
        verbose_name = '個別問題'
        verbose_name_plural = '個別問題'
        unique_together = ['test', 'problem_number']
        ordering = ['problem_number']
        indexes = [
            models.Index(fields=['test', 'problem_number']),
        ]
    
    def __str__(self):
        return f"{self.test} - 問題{self.problem_number}"

class IndividualProblemScore(models.Model):
    """個別問題のスコア管理"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='individual_problem_scores')
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='individual_problem_scores')
    problem = models.ForeignKey(IndividualProblem, on_delete=models.CASCADE, related_name='scores')
    score = models.IntegerField(verbose_name='得点')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'individual_problem_scores'
        verbose_name = '個別問題得点'
        verbose_name_plural = '個別問題得点'
        unique_together = ['student', 'test', 'problem']
        indexes = [
            models.Index(fields=['student', 'test']),
            models.Index(fields=['problem']),
            models.Index(fields=['created_at']),
        ]
    
    def clean(self):
        """バリデーション: 満点以上の点数は無効"""
        from django.core.exceptions import ValidationError
        if self.score < 0:
            raise ValidationError('得点は0以上である必要があります。')
        if self.score > self.problem.max_score:
            raise ValidationError(f'得点は満点（{self.problem.max_score}点）以下である必要があります。')
    
    def save(self, *args, **kwargs):
        """保存時にバリデーションを実行"""
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student} - {self.test} - 問題{self.problem.problem_number} - {self.score}点"

class QuestionScore(models.Model):
    """小問レベルでのスコア管理"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='question_scores')
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='question_scores')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='scores')
    score = models.IntegerField(verbose_name='得点')
    is_correct = models.BooleanField(default=False, verbose_name='正答フラグ')
    answer_text = models.TextField(blank=True, verbose_name='答案内容')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'question_scores'
        verbose_name = '小問得点'
        verbose_name_plural = '小問得点'
        unique_together = ['student', 'test', 'question']
        indexes = [
            models.Index(fields=['student', 'test']),
            models.Index(fields=['question']),
            models.Index(fields=['created_at']),
        ]
    
    def clean(self):
        """バリデーション: 満点以上の点数は無効"""
        from django.core.exceptions import ValidationError
        if self.score < 0:
            raise ValidationError('得点は0以上である必要があります。')
        if self.score > self.question.max_score:
            raise ValidationError(f'得点は満点（{self.question.max_score}点）以下である必要があります。')
    
    def save(self, *args, **kwargs):
        """保存時にバリデーションと正答フラグを自動設定"""
        self.clean()
        if self.score == self.question.max_score:
            self.is_correct = True
        else:
            self.is_correct = False
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student} - {self.test} - Q{self.question.question_number} - {self.score}点"


class TestAttendance(models.Model):
    """詳細な出席管理"""
    ATTENDANCE_STATUS_CHOICES = [
        (1, '出席'),
        (0, '欠席'),
        (2, '遅刻'),
        (3, '早退'),
        (4, '途中退席'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_attendances')
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='attendances')
    attendance_status = models.IntegerField(
        choices=ATTENDANCE_STATUS_CHOICES, 
        default=1, 
        verbose_name='出席状態'
    )
    attendance_time = models.DateTimeField(null=True, blank=True, verbose_name='出席時刻')
    leave_time = models.DateTimeField(null=True, blank=True, verbose_name='退席時刻')
    reason = models.TextField(blank=True, verbose_name='理由')
    notes = models.TextField(blank=True, verbose_name='備考')
    
    # 部分受験管理（遅刻・早退時の対象問題制御）
    available_questions = models.ManyToManyField(
        Question, 
        blank=True,
        verbose_name='受験可能問題',
        help_text='遅刻・早退時に受験可能な問題を指定'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_attendances'
        verbose_name = 'テスト出席管理'
        verbose_name_plural = 'テスト出席管理'
        unique_together = ['student', 'test']
        indexes = [
            models.Index(fields=['test', 'attendance_status']),
            models.Index(fields=['attendance_time']),
        ]
    
    def __str__(self):
        return f"{self.student} - {self.test} - {self.get_attendance_status_display()}"
    
    @property
    def is_present(self):
        """出席しているか（出席、遅刻、早退を含む）"""
        return self.attendance_status in [1, 2, 3, 4]
    
    @property
    def can_take_full_test(self):
        """フルテストを受験できるか"""
        return self.attendance_status == 1
    
    def get_available_question_groups(self):
        """受験可能な大問を取得"""
        if self.can_take_full_test:
            return self.test.question_groups.all()
        elif self.available_questions.exists():
            # 指定された小問から大問を特定
            question_groups = QuestionGroup.objects.filter(
                questions__in=self.available_questions.all()
            ).distinct()
            return question_groups
        else:
            return QuestionGroup.objects.none()
    
    def update_score_eligibility(self):
        """出席状況に応じてスコア入力可否を更新"""
        if not self.is_present:
            # 欠席の場合、全スコアを0に設定
            Score.objects.filter(student=self.student, test=self.test).update(
                score=0, attendance=False
            )
            QuestionScore.objects.filter(student=self.student, test=self.test).update(
                score=0, is_correct=False
            )
    
    def save(self, *args, **kwargs):
        """保存時に関連スコアの出席状況を更新"""
        super().save(*args, **kwargs)
        self.update_score_eligibility()


class StudentComment(models.Model):
    """生徒別総合コメント管理"""
    COMMENT_TYPE_CHOICES = [
        ('general', '総合コメント'),
        ('improvement', '改善点'),
        ('strength', '強み'),
        ('homework', '宿題・課題'),
        ('parent_note', '保護者連絡'),
        ('behavioral', '学習態度'),
        ('academic', '学習内容'),
    ]
    
    VISIBILITY_CHOICES = [
        ('teacher_only', '教師のみ'),
        ('parent_visible', '保護者表示可'),
        ('student_visible', '生徒表示可'),
        ('public', '全体公開'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='comments')
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='student_comments', null=True, blank=True)
    comment_type = models.CharField(
        max_length=20,
        choices=COMMENT_TYPE_CHOICES,
        default='general',
        verbose_name='コメント種別'
    )
    title = models.CharField(max_length=200, verbose_name='タイトル')
    content = models.TextField(verbose_name='コメント内容')
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='teacher_only',
        verbose_name='表示権限'
    )
    is_important = models.BooleanField(default=False, verbose_name='重要フラグ')
    follow_up_required = models.BooleanField(default=False, verbose_name='フォローアップ要')
    follow_up_date = models.DateField(null=True, blank=True, verbose_name='フォローアップ予定日')
    tags = models.CharField(max_length=500, blank=True, verbose_name='タグ（カンマ区切り）')
    
    created_by = models.CharField(max_length=100, verbose_name='作成者')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_comments'
        verbose_name = '生徒コメント'
        verbose_name_plural = '生徒コメント'
        indexes = [
            models.Index(fields=['student', 'test']),
            models.Index(fields=['comment_type']),
            models.Index(fields=['visibility']),
            models.Index(fields=['is_important']),
            models.Index(fields=['follow_up_required', 'follow_up_date']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        test_part = f" - {self.test}" if self.test else ""
        return f"{self.student}{test_part} - {self.get_comment_type_display()}: {self.title[:50]}"
    
    def get_tags_list(self):
        """タグをリストとして取得"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def set_tags_from_list(self, tag_list):
        """リストからタグを設定"""
        self.tags = ', '.join(tag_list) if tag_list else ''


class TestComment(models.Model):
    """テスト別コメント管理（問題別・大問別）"""
    COMMENT_SCOPE_CHOICES = [
        ('test_overall', 'テスト全体'),
        ('question_group', '大問別'),
        ('question', '問題別'),
        ('subject_area', '分野別'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_comments')
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='test_comments')
    question_group = models.ForeignKey(QuestionGroup, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    
    scope = models.CharField(
        max_length=20,
        choices=COMMENT_SCOPE_CHOICES,
        default='test_overall',
        verbose_name='コメント範囲'
    )
    content = models.TextField(verbose_name='コメント内容')
    is_positive = models.BooleanField(null=True, blank=True, verbose_name='ポジティブ評価')
    
    # 自動生成フラグ
    is_auto_generated = models.BooleanField(default=False, verbose_name='自動生成')
    auto_generation_rule = models.CharField(max_length=200, blank=True, verbose_name='自動生成ルール')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_comments'
        verbose_name = 'テストコメント'
        verbose_name_plural = 'テストコメント'
        indexes = [
            models.Index(fields=['student', 'test']),
            models.Index(fields=['question_group']),
            models.Index(fields=['question']),
            models.Index(fields=['scope']),
            models.Index(fields=['is_positive']),
            models.Index(fields=['is_auto_generated']),
        ]
    
    def __str__(self):
        scope_detail = ""
        if self.question_group:
            scope_detail = f" - 大問{self.question_group.group_number}"
        elif self.question:
            scope_detail = f" - 問{self.question.question_number}"
        
        return f"{self.student} - {self.test}{scope_detail}: {self.content[:30]}"


class CommentTemplateV2(models.Model):
    """コメントテンプレート管理 (V2)"""
    TEMPLATE_CATEGORY_CHOICES = [
        ('positive', '良い評価'),
        ('needs_improvement', '改善が必要'),
        ('neutral', '中立的'),
        ('encouragement', '励まし'),
        ('specific_skill', '特定スキル'),
        ('homework', '宿題関連'),
        ('behavior', '学習態度'),
    ]
    
    APPLICABLE_SCOPE_CHOICES = [
        ('any', '全般'),
        ('high_score', '高得点時'),
        ('low_score', '低得点時'),
        ('average_score', '平均的得点時'),
        ('improved', '前回より向上'),
        ('declined', '前回より低下'),
        ('specific_subject', '特定科目'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='テンプレート名')
    category = models.CharField(
        max_length=20,
        choices=TEMPLATE_CATEGORY_CHOICES,
        verbose_name='カテゴリ'
    )
    template_text = models.TextField(verbose_name='テンプレート文')
    applicable_scope = models.CharField(
        max_length=20,
        choices=APPLICABLE_SCOPE_CHOICES,
        default='any',
        verbose_name='適用条件'
    )
    subject_filter = models.CharField(max_length=50, blank=True, verbose_name='科目フィルター')
    score_range_min = models.IntegerField(null=True, blank=True, verbose_name='適用得点範囲(最小)')
    score_range_max = models.IntegerField(null=True, blank=True, verbose_name='適用得点範囲(最大)')
    
    # 塾・教室別テンプレート対応
    school = models.ForeignKey(
        'schools.School', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='comment_templates_v2',
        verbose_name='塾（NULLの場合はシステム共有）'
    )
    classroom = models.ForeignKey(
        'classrooms.Classroom',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='comment_templates_v2',
        verbose_name='教室（NULLの場合は塾全体）'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='有効')
    usage_count = models.IntegerField(default=0, verbose_name='使用回数')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comment_templates_v2'
        verbose_name = 'コメントテンプレートV2'
        verbose_name_plural = 'コメントテンプレートV2'
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['applicable_scope']),
            models.Index(fields=['is_active']),
            models.Index(fields=['usage_count']),
            models.Index(fields=['school', 'classroom']),
            models.Index(fields=['school', 'category']),
        ]
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"
    
    def increment_usage(self):
        """使用回数をインクリメント"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

    def is_applicable_for_score(self, score, max_score):
        """得点に対して適用可能かチェック"""
        if self.score_range_min is not None and score < self.score_range_min:
            return False
        if self.score_range_max is not None and score > self.score_range_max:
            return False
        
        score_percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        if self.applicable_scope == 'high_score' and score_percentage < 80:
            return False
        elif self.applicable_scope == 'low_score' and score_percentage > 60:
            return False
        elif self.applicable_scope == 'average_score' and (score_percentage < 60 or score_percentage > 80):
            return False
        
        return True


class PastDataImport(models.Model):
    """過去データ統合管理"""
    IMPORT_TYPE_CHOICES = [
        ('student_data', '生徒データ'),
        ('score_data', 'スコアデータ'),
        ('comment_data', 'コメントデータ'),
        ('attendance_data', '出席データ'),
        ('test_results', 'テスト結果'),
        ('full_migration', '全データ移行'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待機中'),
        ('processing', '処理中'),
        ('completed', '完了'),
        ('failed', '失敗'),
        ('partial', '部分完了'),
    ]
    
    import_type = models.CharField(
        max_length=20,
        choices=IMPORT_TYPE_CHOICES,
        verbose_name='インポート種別'
    )
    source_system = models.CharField(max_length=100, verbose_name='移行元システム')
    file_path = models.CharField(max_length=500, blank=True, verbose_name='ファイルパス')
    
    target_school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='処理状況'
    )
    
    total_records = models.IntegerField(default=0, verbose_name='総レコード数')
    processed_records = models.IntegerField(default=0, verbose_name='処理済みレコード数')
    success_records = models.IntegerField(default=0, verbose_name='成功レコード数')
    error_records = models.IntegerField(default=0, verbose_name='エラーレコード数')
    
    error_log = models.TextField(blank=True, verbose_name='エラーログ')
    processing_log = models.TextField(blank=True, verbose_name='処理ログ')
    
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='開始時刻')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完了時刻')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'past_data_imports'
        verbose_name = '過去データインポート'
        verbose_name_plural = '過去データインポート'
        indexes = [
            models.Index(fields=['import_type']),
            models.Index(fields=['status']),
            models.Index(fields=['target_school']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        return f"{self.get_import_type_display()} - {self.source_system} - {self.get_status_display()}"
    
    @property
    def progress_percentage(self):
        """進捗率を計算"""
        if self.total_records == 0:
            return 0
        return (self.processed_records / self.total_records) * 100
    
    def add_error_log(self, error_message):
        """エラーログを追加"""
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        new_log = f"[{timestamp}] {error_message}\n"
        self.error_log = (self.error_log or '') + new_log
    
    def add_processing_log(self, message):
        """処理ログを追加"""
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        new_log = f"[{timestamp}] {message}\n"
        self.processing_log = (self.processing_log or '') + new_log


class SubjectGeneralComment(models.Model):
    """教科別総評コメント"""
    SUBJECT_CHOICES = [
        ('japanese', '国語'),
        ('math', '算数'),
    ]

    SCORE_RANGE_CHOICES = [
        ('0-20', '0-20点'),
        ('21-40', '21-40点'),
        ('41-60', '41-60点'),
        ('61-80', '61-80点'),
        ('81-100', '81-100点'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='subject_general_comments')
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='subject_general_comments')
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, verbose_name='教科')
    score = models.IntegerField(verbose_name='得点')
    score_range = models.CharField(max_length=10, choices=SCORE_RANGE_CHOICES, verbose_name='点数範囲', blank=True)
    comment_text = models.TextField(verbose_name='総評コメント')
    template_used = models.ForeignKey(
        CommentTemplateV2,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subject_comments',
        verbose_name='使用テンプレート'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subject_general_comments'
        verbose_name = '教科別総評コメント'
        verbose_name_plural = '教科別総評コメント'
        unique_together = ['student', 'test', 'subject']
        indexes = [
            models.Index(fields=['student', 'test']),
            models.Index(fields=['subject']),
            models.Index(fields=['score_range']),
        ]

    def save(self, *args, **kwargs):
        """保存時に点数範囲を自動設定"""
        if self.score is not None:
            if 0 <= self.score <= 20:
                self.score_range = '0-20'
            elif 21 <= self.score <= 40:
                self.score_range = '21-40'
            elif 41 <= self.score <= 60:
                self.score_range = '41-60'
            elif 61 <= self.score <= 80:
                self.score_range = '61-80'
            elif 81 <= self.score <= 100:
                self.score_range = '81-100'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.student_name} - {self.test} - {self.get_subject_display()} ({self.score}点)"

    @classmethod
    def get_or_create_from_score(cls, student, test, subject, score):
        """得点から自動的にコメントを取得または作成"""
        comment, created = cls.objects.get_or_create(
            student=student,
            test=test,
            subject=subject,
            defaults={'score': score, 'comment_text': ''}
        )

        if created or not comment.comment_text:
            # テンプレートから自動選択
            template = cls.get_template_for_score(subject, score)
            if template:
                comment.comment_text = template.template_text
                comment.template_used = template
                comment.save()

        return comment

    @classmethod
    def get_template_for_score(cls, subject, score):
        """点数に応じた適切なテンプレートを取得"""
        from django.db.models import Q

        # 教科と点数範囲に合致するテンプレートを検索
        templates = CommentTemplateV2.objects.filter(
            Q(subject_filter=subject) | Q(subject_filter=''),
            is_active=True
        )

        # 点数範囲でフィルタリング
        applicable_templates = []
        for template in templates:
            if template.score_range_min is not None and score < template.score_range_min:
                continue
            if template.score_range_max is not None and score > template.score_range_max:
                continue
            applicable_templates.append(template)

        # 使用回数が少ないテンプレートを優先
        if applicable_templates:
            return sorted(applicable_templates, key=lambda t: t.usage_count)[0]

        return None