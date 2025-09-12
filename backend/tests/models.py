from django.db import models

class TestSchedule(models.Model):
    PERIODS = [
        ('spring', '春期'),
        ('summer', '夏期'),
        ('winter', '冬期'),
    ]
    
    year = models.IntegerField(verbose_name='年度')
    period = models.CharField(max_length=10, choices=PERIODS, verbose_name='時期')
    planned_date = models.DateField(verbose_name='予定日')
    actual_date = models.DateField(null=True, blank=True, verbose_name='実施日')
    deadline_at = models.DateTimeField(verbose_name='締切日時')
    is_active = models.BooleanField(default=True, verbose_name='アクティブ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_schedules'
        verbose_name = 'テストスケジュール'
        verbose_name_plural = 'テストスケジュール'
        unique_together = ['year', 'period']
        indexes = [
            models.Index(fields=['year', 'period']),
            models.Index(fields=['deadline_at']),
        ]
    
    def is_active_now(self):
        """現在がテスト期間内かどうかを判定"""
        from django.utils import timezone
        now = timezone.now()
        
        # actual_dateがある場合はそれを使用、なければplanned_dateを使用
        test_date = self.actual_date or self.planned_date
        
        # テスト日付が今日以降で、締切時刻より前かどうか
        return test_date <= now.date() and now <= self.deadline_at
    
    def get_period_status(self):
        """テスト期間の状態を取得"""
        from django.utils import timezone
        now = timezone.now()
        
        test_date = self.actual_date or self.planned_date
        
        if now.date() < test_date:
            return 'not_started'  # 開始前
        elif now > self.deadline_at:
            return 'ended'  # 終了
        else:
            return 'active'  # 実施中
    
    def __str__(self):
        return f"{self.year}年 {self.get_period_display()}"

class TestDefinition(models.Model):
    ELEMENTARY_SUBJECTS = [
        ('japanese', '国語'),
        ('math', '算数'),
    ]
    
    MIDDLE_SCHOOL_SUBJECTS = [
        ('english', '英語'),
        ('mathematics', '数学'),
    ]
    
    # Combined subjects for choice field
    SUBJECTS = ELEMENTARY_SUBJECTS + MIDDLE_SCHOOL_SUBJECTS
    
    # 教科コードマッピング
    SUBJECT_CODES = {
        'math': 1,      # 算数
        'japanese': 2,  # 国語
        'english': 3,   # 英語
        'mathematics': 4,  # 数学
    }
    
    # 逆マッピング（コードから教科名）
    CODE_TO_SUBJECT = {v: k for k, v in SUBJECT_CODES.items()}
    
    GRADE_LEVELS = [
        ('elementary_1', '小1'),
        ('elementary_2', '小2'),
        ('elementary_3', '小3'),
        ('elementary_4', '小4'),
        ('elementary_5', '小5'),
        ('elementary_6', '小6'),
        ('middle_1', '中1'),
        ('middle_2', '中2'),
        ('middle_3', '中3'),
    ]
    
    schedule = models.ForeignKey(TestSchedule, on_delete=models.CASCADE, related_name='tests', verbose_name='テストスケジュール')
    grade_level = models.CharField(max_length=20, choices=GRADE_LEVELS, default='elementary_1', verbose_name='対象学年')
    subject = models.CharField(max_length=20, choices=SUBJECTS, verbose_name='科目')
    max_score = models.IntegerField(default=100, verbose_name='満点')
    question_pdf = models.FileField(upload_to='test_questions/', null=True, blank=True, verbose_name='問題PDF')
    answer_pdf = models.FileField(upload_to='test_answers/', null=True, blank=True, verbose_name='解答PDF')
    is_active = models.BooleanField(default=True, verbose_name='アクティブ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_definitions'
        verbose_name = 'テスト'
        verbose_name_plural = 'テスト'
        unique_together = ['schedule', 'grade_level', 'subject']
        indexes = [
            models.Index(fields=['schedule', 'grade_level', 'subject']),
        ]
    
    def clean(self):
        """Validate grade level and subject combination"""
        from django.core.exceptions import ValidationError
        
        if self.grade_level and self.subject:
            # 小学生の学年チェック
            if self.grade_level.startswith('elementary_'):
                valid_subjects = [s[0] for s in self.ELEMENTARY_SUBJECTS]
                if self.subject not in valid_subjects:
                    raise ValidationError({
                        'subject': f'小学生では{self.get_subject_display()}は選択できません。国語または算数を選択してください。'
                    })
            # 中学生の学年チェック
            elif self.grade_level.startswith('middle_'):
                valid_subjects = [s[0] for s in self.MIDDLE_SCHOOL_SUBJECTS]
                if self.subject not in valid_subjects:
                    raise ValidationError({
                        'subject': f'中学生では{self.get_subject_display()}は選択できません。英語または数学を選択してください。'
                    })
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_subjects_for_grade(cls, grade_level):
        """Get available subjects for a specific grade level"""
        if grade_level.startswith('elementary_'):
            return cls.ELEMENTARY_SUBJECTS
        elif grade_level.startswith('middle_'):
            return cls.MIDDLE_SCHOOL_SUBJECTS
        return cls.SUBJECTS
    
    def is_input_allowed(self):
        """現在、得点入力が許可されているかどうか"""
        return self.is_active and self.schedule.is_active_now()
    
    def get_input_status(self):
        """入力状況の詳細を取得"""
        if not self.is_active:
            return {
                'allowed': False,
                'reason': 'テストが無効化されています',
                'status': 'inactive'
            }
        
        period_status = self.schedule.get_period_status()
        
        if period_status == 'not_started':
            return {
                'allowed': False,
                'reason': 'テスト期間開始前です',
                'status': 'not_started',
                'start_date': self.schedule.actual_date or self.schedule.planned_date,
                'deadline': self.schedule.deadline_at
            }
        elif period_status == 'ended':
            return {
                'allowed': False,
                'reason': 'テスト期間が終了しています',
                'status': 'ended',
                'deadline': self.schedule.deadline_at
            }
        else:
            return {
                'allowed': True,
                'reason': '入力可能',
                'status': 'active',
                'deadline': self.schedule.deadline_at
            }
    
    def get_subject_code(self):
        """教科コードを取得"""
        return self.SUBJECT_CODES.get(self.subject, 0)
    
    @classmethod
    def get_subject_by_code(cls, code):
        """教科コードから教科名を取得"""
        return cls.CODE_TO_SUBJECT.get(code, None)
    
    def __str__(self):
        return f"{self.schedule} - {self.get_grade_level_display()} {self.get_subject_display()}"

class QuestionGroup(models.Model):
    test = models.ForeignKey(TestDefinition, on_delete=models.CASCADE, related_name='question_groups', verbose_name='テスト')
    group_number = models.IntegerField(verbose_name='大問番号')
    title = models.CharField(max_length=100, verbose_name='タイトル')
    max_score = models.IntegerField(verbose_name='満点')
    
    class Meta:
        db_table = 'question_groups'
        verbose_name = '大問'
        verbose_name_plural = '大問'
        unique_together = ['test', 'group_number']
        ordering = ['group_number']
    
    def __str__(self):
        return f"{self.test} - 大問{self.group_number}"

class Question(models.Model):
    group = models.ForeignKey(QuestionGroup, on_delete=models.CASCADE, related_name='questions', verbose_name='大問')
    question_number = models.IntegerField(verbose_name='問題番号')
    content = models.TextField(verbose_name='問題内容')
    max_score = models.IntegerField(verbose_name='満点')
    
    class Meta:
        db_table = 'questions'
        verbose_name = '問題'
        verbose_name_plural = '問題'
        unique_together = ['group', 'question_number']
        ordering = ['question_number']
    
    def __str__(self):
        return f"{self.group} - 問{self.question_number}"

class AnswerKey(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='answer_key', verbose_name='問題')
    correct_answer = models.TextField(verbose_name='正解')
    explanation = models.TextField(blank=True, verbose_name='解説')
    
    class Meta:
        db_table = 'answer_keys'
        verbose_name = '解答'
        verbose_name_plural = '解答'
    
    def __str__(self):
        return f"{self.question} - 解答"