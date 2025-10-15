from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from .models import TestSchedule, TestDefinition, QuestionGroup, Question, AnswerKey

class ScoreEntryPermission(BasePermission):
    """
    Allow read-only access for score entry functionality.
    Require authentication for write operations.
    """
    def has_permission(self, request, view):
        # Allow read-only access for score entry related endpoints
        if request.method in ['GET'] and view.action in ['list', 'retrieve', 'question_groups', 'test_structure', 'available_tests']:
            return True
        # Require authentication for all other operations
        return request.user and request.user.is_authenticated

from .serializers import (
    TestScheduleSerializer, TestDefinitionSerializer, 
    QuestionGroupSerializer, QuestionSerializer, AnswerKeySerializer
)
import zipfile
import tempfile
import os

class TestScheduleViewSet(viewsets.ModelViewSet):
    queryset = TestSchedule.objects.all()
    serializer_class = TestScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['year', 'period', 'is_active']
    ordering = ['-year', 'period']

class TestDefinitionViewSet(viewsets.ModelViewSet):
    serializer_class = TestDefinitionSerializer
    permission_classes = [ScoreEntryPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['schedule', 'grade_level', 'subject', 'is_active']
    
    def get_queryset(self):
        # 全ての科目を対象とする（学年別フィルタリング）
        return TestDefinition.objects.all()
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """テストの問題一覧を取得"""
        test = self.get_object()
        question_groups = test.question_groups.all().order_by('group_number')
        serializer = QuestionGroupSerializer(question_groups, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def question_groups(self, request, pk=None):
        """フロントエンド用：テストの大問一覧を取得"""
        test = self.get_object()
        question_groups = test.question_groups.all().order_by('group_number')
        
        result = []
        for group in question_groups:
            result.append({
                'id': group.id,
                'group_number': group.group_number,
                'title': group.title,
                'max_score': group.max_score,
                'question_count': group.questions.count()
            })
        
        # 大問が設定されていない場合、デフォルト構造を返す
        if not result:
            # テストの科目と学年に基づいてデフォルト大問を生成
            if test.subject in ['japanese', 'math']:
                default_count = 5
            elif test.subject in ['english', 'mathematics']:
                default_count = 6
            else:
                default_count = 5
            
            for i in range(1, min(default_count + 1, 11)):  # 最大10問
                result.append({
                    'id': None,  # 仮想的な大問
                    'group_number': i,
                    'title': f'大問{i}',
                    'max_score': 20,  # デフォルト満点
                    'question_count': 0
                })
        
        return Response({
            'test_id': test.id,
            'total_max_score': sum(group['max_score'] for group in result),
            'groups': result
        })
    
    @action(detail=True, methods=['get'])
    def test_structure(self, request, pk=None):
        """フロントエンド用：テストの構造（大問・小問）を取得"""
        test = self.get_object()
        question_groups = QuestionGroup.objects.filter(test=test).prefetch_related('questions').order_by('group_number')
        
        # 入力ステータスを取得
        input_status = test.get_input_status()
        
        structure = {
            'test': {
                'id': test.id,
                'grade_level': test.grade_level,
                'grade_level_display': test.get_grade_level_display(),
                'subject': test.subject,
                'subject_display': test.get_subject_display(),
                'max_score': test.max_score,
                'year': test.schedule.year,
                'period': test.schedule.period,
                'period_display': test.schedule.get_period_display(),
                'input_allowed': input_status['allowed'],
                'input_status': input_status,
            },
            'question_groups': []
        }
        
        for group in question_groups:
            questions = group.questions.all().order_by('question_number')
            group_data = {
                'id': group.id,
                'group_number': group.group_number,
                'title': group.title,
                'max_score': group.max_score,
                'questions': [
                    {
                        'id': q.id,
                        'question_number': q.question_number,
                        'content': q.content,
                        'max_score': q.max_score
                    }
                    for q in questions
                ]
            }
            structure['question_groups'].append(group_data)
        
        return Response(structure)
    
    @action(detail=False, methods=['get'])
    def available_tests(self, request):
        """フロントエンド用：利用可能なテスト一覧"""
        tests = self.get_queryset().filter(is_active=True).select_related('schedule')
        
        test_list = []
        for test in tests:
            input_status = test.get_input_status()
            test_list.append({
                'id': test.id,
                'grade_level': test.grade_level,
                'grade_level_display': test.get_grade_level_display(),
                'subject': test.subject,
                'subject_display': test.get_subject_display(),
                'year': test.schedule.year,
                'period': test.schedule.period,
                'period_display': test.schedule.get_period_display(),
                'max_score': test.max_score,
                'question_groups_count': test.question_groups.count(),
                'input_allowed': input_status['allowed'],
                'input_status': input_status['status'],
                'deadline': test.schedule.deadline_at
            })
        
        return Response(test_list)
    
    @action(detail=False, methods=['get'])
    def subjects_for_grade(self, request):
        """学年別の利用可能な科目を取得"""
        grade_level = request.query_params.get('grade_level')
        
        if not grade_level:
            return Response({'error': 'grade_levelパラメータが必要です'}, status=status.HTTP_400_BAD_REQUEST)
        
        subjects = TestDefinition.get_subjects_for_grade(grade_level)
        
        return Response({
            'grade_level': grade_level,
            'grade_level_display': dict(TestDefinition.GRADE_LEVELS).get(grade_level, grade_level),
            'subjects': [{'value': s[0], 'label': s[1]} for s in subjects]
        })
    
    @action(detail=True, methods=['get'])
    def input_status(self, request, pk=None):
        """テストの入力可能状況を取得"""
        test = self.get_object()
        status = test.get_input_status()
        
        return Response({
            'test_id': test.id,
            'test_info': {
                'year': test.schedule.year,
                'period': test.schedule.period,
                'period_display': test.schedule.get_period_display(),
                'grade_level': test.grade_level,
                'grade_level_display': test.get_grade_level_display(),
                'subject': test.subject,
                'subject_display': test.get_subject_display(),
            },
            'input_status': status
        })
    
    @action(detail=True, methods=['get'])
    def download_question_pdf(self, request, pk=None):
        """問題PDFをダウンロード"""
        from django.http import HttpResponse
        from django.shortcuts import get_object_or_404
        
        test = get_object_or_404(TestDefinition, pk=pk)
        
        if not test.question_pdf:
            return Response({'error': '問題PDFが登録されていません'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            with open(test.question_pdf.path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                test_name = f"{test.schedule.year}年度{test.schedule.get_period_display()}{test.get_grade_level_display()}{test.get_subject_display()}"
                response['Content-Disposition'] = f'attachment; filename="{test_name}_問題.pdf"'
                return response
        except FileNotFoundError:
            return Response({'error': 'PDFファイルが見つかりません'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def download_answer_pdf(self, request, pk=None):
        """解答PDFをダウンロード"""
        from django.http import HttpResponse
        from django.shortcuts import get_object_or_404
        
        test = get_object_or_404(TestDefinition, pk=pk)
        
        if not test.answer_pdf:
            return Response({'error': '解答PDFが登録されていません'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            with open(test.answer_pdf.path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                test_name = f"{test.schedule.year}年度{test.schedule.get_period_display()}{test.get_grade_level_display()}{test.get_subject_display()}"
                response['Content-Disposition'] = f'attachment; filename="{test_name}_解答.pdf"'
                return response
        except FileNotFoundError:
            return Response({'error': 'PDFファイルが見つかりません'}, status=status.HTTP_404_NOT_FOUND)

class QuestionGroupViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['test']
    ordering = ['group_number']
    
    def get_queryset(self):
        # 全ての科目のテストの問題グループを対象とする
        return QuestionGroup.objects.all()

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group', 'group__test']
    ordering = ['group', 'question_number']
    
    def get_queryset(self):
        # 全ての科目のテストの問題を対象とする
        return Question.objects.all()

class TestFileListView(APIView):
    """指定された年度・期間のテストファイル一覧を取得"""
    permission_classes = []  # 一時的に認証を無効化
    
    def get(self, request, year, period):
        try:
            # 指定された年度・期間のテストを取得
            schedule = get_object_or_404(TestSchedule, year=year, period=period)
        except Http404:
            # テストスケジュールが存在しない場合は空のリストを返す
            return Response([])

        try:
            tests = TestDefinition.objects.filter(schedule=schedule, is_active=True)

            files = []
            for test in tests:
                # 問題ファイル
                problem_status = self._get_file_status(test.question_pdf)
                files.append({
                    'id': f"{test.id}_problem",
                    'name': f"{test.get_grade_level_display()}{test.get_subject_display()}問題",
                    'type': 'problem',
                    'subject': test.get_subject_display(),
                    'grade': test.get_grade_level_display(),
                    'size': self._get_file_size(test.question_pdf) if problem_status == 'available' else '未準備',
                    'status': problem_status,
                    'test_id': test.id,
                    'year': year,
                    'period': period,
                    'downloadCount': 0 if problem_status != 'available' else 0,
                    'lastUpdated': test.updated_at.isoformat() if test.updated_at else None,
                })

                # 解答ファイル
                answer_status = self._get_file_status(test.answer_pdf)
                files.append({
                    'id': f"{test.id}_answer",
                    'name': f"{test.get_grade_level_display()}{test.get_subject_display()}解答",
                    'type': 'answer',
                    'subject': test.get_subject_display(),
                    'grade': test.get_grade_level_display(),
                    'size': self._get_file_size(test.answer_pdf) if answer_status == 'available' else '未準備',
                    'status': answer_status,
                    'test_id': test.id,
                    'year': year,
                    'period': period,
                    'downloadCount': 0 if answer_status != 'available' else 0,
                    'lastUpdated': test.updated_at.isoformat() if test.updated_at else None,
                })

            return Response(files)
        except Exception as e:
            import traceback
            print(f"ERROR in TestFileListView: {str(e)}")
            print(traceback.format_exc())
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_file_status(self, file_field):
        """ファイルの状態を取得"""
        try:
            # ファイルフィールドが存在しない場合
            if not file_field:
                return 'processing'
            
            # ファイルが登録されているが実ファイルが存在しない場合
            if not hasattr(file_field, 'path') or not os.path.exists(file_field.path):
                return 'error'
            
            # ファイルが存在する場合
            return 'available'
        except:
            return 'error'
    
    def _get_file_size(self, file_field):
        """ファイルサイズを取得"""
        try:
            if file_field and hasattr(file_field, 'size'):
                size = file_field.size
                if size < 1024:
                    return f"{size}B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f}KB"
                else:
                    return f"{size / (1024 * 1024):.1f}MB"
            return "不明"
        except:
            return "不明"

class TestFileDownloadView(APIView):
    """テストファイルをダウンロード"""
    permission_classes = []  # 一時的に認証を無効化
    
    def get(self, request, year, period, file_id):
        try:
            # file_idから test_id と type を解析
            parts = file_id.split('_')
            if len(parts) != 2:
                return Response({'error': 'Invalid file ID'}, status=status.HTTP_400_BAD_REQUEST)
            
            test_id, file_type = parts
            test = get_object_or_404(TestDefinition, id=test_id)
            
            if file_type == 'problem':
                if not test.question_pdf:
                    return Response({'error': '問題ファイルは準備中です'}, status=status.HTTP_404_NOT_FOUND)
                file_field = test.question_pdf
                filename = f"{test.schedule.year}年度{test.schedule.get_period_display()}{test.get_grade_level_display()}{test.get_subject_display()}_問題.pdf"
            elif file_type == 'answer':
                if not test.answer_pdf:
                    return Response({'error': '解答ファイルは準備中です'}, status=status.HTTP_404_NOT_FOUND)
                file_field = test.answer_pdf
                filename = f"{test.schedule.year}年度{test.schedule.get_period_display()}{test.get_grade_level_display()}{test.get_subject_display()}_解答.pdf"
            else:
                return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
            
            # ファイルの存在チェック
            if not hasattr(file_field, 'path') or not os.path.exists(file_field.path):
                return Response({'error': 'ファイルが見つかりません。準備中の可能性があります。'}, status=status.HTTP_404_NOT_FOUND)
            
            try:
                with open(file_field.path, 'rb') as pdf_file:
                    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    return response
            except FileNotFoundError:
                return Response({'error': 'ファイルが見つかりません。準備中の可能性があります。'}, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TestFileBulkDownloadView(APIView):
    """指定された年度・期間の全テストファイルを一括ダウンロード"""
    permission_classes = []  # 一時的に認証を無効化
    
    def get(self, request, year, period):
        try:
            schedule = get_object_or_404(TestSchedule, year=year, period=period)
            tests = TestDefinition.objects.filter(schedule=schedule, is_active=True)
            
            # 一時ファイルを作成してZIPファイルを作成
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                    added_files = 0
                    for test in tests:
                        # 問題ファイルを追加
                        if test.question_pdf and hasattr(test.question_pdf, 'path') and os.path.exists(test.question_pdf.path):
                            try:
                                filename = f"{test.get_grade_level_display()}{test.get_subject_display()}_問題.pdf"
                                zip_file.write(test.question_pdf.path, filename)
                                added_files += 1
                            except (FileNotFoundError, PermissionError):
                                continue
                        
                        # 解答ファイルを追加
                        if test.answer_pdf and hasattr(test.answer_pdf, 'path') and os.path.exists(test.answer_pdf.path):
                            try:
                                filename = f"{test.get_grade_level_display()}{test.get_subject_display()}_解答.pdf"
                                zip_file.write(test.answer_pdf.path, filename)
                                added_files += 1
                            except (FileNotFoundError, PermissionError):
                                continue
                
                # ダウンロード可能なファイルがない場合
                if added_files == 0:
                    os.unlink(tmp_file.name)
                    return Response({'error': 'ダウンロード可能なファイルがありません。ファイルが準備中の可能性があります。'}, status=status.HTTP_404_NOT_FOUND)
                
                # ZIPファイルを読み込んでレスポンスとして返す
                with open(tmp_file.name, 'rb') as zip_data:
                    response = HttpResponse(zip_data.read(), content_type='application/zip')
                    zip_filename = f"{year}年度{schedule.get_period_display()}テスト_全ファイル.zip"
                    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
                
                # 一時ファイルを削除
                os.unlink(tmp_file.name)
                return response
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
