from rest_framework import serializers
from tests.models import TestSchedule

class TestScheduleInfoSerializer(serializers.ModelSerializer):
    """
    TestSchedule モデルを使用するシリアライザー
    フロントエンド互換性のため、フィールド名を TestScheduleInfo に合わせる
    """
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    # TestSchedule は status フィールドがないため、is_active から status を生成
    status = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    # TestSchedule の deadline_at を deadline にマッピング
    deadline = serializers.DateTimeField(source='deadline_at')

    class Meta:
        model = TestSchedule
        fields = [
            'id', 'year', 'period', 'period_display', 'planned_date',
            'actual_date', 'deadline', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_status(self, obj):
        """is_active と期間状態から status を生成"""
        if not obj.is_active:
            return 'completed'

        period_status = obj.get_period_status()
        if period_status == 'not_started':
            return 'scheduled'
        elif period_status == 'active':
            return 'in_progress'
        else:  # ended
            return 'completed'

    def get_status_display(self, obj):
        """status の日本語表示"""
        status = self.get_status(obj)
        status_map = {
            'scheduled': '予定',
            'in_progress': '実施中',
            'completed': '完了'
        }
        return status_map.get(status, status)