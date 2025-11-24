from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import TestScheduleInfo
from .serializers import TestScheduleInfoSerializer

class TestScheduleInfoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TestScheduleInfoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TestScheduleInfo.objects.all().order_by('-year', 'period')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'count': queryset.count()
        })