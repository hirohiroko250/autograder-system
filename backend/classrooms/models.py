from django.db import models
from django.core.validators import RegexValidator
from schools.models import School


class MembershipType(models.Model):
    """会員種別・料金設定"""
    TYPE_CHOICES = [
        ('culture_kids', 'カルチャーキッズ導入塾'),
        ('general', '一般塾'),
        ('eduplus', 'eduplus導入塾'),
    ]
    
    type_code = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        unique=True,
        verbose_name='塾区分コード'
    )
    name = models.CharField(max_length=100, verbose_name='塾区分名')
    description = models.TextField(blank=True, verbose_name='説明')
    price_per_student = models.IntegerField(verbose_name='1名あたり料金（円）')
    is_active = models.BooleanField(default=True, verbose_name='アクティブ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'membership_types'
        verbose_name = '会員種別'
        verbose_name_plural = '会員種別'
        indexes = [
            models.Index(fields=['type_code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.price_per_student}円"

class Classroom(models.Model):
    
    classroom_id = models.CharField(
        max_length=6, 
        unique=True,
        validators=[RegexValidator(r'^\d{6}$', '6桁の数字で入力してください')],
        verbose_name='教室ID'
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classrooms', verbose_name='塾')
    name = models.CharField(max_length=100, verbose_name='教室名')
    is_active = models.BooleanField(default=True, verbose_name='アクティブ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'classrooms'
        verbose_name = '教室'
        verbose_name_plural = '教室'
        indexes = [
            models.Index(fields=['school', 'classroom_id']),
            models.Index(fields=['is_active']),
        ]
    
    def save(self, *args, **kwargs):
        """新規作成時に教室管理者ユーザーアカウントと権限設定を自動作成"""
        is_new = self.pk is None
        if is_new:
            super().save(*args, **kwargs)
            self._create_classroom_admin_user()
            self._create_default_permissions()
        else:
            super().save(*args, **kwargs)
    
    def _create_classroom_admin_user(self):
        """教室管理者ユーザーアカウントを自動作成"""
        from accounts.models import User
        
        # ユーザー名は塾ID + 教室ID
        username = f"{self.school.school_id}{self.classroom_id}"
        
        # 既存のユーザーがいないか確認
        if not User.objects.filter(username=username).exists():
            user = User.objects.create(
                username=username,
                email=self.school.email,  # 塾のメールアドレスを使用
                role='classroom_admin',
                school_id=self.school.school_id,
                classroom_id=self.classroom_id,
                is_active=True
            )
            # パスワードを教室IDに設定
            user.set_password(self.classroom_id)
            user.save()
            print(f"教室管理者ユーザーを作成しました: {username} (password: {self.classroom_id})")
    
    def _create_default_permissions(self):
        """デフォルトの権限設定を作成"""
        ClassroomPermission.objects.get_or_create(
            classroom=self,
            defaults={
                'can_register_students': True,
                'can_input_scores': True,
                'can_view_reports': True,
            }
        )
        print(f"教室権限設定を作成しました: {self.name}")
    
    def get_price_per_student(self):
        """会員種別に応じた1名あたり料金を取得（塾から取得）"""
        return self.school.get_price_per_student()
    
    def calculate_total_fee(self, student_count):
        """受講者数から合計料金を計算"""
        return self.get_price_per_student() * student_count
    
    def get_membership_display_with_price(self):
        """会員種別と料金を表示（塾から取得）"""
        return self.school.get_membership_display_with_price()
    
    def __str__(self):
        return f"{self.classroom_id} - {self.name}"


class ClassroomPermission(models.Model):
    """教室の機能権限設定"""
    classroom = models.OneToOneField(
        Classroom, 
        on_delete=models.CASCADE, 
        related_name='permissions',
        verbose_name='教室'
    )
    can_register_students = models.BooleanField(default=True, verbose_name='生徒登録権限')
    can_input_scores = models.BooleanField(default=True, verbose_name='点数入力権限')
    can_view_reports = models.BooleanField(default=True, verbose_name='結果出力権限')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'classroom_permissions'
        verbose_name = '教室権限設定'
        verbose_name_plural = '教室権限設定'
    
    def __str__(self):
        return f"{self.classroom.name} - 権限設定"


class AttendanceRecord(models.Model):
    """受講記録（課金計算用）"""
    PERIOD_CHOICES = [
        ('spring', '春期'),
        ('summer', '夏期'),
        ('winter', '冬期'),
    ]
    
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name='教室')
    student_id = models.CharField(max_length=10, verbose_name='生徒ID')
    student_name = models.CharField(max_length=100, verbose_name='生徒名')
    year = models.IntegerField(verbose_name='年度')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, verbose_name='期')
    subject = models.CharField(max_length=50, verbose_name='教科')
    has_score_input = models.BooleanField(default=False, verbose_name='点数入力済み')
    score_input_date = models.DateTimeField(null=True, blank=True, verbose_name='点数入力日時')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'attendance_records'
        verbose_name = '受講記録'
        verbose_name_plural = '受講記録'
        unique_together = ['classroom', 'student_id', 'year', 'period', 'subject']
        indexes = [
            models.Index(fields=['classroom', 'year', 'period']),
            models.Index(fields=['has_score_input']),
            models.Index(fields=['score_input_date']),
        ]
    
    def get_billing_amount(self):
        """この受講記録の課金額を計算"""
        if self.has_score_input:
            return self.classroom.school.get_price_per_student()
        return 0
    
    def __str__(self):
        return f"{self.classroom.name} - {self.student_name} ({self.year}年度 {self.get_period_display()})"


class BillingReport(models.Model):
    """課金レポート（集計用）"""
    PERIOD_CHOICES = [
        ('spring', '春期'),
        ('summer', '夏期'),
        ('winter', '冬期'),
    ]
    
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name='教室')
    year = models.IntegerField(verbose_name='年度')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, verbose_name='期')
    
    # 集計情報
    total_students = models.IntegerField(default=0, verbose_name='総生徒数')
    billed_students = models.IntegerField(default=0, verbose_name='課金対象生徒数')
    price_per_student = models.IntegerField(verbose_name='単価（円）')
    total_amount = models.IntegerField(default=0, verbose_name='合計金額（円）')
    
    # 詳細情報（JSON）
    student_details = models.JSONField(default=dict, verbose_name='生徒詳細')
    
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='生成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'billing_reports'
        verbose_name = '課金レポート'
        verbose_name_plural = '課金レポート'
        unique_together = ['classroom', 'year', 'period']
        indexes = [
            models.Index(fields=['year', 'period']),
            models.Index(fields=['generated_at']),
        ]
    
    def __str__(self):
        return f"{self.classroom.name} - {self.year}年度 {self.get_period_display()} - {self.total_amount}円"