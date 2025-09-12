from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class User(AbstractUser):
    USER_ROLES = [
        ('school_admin', '塾管理者'),
        ('classroom_admin', '教室管理者'),
    ]
    
    role = models.CharField(max_length=20, choices=USER_ROLES, verbose_name='役割')
    school_id = models.CharField(
        max_length=6, 
        null=True, 
        blank=True,
        validators=[RegexValidator(r'^\d{6}$', '6桁の数字で入力してください')],
        verbose_name='塾ID'
    )
    classroom_id = models.CharField(
        max_length=6, 
        null=True, 
        blank=True,
        validators=[RegexValidator(r'^\d{6}$', '6桁の数字で入力してください')],
        verbose_name='教室ID'
    )
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'role']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'
        indexes = [
            models.Index(fields=['school_id']),
            models.Index(fields=['classroom_id']),
            models.Index(fields=['role']),
        ]
    
    def save(self, *args, **kwargs):
        # スーパーユーザーの場合はusernameを変更しない
        if not self.is_superuser:
            if self.role == 'school_admin' and self.school_id:
                self.username = self.school_id
            elif self.role == 'classroom_admin' and self.classroom_id and self.school_id:
                # 教室管理者のusernameは塾ID + 教室ID
                self.username = f'{self.school_id}{self.classroom_id}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"