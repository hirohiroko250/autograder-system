from django.db import models
from django.core.validators import RegexValidator

class School(models.Model):
    STATUS_CHOICES = [
        ('trial', '体験'),
        ('active', '本入会'),
        ('withdrawn', '退会'),
    ]
    
    MEMBERSHIP_TYPE_CHOICES = [
        ('culture_kids', 'カルチャーキッズ導入塾'),
        ('general', '一般塾'),
        ('eduplus', 'eduplus導入塾'),
    ]
    
    school_id = models.CharField(
        max_length=6, 
        unique=True, 
        validators=[RegexValidator(r'^\d{6}$', '6桁の数字で入力してください')],
        verbose_name='塾ID'
    )
    name = models.CharField(max_length=100, verbose_name='塾名')
    contact_person = models.CharField(max_length=100, default='管理者', verbose_name='担当者名')
    email = models.EmailField(verbose_name='メールアドレス')
    phone = models.CharField(max_length=20, blank=True, verbose_name='電話番号')
    address = models.TextField(blank=True, verbose_name='住所')
    
    # 会員種別
    membership_type = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_TYPE_CHOICES,
        default='general',
        verbose_name='会員種別'
    )
    
    # ステータス関連
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='trial', 
        verbose_name='ステータス'
    )
    trial_date = models.DateField(null=True, blank=True, verbose_name='体験開始日')
    active_date = models.DateField(null=True, blank=True, verbose_name='本入会日')
    withdrawn_date = models.DateField(null=True, blank=True, verbose_name='退会日')
    
    # 権限設定
    can_register_students = models.BooleanField(default=True, verbose_name='生徒登録権限')
    can_input_scores = models.BooleanField(default=True, verbose_name='点数入力権限')
    can_view_reports = models.BooleanField(default=True, verbose_name='結果出力権限')
    
    is_active = models.BooleanField(default=True, verbose_name='アクティブ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'schools'
        verbose_name = '塾'
        verbose_name_plural = '塾'
        indexes = [
            models.Index(fields=['school_id']),
            models.Index(fields=['is_active']),
        ]
    
    def save(self, *args, **kwargs):
        """ステータス変更時に日付を自動設定"""
        from django.utils import timezone
        
        # 以前のステータスを取得
        if self.pk:
            try:
                old_instance = School.objects.get(pk=self.pk)
                old_status = old_instance.status
            except School.DoesNotExist:
                old_status = None
        else:
            old_status = None
        
        # ステータスが変更された場合、対応する日付を設定
        if old_status != self.status:
            today = timezone.now().date()
            
            if self.status == 'trial' and not self.trial_date:
                self.trial_date = today
            elif self.status == 'active' and not self.active_date:
                self.active_date = today
            elif self.status == 'withdrawn' and not self.withdrawn_date:
                self.withdrawn_date = today
                # 退会時はis_activeをFalseに設定
                self.is_active = False
        
        # 新規作成時またはschool_idが変更された場合、対応するユーザーアカウントを作成
        is_new = self.pk is None
        if is_new:
            super().save(*args, **kwargs)
            self._create_school_admin_user()
        else:
            super().save(*args, **kwargs)
    
    def _create_school_admin_user(self):
        """塾管理者ユーザーアカウントを自動作成"""
        from accounts.models import User
        
        # 既存のユーザーがいないか確認
        if not User.objects.filter(username=self.school_id).exists():
            user = User.objects.create(
                username=self.school_id,
                email=self.email,
                role='school_admin',
                school_id=self.school_id,
                is_active=True
            )
            # パスワードを塾IDに設定
            user.set_password(self.school_id)
            user.save()
            print(f"塾管理者ユーザーを作成しました: {self.school_id}")
    
    def can_access(self):
        """アクセス可能かどうかを判定"""
        return self.status != 'withdrawn' and self.is_active
    
    def get_status_display_with_date(self):
        """ステータスと日付を組み合わせて表示"""
        status_display = self.get_status_display()
        
        if self.status == 'trial' and self.trial_date:
            return f"{status_display} ({self.trial_date})"
        elif self.status == 'active' and self.active_date:
            return f"{status_display} ({self.active_date})"
        elif self.status == 'withdrawn' and self.withdrawn_date:
            return f"{status_display} ({self.withdrawn_date})"
        
        return status_display
    
    def get_price_per_student(self):
        """会員種別に応じた1名あたり料金を取得"""
        price_mapping = {
            'culture_kids': 100,
            'eduplus': 300,
            'general': 500,
        }
        return price_mapping.get(self.membership_type, 500)
    
    def calculate_total_fee(self, student_count):
        """受講者数から合計料金を計算"""
        return self.get_price_per_student() * student_count
    
    def get_membership_display_with_price(self):
        """会員種別と料金を表示"""
        price = self.get_price_per_student()
        return f"{self.get_membership_type_display()} ({price}円/名)"
    
    def __str__(self):
        return f"{self.school_id} - {self.name}"