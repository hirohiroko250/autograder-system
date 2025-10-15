from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from tests.models import TestSchedule
from .serializers import TestScheduleInfoSerializer

class TestScheduleInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    TestSchedule モデルを使用する ViewSet
    フロントエンド互換性のため、エンドポイント名とレスポンス形式は維持
    """
    serializer_class = TestScheduleInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TestSchedule.objects.all().order_by('-year', 'period')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'count': queryset.count()
        })