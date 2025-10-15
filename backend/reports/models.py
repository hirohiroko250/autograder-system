from django.db import models
from schools.models import School

class BillingRecord(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='billing_records')
    year = models.IntegerField()
    month = models.IntegerField()
    student_count = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_records'
        unique_together = ['school', 'year', 'month']
        indexes = [
            models.Index(fields=['school', 'year', 'month']),
            models.Index(fields=['is_paid']),
        ]
    
    def __str__(self):
        return f"{self.school} - {self.year}年{self.month}月 - {self.amount}円"