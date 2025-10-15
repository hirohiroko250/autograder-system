from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from .models import School
from .serializers import SchoolSerializer
from classrooms.models import Classroom
from .utils import (
    import_schools_from_excel, import_students_from_excel,
    export_school_template, export_student_template
)
import tempfile
import os
import pandas as pd

User = get_user_model()

class SchoolViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    
    def update(self, request, *args, **kwargs):
        """学校情報の更新（権限更新のデバッグ用ログ追加）"""
        print(f"School update request received:")
        print(f"  User: {request.user.username} (role: {request.user.role})")
        print(f"  School ID: {kwargs.get('pk')}")
        print(f"  Data: {request.data}")
        
        instance = self.get_object()
        print(f"  Target school: {instance.name} ({instance.school_id})")
        print(f"  Before update - permissions: register={instance.can_register_students}, input={instance.can_input_scores}, view={instance.can_view_reports}")
        
        response = super().update(request, *args, **kwargs)
        
        # 更新後の状態を確認
        instance.refresh_from_db()
        print(f"  After update - permissions: register={instance.can_register_students}, input={instance.can_input_scores}, view={instance.can_view_reports}")
        
        return response
    
    def partial_update(self, request, *args, **kwargs):
        """学校情報の部分更新（PATCH用）"""
        print(f"School partial_update request received:")
        print(f"  User: {request.user.username} (role: {request.user.role})")  
        print(f"  School ID: {kwargs.get('pk')}")
        print(f"  Data: {request.data}")
        
        instance = self.get_object()
        print(f"  Target school: {instance.name} ({instance.school_id})")
        print(f"  Before update - permissions: register={instance.can_register_students}, input={instance.can_input_scores}, view={instance.can_view_reports}")
        
        response = super().partial_update(request, *args, **kwargs)
        
        # 更新後の状態を確認
        instance.refresh_from_db()
        print(f"  After update - permissions: register={instance.can_register_students}, input={instance.can_input_scores}, view={instance.can_view_reports}")
        
        return response
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'school_admin':
            # 退会した塾はアクセス不可
            school = School.objects.filter(school_id=user.school_id).first()
            if school and not school.can_access():
                return School.objects.none()
            return School.objects.filter(school_id=user.school_id)
        elif user.role == 'classroom_admin':
            # 教室管理者は所属塾のみ閲覧可能（退会チェック含む）
            school = School.objects.filter(classrooms__classroom_id=user.classroom_id).first()
            if school and not school.can_access():
                return School.objects.none()
            return School.objects.filter(classrooms__classroom_id=user.classroom_id)
        else:
            # 管理者は全て閲覧可能
            return School.objects.all()
    
    @action(detail=True, methods=['post'])
    def create_classroom(self, request, pk=None):
        school = self.get_object()
        classroom_data = request.data.copy()
        
        # 次の教室IDを生成
        last_classroom = Classroom.objects.filter(
            school=school
        ).order_by('-classroom_id').first()
        
        if last_classroom:
            next_id = str(int(last_classroom.classroom_id) + 1).zfill(6)
        else:
            # 学校IDベースで教室IDを生成
            next_id = str(int(school.school_id) * 1000 + 1).zfill(6)
        
        classroom_data['classroom_id'] = next_id
        
        from classrooms.serializers import ClassroomSerializer
        serializer = ClassroomSerializer(data=classroom_data)
        if serializer.is_valid():
            classroom = serializer.save(school=school)
            
            # 教室管理者アカウント作成
            user = User.objects.create_user(
                username=classroom.classroom_id,
                password=classroom.classroom_id,
                role='classroom_admin',
                school_id=school.school_id,
                classroom_id=classroom.classroom_id
            )
            
            return Response({
                'classroom': serializer.data,
                'credentials': {
                    'classroom_id': classroom.classroom_id,
                    'password': classroom.classroom_id
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def import_excel(self, request):
        """Excelファイルから塾を一括インポート"""
        if 'file' not in request.FILES:
            return Response({'error': 'ファイルが必要です。'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            for chunk in file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            result = import_schools_from_excel(tmp_file_path)
            return Response(result)
        finally:
            # 一時ファイルを削除
            os.unlink(tmp_file_path)
    
    @action(detail=False, methods=['get'])
    def export_template(self, request):
        """塾登録用Excelテンプレートをダウンロード"""
        df = export_school_template()
        
        # Excelファイルを生成
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            df.to_excel(tmp_file.name, index=False)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="school_template.xlsx"'
                return response
        finally:
            os.unlink(tmp_file_path)
    
    @action(detail=False, methods=['get'])
    def export_data(self, request):
        """塾データをExcelファイルでエクスポート"""
        schools = self.get_queryset()
        
        # データをDataFrameに変換
        data = []
        for school in schools:
            data.append({
                '塾ID': school.school_id,
                '塾名': school.name,
                'メールアドレス': school.email,
                '電話番号': school.phone,
                '住所': school.address,
                'アクティブ': '有効' if school.is_active else '無効',
                '作成日': school.created_at.strftime('%Y-%m-%d'),
            })
        
        df = pd.DataFrame(data)
        
        # Excelファイルを生成
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            df.to_excel(tmp_file.name, index=False)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="schools_data.xlsx"'
                return response
        finally:
            os.unlink(tmp_file_path)

@staff_member_required  
def school_import_view(request):
    """塾データインポート専用ビュー"""
    from django.shortcuts import render, redirect
    from django.contrib import messages
    from .admin_actions import SchoolImportForm
    
    if request.method == 'POST' and 'excel_file' in request.FILES:
        form = SchoolImportForm(request)
        if form.process_import(request.FILES['excel_file']):
            return redirect('/admin/schools/school/')
    
    return render(request, 'admin/school_import.html', {
        'title': '塾データ一括インポート',
        'opts': School._meta,
    })