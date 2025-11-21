from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.db import models
from .models import (
    Score, TestResult, CommentTemplate, CommentTemplateV2, StudentComment, TestComment,
    QuestionScore, TestAttendance, IndividualProblem, IndividualProblemScore
)
from .serializers import (
    ScoreSerializer, TestResultSerializer, CommentTemplateSerializer, CommentTemplateV2Serializer, 
    StudentCommentSerializer, TestCommentSerializer,
    QuestionScoreSerializer, TestAttendanceSerializer,
    IndividualProblemSerializer, IndividualProblemScoreSerializer
)

class ScoreViewSet(viewsets.ModelViewSet):
    serializer_class = ScoreSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['test', 'student', 'attendance']
    search_fields = ['student__name', 'student__student_id']
    ordering_fields = ['created_at', 'score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Score.objects.all().select_related('student', 'test', 'question_group')
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_recalculate_results(self, request):
        """テスト結果一括再計算"""
        try:
            test_id = request.data.get('test_id')
            year = request.data.get('year')
            period = request.data.get('period')

            if test_id:
                # 特定のテストのみ再計算
                from tests.models import TestDefinition
                test = TestDefinition.objects.get(id=test_id)
                from .utils import bulk_calculate_test_results
                count = bulk_calculate_test_results(test)

                return Response({
                    'success': True,
                    'message': f'{test}の{count}件の結果を再計算しました',
                    'processed_count': count
                })

            elif year and period:
                # 年度・期間指定で一括再計算
                from tests.models import TestDefinition
                tests = TestDefinition.objects.filter(
                    schedule__year=year,
                    schedule__period=period
                )

                total_count = 0
                processed_tests = []

                for test in tests:
                    from .utils import bulk_calculate_test_results
                    count = bulk_calculate_test_results(test)
                    total_count += count
                    processed_tests.append({
                        'test_name': str(test),
                        'processed_count': count
                    })

                return Response({
                    'success': True,
                    'message': f'{year}年度{period}期の{total_count}件の結果を再計算しました',
                    'total_processed_count': total_count,
                    'processed_tests': processed_tests
                })
            else:
                return Response({
                    'success': False,
                    'error': 'test_id または year と period の指定が必要です'
                }, status=400)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_score(self, request):
        """個別の大問スコアを保存"""
        try:
            student_id = request.data.get('student_id')
            test_id = request.data.get('test_id')
            question_group_number = request.data.get('question_group_number')
            score = request.data.get('score', 0)
            attendance = request.data.get('attendance', True)
            
            if not all([student_id, test_id, question_group_number is not None]):
                return Response({
                    'success': False,
                    'error': 'student_id, test_id, question_group_numberは必須です'
                }, status=400)
            
            from students.models import Student
            from tests.models import TestDefinition, QuestionGroup
            
            # 生徒、テスト、大問グループを取得
            try:
                student = Student.objects.get(student_id=student_id)
                test = TestDefinition.objects.get(id=test_id)
                
                # 大問グループが存在しない場合は自動作成
                question_group, group_created = QuestionGroup.objects.get_or_create(
                    test=test, 
                    group_number=question_group_number,
                    defaults={
                        'title': f'大問{question_group_number}',
                        'max_score': 20  # デフォルト満点
                    }
                )
                
            except (Student.DoesNotExist, TestDefinition.DoesNotExist) as e:
                return Response({
                    'success': False,
                    'error': f'データが見つかりません: {str(e)}'
                }, status=404)
            
            # スコアの保存・更新
            score_obj, created = Score.objects.update_or_create(
                student=student,
                test=test,
                question_group=question_group,
                defaults={
                    'score': int(score),
                    'attendance': attendance
                }
            )
            
            # スコア保存後、TestResultを更新（統一されたロジックを使用）
            from .utils import calculate_test_results
            test_result = calculate_test_results(student, test)
            
            return Response({
                'success': True,
                'score_id': score_obj.id,
                'created': created,
                'total_score': test_result.total_score,
                'correct_rate': float(test_result.correct_rate),
                'message': 'スコアを保存しました'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def generate_all_grades_template(self, request):
        """全学年対応スコアテンプレート生成（CSV形式）"""
        try:
            year = request.query_params.get('year')
            period = request.query_params.get('period')
            
            if not year or not period:
                return Response({
                    'success': False,
                    'error': 'year と period パラメータが必要です'
                }, status=400)
            
            # utils.pyの関数を使用
            from .utils import generate_all_grades_unified_template
            from django.http import HttpResponse
            import tempfile
            import os
            import pandas as pd
            
            df, all_structures = generate_all_grades_unified_template(int(year), period)
            
            # CSVファイルとしてHTTPレスポンスを生成（BOM付きUTF-8）
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8-sig') as tmp_file:
                df.to_csv(tmp_file, index=False)
                tmp_file_path = tmp_file.name
            
            try:
                # ファイル名を生成
                period_display = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}.get(period, period)
                filename = f"スコア入力テンプレート_{year}年{period_display}.csv"
                
                with open(tmp_file_path, 'rb') as f:
                    response = HttpResponse(
                        f.read(),
                        content_type='text/csv; charset=utf-8-sig'
                    )
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    
                return response
            finally:
                os.unlink(tmp_file_path)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def export_scores_with_students(self, request):
        """実際の生徒データと既存の点数を含むCSVエクスポート"""
        try:
            year = request.query_params.get('year')
            period = request.query_params.get('period')

            if not year or not period:
                return Response({
                    'success': False,
                    'error': 'year と period パラメータが必要です'
                }, status=400)

            from students.models import Student, StudentEnrollment
            from tests.models import TestDefinition, TestSchedule, QuestionGroup
            from django.db.models import Q
            import pandas as pd
            import tempfile
            import os

            # 指定された年度・期間のテストスケジュールを取得
            try:
                schedule = TestSchedule.objects.get(year=int(year), period=period)
            except TestSchedule.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'{year}年度{period}期のテストスケジュールが見つかりません'
                }, status=404)

            # その期間に登録されている生徒を取得（StudentEnrollment経由）
            enrollments = StudentEnrollment.objects.filter(
                year=int(year),
                period=period
            ).select_related('student', 'student__classroom', 'student__classroom__school')

            # ユーザーの権限に応じてフィルタリング
            user = request.user
            if user.role == 'school_admin' and hasattr(user, 'school_id'):
                enrollments = enrollments.filter(
                    student__classroom__school__school_id=user.school_id
                )
            elif user.role == 'classroom_admin' and hasattr(user, 'classroom_id'):
                enrollments = enrollments.filter(
                    student__classroom__classroom_id=user.classroom_id
                )

            # 全テスト定義を取得
            test_definitions = TestDefinition.objects.filter(schedule=schedule)

            # 大問グループ情報を事前に取得
            question_groups_by_test = {}
            for test_def in test_definitions:
                question_groups = list(QuestionGroup.objects.filter(test=test_def).order_by('group_number'))
                question_groups_by_test[test_def.id] = question_groups

            # CSVのカラムを動的に生成
            columns = ['塾ID', '塾名', '教室ID', '教室名', '生徒ID', '生徒名', '学年', '年度', '期間', '出席']

            # 教科ごとの大問列を追加（大問数が最も多いテストを使用して重複を防ぐ）
            subject_columns = {}
            subject_max_questions = {}  # 各教科の最大大問数を記録

            for test_def in test_definitions:
                subject_display = test_def.get_subject_display()
                question_groups = question_groups_by_test[test_def.id]

                # 各教科で最も大問数が多いテスト構造を使用
                if subject_display not in subject_max_questions or len(question_groups) > subject_max_questions[subject_display]:
                    subject_max_questions[subject_display] = len(question_groups)
                    subject_columns[subject_display] = []

                    for qg in question_groups:
                        subject_columns[subject_display].append(f'{subject_display}_大問{qg.group_number}')
                    subject_columns[subject_display].append(f'{subject_display}_合計点')

            # カラムを追加（国語、算数の順）
            for subject in ['国語', '算数', '英語', '数学']:
                if subject in subject_columns:
                    columns.extend(subject_columns[subject])

            columns.append('全体合計点')

            # 全ての生徒IDを取得
            student_ids = [enrollment.student.id for enrollment in enrollments]

            # 全生徒の全スコアを一括取得（N+1問題を解決）
            all_scores = Score.objects.filter(
                student__id__in=student_ids,
                test__schedule=schedule
            ).select_related('student', 'test', 'question_group').values(
                'student_id',
                'test_id',
                'question_group_id',
                'score',
                'attendance',
                'question_group__group_number'
            )

            # スコアを辞書形式で整理: student_id -> test_id -> question_group_id -> score_data
            scores_dict = {}
            for score_data in all_scores:
                student_id = score_data['student_id']
                test_id = score_data['test_id']
                qg_id = score_data['question_group_id']

                if student_id not in scores_dict:
                    scores_dict[student_id] = {}
                if test_id not in scores_dict[student_id]:
                    scores_dict[student_id][test_id] = {}

                scores_dict[student_id][test_id][qg_id] = score_data

            # 登録がない場合のチェック
            if not enrollments.exists():
                return Response({
                    'success': False,
                    'error': f'{year}年度{period}期の登録生徒が見つかりません。権限設定を確認してください。'
                }, status=404)

            # データ行を生成
            data_rows = []

            for enrollment in enrollments:
                student = enrollment.student

                row_data = {
                    '塾ID': student.classroom.school.school_id if student.classroom else '',
                    '塾名': student.classroom.school.name if student.classroom else '',
                    '教室ID': student.classroom.classroom_id if student.classroom else '',
                    '教室名': student.classroom.name if student.classroom else '',
                    '生徒ID': student.student_id,
                    '生徒名': student.name,
                    '学年': student.grade,
                    '年度': year,
                    '期間': {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}.get(period, period),
                    '出席': '出席',  # デフォルトは出席
                }

                total_score = 0
                student_scores = scores_dict.get(student.id, {})

                # 各教科の点数を取得
                for test_def in test_definitions:
                    subject_display = test_def.get_subject_display()
                    question_groups = question_groups_by_test[test_def.id]
                    subject_total = 0
                    test_scores = student_scores.get(test_def.id, {})

                    # 生徒のこの教科のテストの全スコアを取得
                    for qg in question_groups:
                        col_name = f'{subject_display}_大問{qg.group_number}'

                        # 既存の点数を辞書から取得（キーはquestion_group_id）
                        score_data = test_scores.get(qg.id)

                        if score_data:
                            row_data[col_name] = score_data['score']
                            subject_total += score_data['score']
                            if not score_data['attendance']:
                                row_data['出席'] = '欠席'
                        else:
                            row_data[col_name] = ''  # 未入力は空欄

                    row_data[f'{subject_display}_合計点'] = subject_total if subject_total > 0 else ''
                    total_score += subject_total

                row_data['全体合計点'] = total_score if total_score > 0 else ''
                data_rows.append(row_data)

            # DataFrameを作成
            df = pd.DataFrame(data_rows, columns=columns)

            # CSVファイルとしてHTTPレスポンスを生成（BOM付きUTF-8）
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8-sig') as tmp_file:
                df.to_csv(tmp_file, index=False)
                tmp_file_path = tmp_file.name

            try:
                # ファイル名を生成
                period_display = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}.get(period, period)
                filename = f"生徒データ_得点入り_{year}年{period_display}.csv"

                with open(tmp_file_path, 'rb') as f:
                    response = HttpResponse(
                        f.read(),
                        content_type='text/csv; charset=utf-8-sig'
                    )
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'

                return response
            finally:
                os.unlink(tmp_file_path)

        except Exception as e:
            import traceback
            import sys

            # 詳細なエラーログを出力
            print('='*80, file=sys.stderr)
            print('ERROR in export_scores_with_students:', file=sys.stderr)
            print('Error type:', type(e).__name__, file=sys.stderr)
            print('Error message:', str(e), file=sys.stderr)
            print('Full traceback:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            print('='*80, file=sys.stderr)

            return Response({
                'success': False,
                'error': f'{type(e).__name__}: {str(e)}'
            }, status=500)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def import_excel(self, request):
        """ExcelまたはCSVファイルからスコアを一括インポート"""
        try:
            if 'file' not in request.FILES:
                return Response({
                    'success': False,
                    'error': 'ファイルが必要です'
                }, status=400)
            
            file = request.FILES['file']
            
            # ファイルを処理
            import pandas as pd
            import io
            from tests.models import TestDefinition, QuestionGroup
            from students.models import Student
            
            try:
                # ファイル形式を判定して読み込み
                file_content = file.read()
                file.seek(0)  # ファイルポインタをリセット
                
                if file.name.endswith('.csv'):
                    # CSVファイルを読み込み
                    df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
                else:
                    # Excelファイルを読み込み
                    df = pd.read_excel(io.BytesIO(file_content))
            except Exception as e:
                return Response({
                    'success': False,
                    'error': f'ファイルの読み込みに失敗しました: {str(e)}'
                }, status=400)
            
            success_count = 0
            error_count = 0
            warnings = []
            validation_errors = []
            missing_data = []
            
            # 各行を処理
            for index, row in df.iterrows():
                try:
                    student_id = str(row.get('生徒ID', '')).strip()
                    if not student_id:
                        continue
                    
                    # 生徒を検索
                    try:
                        student = Student.objects.get(student_id=student_id)
                    except Student.DoesNotExist:
                        warnings.append(f'行{index+2}: 生徒ID {student_id} が見つかりません')
                        error_count += 1
                        continue
                    
                    # 年度と期間をCSVから取得
                    year = row.get('年度', 2025)
                    period_jp = row.get('期間', '夏期')
                    
                    # 期間を英語に変換
                    period_map = {'春期': 'spring', '夏期': 'summer', '秋期': 'autumn', '冬期': 'winter'}
                    period = period_map.get(period_jp, 'summer')
                    
                    # 各科目の得点を処理
                    for col in df.columns:
                        # 基本情報列をスキップ
                        if col in ['塾ID', '塾名', '教室ID', '教室名', '生徒ID', '生徒名', '学年', '年度', '期間', '出席', 
                                  '国語_合計点', '算数_合計点', '全体合計点']:
                            continue
                        
                        # 列名から教科と大問番号を解析
                        # 例: "国語_大問1", "算数_大問2"
                        if '_大問' in col:
                            col_parts = col.split('_')
                            if len(col_parts) >= 2:
                                subject_jp = col_parts[0]
                                question_part = col_parts[1]  # "大問1"など
                                
                                # 科目名を英語に変換
                                subject_map = {'国語': 'japanese', '算数': 'math', '数学': 'math'}
                                subject = subject_map.get(subject_jp)
                                if not subject:
                                    continue
                                
                                # 大問番号を抽出
                                import re
                                question_match = re.search(r'大問(\d+)', question_part)
                                if not question_match:
                                    continue
                                
                                question_number = int(question_match.group(1))
                                
                                # 点数を取得
                                score = row.get(col, '')
                                if pd.isna(score) or score == '':
                                    # 未入力データを記録
                                    missing_data.append({
                                        'row': index + 2,
                                        'student_id': student_id,
                                        'student_name': row.get('生徒名', ''),
                                        'subject': subject_jp,
                                        'question': f'大問{question_number}',
                                        'message': f'行{index+2}: {row.get("生徒名", "")}({student_id})の{subject_jp}大問{question_number}が未入力です'
                                    })
                                    continue
                                    
                                try:
                                    score = float(score)
                                except (ValueError, TypeError):
                                    warnings.append(f'行{index+2}: {subject_jp}大問{question_number}の値が無効です: {score}')
                                    continue
                                
                                # 学年に応じたテスト定義を検索
                                grade_str = str(student.grade) if hasattr(student, 'grade') else '1'
                                if grade_str.startswith('小'):
                                    grade_num = grade_str.replace('小', '')
                                    grade_level = f'elementary_{grade_num}'
                                elif grade_str.startswith('中'):
                                    grade_num = grade_str.replace('中', '')
                                    grade_level = f'middle_{grade_num}'
                                else:
                                    grade_level = f'elementary_{grade_str}'
                                
                                try:
                                    test = TestDefinition.objects.get(
                                        schedule__year=year,
                                        schedule__period=period,
                                        subject=subject,
                                        grade_level=grade_level
                                    )
                                except TestDefinition.DoesNotExist:
                                    # フォールバック: 学年に関係なく同じ科目のテストを探す
                                    try:
                                        test = TestDefinition.objects.filter(
                                            schedule__year=year,
                                            schedule__period=period,
                                            subject=subject
                                        ).first()
                                        if not test:
                                            continue
                                    except:
                                        continue
                                
                                # 大問グループを検索
                                try:
                                    question_group = QuestionGroup.objects.get(
                                        test=test,
                                        group_number=question_number
                                    )
                                except QuestionGroup.DoesNotExist:
                                    warnings.append(f'行{index+2}: {subject_jp}大問{question_number}のグループが見つかりません')
                                    continue
                                
                                # 満点チェック
                                if score > question_group.max_score:
                                    validation_errors.append({
                                        'row': index + 2,
                                        'student_id': student_id,
                                        'student_name': row.get('生徒名', ''),
                                        'subject': subject_jp,
                                        'question': f'大問{question_number}',
                                        'score': score,
                                        'max_score': question_group.max_score,
                                        'message': f'行{index+2}: {row.get("生徒名", "")}({student_id})の{subject_jp}大問{question_number}が満点を超えています（{score}点 > {question_group.max_score}点）'
                                    })
                                    continue
                                
                                # スコアを保存
                                Score.objects.update_or_create(
                                    student=student,
                                    test=test,
                                    question_group=question_group,
                                    defaults={
                                        'score': int(score),
                                        'attendance': True
                                    }
                                )
                    
                    success_count += 1
                    
                except Exception as e:
                    warnings.append(f'行{index+2}: エラー - {str(e)}')
                    error_count += 1
            
            # CSVにない大問を0点で補完し、TestResultを統一ロジックで更新
            from .utils import calculate_test_results
            for student_id in df['生徒ID'].dropna().unique():
                try:
                    student = Student.objects.get(student_id=str(student_id))

                    # 各テストの合計点を計算してTestResultを更新
                    tests = TestDefinition.objects.filter(
                        schedule__year=2025,
                        schedule__period='summer'
                    )

                    for test in tests:
                        # CSVにない大問を0点で補完
                        all_question_groups = test.question_groups.all()
                        for question_group in all_question_groups:
                            score_exists = Score.objects.filter(
                                student=student,
                                test=test,
                                question_group=question_group
                            ).exists()

                            if not score_exists:
                                # CSVにない大問は0点で補完
                                Score.objects.create(
                                    student=student,
                                    test=test,
                                    question_group=question_group,
                                    score=0,
                                    attendance=True
                                )

                        # 統一されたロジックでTestResultを計算・更新
                        calculate_test_results(student, test)

                except Exception as e:
                    warnings.append(f'TestResult更新エラー (生徒ID: {student_id}): {str(e)}')
            
            # データ検証結果をまとめる
            has_validation_errors = len(validation_errors) > 0
            has_missing_data = len(missing_data) > 0
            
            return Response({
                'success': True,
                'message': f'処理完了: 成功 {success_count}件, エラー {error_count}件',
                'warnings': warnings[:20],  # 最初の20件
                'success_count': success_count,
                'error_count': error_count,
                'validation_errors': validation_errors[:20],  # 満点超過エラー
                'missing_data': missing_data[:20],            # 未入力データ
                'has_validation_errors': has_validation_errors,
                'has_missing_data': has_missing_data,
                'validation_summary': {
                    'total_validation_errors': len(validation_errors),
                    'total_missing_data': len(missing_data),
                    'total_warnings': len(warnings)
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

class TestResultViewSet(viewsets.ModelViewSet):
    serializer_class = TestResultSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['test', 'student']
    search_fields = ['student__name', 'student__student_id']
    ordering_fields = ['total_score', 'created_at']
    ordering = ['-total_score']
    
    def get_queryset(self):
        # 出席者のみを返す（欠席者は除外）
        # TestResultがあるということは出席者のスコアから生成されているため、基本的に出席者のみ
        return TestResult.objects.all().select_related('student', 'test')
    
    @action(detail=False, methods=['get'])
    def detailed_results(self, request):
        """生徒管理・帳票ダウンロード用の詳細データ"""
        from django.db.models import Avg
        from .models import Score
        
        # フィルタパラメータ
        test_id = request.query_params.get('test')
        year = request.query_params.get('year')
        period = request.query_params.get('period')
        school_id = request.query_params.get('school')
        student_id = request.query_params.get('student_id')
        
        # TestResultをフィルタ
        queryset = self.get_queryset()
        
        # リクエスト元を判別してフィルタリングを決定
        # classroom管理者かつclassroomページからのリクエストの場合のみ、自分の教室に制限
        is_classroom_page = 'classroom' in request.META.get('HTTP_REFERER', '') or request.query_params.get('app_context') == 'classroom'
        
        if request.user.role == 'classroom_admin' and hasattr(request.user, 'classroom_id') and is_classroom_page:
            queryset = queryset.filter(student__classroom__classroom_id=request.user.classroom_id)
        
        if test_id:
            queryset = queryset.filter(test_id=test_id)
        elif year and period:
            queryset = queryset.filter(
                test__schedule__year=year,
                test__schedule__period=period
            )
        
        # 教室管理者以外（塾管理者など）の場合のみschool_idでフィルタリング
        if school_id and request.user.role != 'classroom_admin':
            queryset = queryset.filter(student__classroom__school_id=school_id)
        
        # 特定の生徒でフィルタリング
        if student_id:
            queryset = queryset.filter(student__student_id=student_id)
        
        # 重複を避けるため、教科・年度・期間の組み合わせごとに最高得点の結果のみ取得
        unique_results = {}
        
        for test_result in queryset:
            subject = test_result.test.get_subject_display()
            year = test_result.test.schedule.year
            period = test_result.test.schedule.period
            
            key = f"{subject}-{year}-{period}"
            
            # 同じキーで既存の結果がない、または現在の結果がより高い得点の場合のみ保持
            if key not in unique_results or test_result.total_score > unique_results[key].total_score:
                unique_results[key] = test_result
        
        results = []
        
        for test_result in unique_results.values():
            # 大問別得点を取得（有効な得点のみ）
            question_scores = Score.objects.filter(
                student=test_result.student,
                test=test_result.test,
                attendance=True,
                score__gte=0  # 0点以上の有効な得点のみ
            ).order_by('question_group__group_number')
            
            question_details = []
            total_max_score = 0
            for score in question_scores:
                question_details.append({
                    'question_number': score.question_group.group_number,
                    'score': score.score,
                    'max_score': score.question_group.max_score
                })
                total_max_score += score.question_group.max_score
            
            # 学年順位（TestResultに既に保存されている順位を優先使用）
            if test_result.grade_rank and test_result.grade_total:
                grade_rank = test_result.grade_rank
                grade_total = test_result.grade_total
            else:
                # 保存されていない場合は計算
                grade_rank = TestResult.objects.filter(
                    test=test_result.test,
                    student__grade=test_result.student.grade,
                    total_score__gt=test_result.total_score
                ).count() + 1
                
                grade_total = TestResult.objects.filter(
                    test=test_result.test,
                    student__grade=test_result.student.grade
                ).count()
            
            # 学年平均と標準偏差を計算
            from django.db.models import StdDev
            grade_stats = TestResult.objects.filter(
                test=test_result.test,
                student__grade=test_result.student.grade
            ).aggregate(
                avg=Avg('total_score'),
                std_dev=StdDev('total_score')
            )
            grade_average = grade_stats['avg'] or 0
            grade_std_dev = grade_stats['std_dev'] or 1  # 0で割ることを防ぐ
            
            # 偏差値を計算 (平均50, 標準偏差10)
            if grade_std_dev > 0 and grade_average > 0:
                deviation_score = 50 + (test_result.total_score - grade_average) / grade_std_dev * 10
                deviation_score = max(0, min(100, deviation_score))  # 0-100の範囲に制限
            else:
                deviation_score = 50
            
            # 学年別大問平均を計算（有効な得点のみ）
            question_averages = Score.objects.filter(
                test=test_result.test,
                student__grade=test_result.student.grade,
                attendance=True,
                score__gte=0  # 0点以上の有効な得点のみ
            ).values('question_group__group_number').annotate(
                avg_score=Avg('score')
            ).order_by('question_group__group_number')
            
            question_avg_dict = {}
            for q_avg in question_averages:
                question_avg_dict[q_avg['question_group__group_number']] = q_avg['avg_score']
            
            results.append({
                'id': test_result.id,
                'student_id': test_result.student.student_id,
                'student_name': test_result.student.name,
                'grade': test_result.student.grade,
                'school_name': test_result.student.classroom.school.name if test_result.student.classroom else '',
                'classroom_name': test_result.student.classroom.name if test_result.student.classroom else '',
                # フロントエンド互換性のための直接フィールド
                'test_name': test_result.test.get_subject_display(),
                'year': test_result.test.schedule.year,
                'period': test_result.test.schedule.period,
                'total_score': test_result.total_score,
                'max_score': total_max_score,
                # 詳細情報（既存の構造も維持）
                'test_info': {
                    'year': test_result.test.schedule.year,
                    'period': test_result.test.schedule.get_period_display(),
                    'subject': test_result.test.get_subject_display(),
                    'grade_level': test_result.test.get_grade_level_display()
                },
                'scores': {
                    'total_score': test_result.total_score,
                    'correct_rate': float(test_result.correct_rate),
                    'question_details': question_details
                },
                'rankings': {
                    'grade_rank': grade_rank,
                    'grade_total': grade_total,
                    'national_rank': test_result.national_rank_temporary,
                    'national_total': test_result.national_total_temporary,
                    # TestResultに既に保存されている偏差値を優先使用
                    'deviation_score': test_result.grade_deviation_score or round(deviation_score, 1)
                },
                'averages': {
                    'grade_average': float(grade_average),
                    'question_averages': question_avg_dict
                }
            })
        
        return Response({
            'results': results,
            'total_count': len(results)
        })
    
    @action(detail=False, methods=['get'])
    def export_data(self, request):
        """結果・データ出力用のCSVエクスポート"""
        import csv
        import io
        from django.http import HttpResponse
        from django.db.models import Avg
        from .models import Score
        
        # 同じフィルタロジックを使用
        test_id = request.query_params.get('test')
        year = request.query_params.get('year')
        period = request.query_params.get('period')
        school_id = request.query_params.get('school')
        
        queryset = self.get_queryset()
        
        # リクエスト元を判別してフィルタリングを決定
        # classroom管理者かつclassroomページからのリクエストの場合のみ、自分の教室に制限
        is_classroom_page = 'classroom' in request.META.get('HTTP_REFERER', '') or request.query_params.get('app_context') == 'classroom'
        
        if request.user.role == 'classroom_admin' and hasattr(request.user, 'classroom_id') and is_classroom_page:
            queryset = queryset.filter(student__classroom__classroom_id=request.user.classroom_id)
        
        if test_id:
            queryset = queryset.filter(test_id=test_id)
        elif year and period:
            queryset = queryset.filter(
                test__schedule__year=year,
                test__schedule__period=period
            )
        
        # 教室管理者以外（塾管理者など）の場合のみschool_idでフィルタリング
        if school_id and request.user.role != 'classroom_admin':
            queryset = queryset.filter(student__classroom__school_id=school_id)
        
        # CSVレスポンスを作成
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー行
        headers = [
            '生徒ID', '生徒名', '学年', '塾名', '教室名',
            '合計点', '正答率(%)', '学年順位', '学年内総数', '学年平均点'
        ]
        
        # 大問数を取得してヘッダーに追加
        if queryset.exists():
            sample_result = queryset.first()
            question_count = Score.objects.filter(
                student=sample_result.student,
                test=sample_result.test,
                attendance=True
            ).count()
            
            for i in range(1, question_count + 1):
                headers.extend([f'大問{i}得点', f'大問{i}平均'])
        
        writer.writerow(headers)
        
        # データ行
        for test_result in queryset:
            # 基本情報
            row = [
                test_result.student.student_id,
                test_result.student.name,
                f'{test_result.student.grade}年生',
                test_result.student.classroom.school.name if test_result.student.classroom else '',
                test_result.student.classroom.name if test_result.student.classroom else '',
                test_result.total_score,
                float(test_result.correct_rate),
            ]
            
            # 学年順位と平均
            grade_rank = TestResult.objects.filter(
                test=test_result.test,
                student__grade=test_result.student.grade,
                total_score__gt=test_result.total_score
            ).count() + 1
            
            grade_total = TestResult.objects.filter(
                test=test_result.test,
                student__grade=test_result.student.grade
            ).count()
            
            grade_average = TestResult.objects.filter(
                test=test_result.test,
                student__grade=test_result.student.grade
            ).aggregate(avg=Avg('total_score'))['avg'] or 0
            
            row.extend([grade_rank, grade_total, float(grade_average)])
            
            # 大問別得点と平均
            question_scores = Score.objects.filter(
                student=test_result.student,
                test=test_result.test,
                attendance=True
            ).order_by('question_group__group_number')
            
            question_averages = Score.objects.filter(
                test=test_result.test,
                student__grade=test_result.student.grade,
                attendance=True
            ).values('question_group__group_number').annotate(
                avg_score=Avg('score')
            ).order_by('question_group__group_number')
            
            q_avg_dict = {}
            for q_avg in question_averages:
                q_avg_dict[q_avg['question_group__group_number']] = q_avg['avg_score']
            
            for score in question_scores:
                q_num = score.question_group.group_number
                q_avg = q_avg_dict.get(q_num, 0)
                row.extend([score.score, float(q_avg)])
            
            writer.writerow(row)
        
        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="test_results_{year}_{period}.csv"'
        
        return response
    
    @action(detail=False, methods=['get'])
    def integrated_student_results(self, request):
        """生徒ID単位での統合テスト結果（国語・算数合算）"""
        from django.db.models import Avg, Sum, Count, Q
        from .models import Score
        from students.models import Student
        
        # フィルタパラメータ
        year = request.query_params.get('year')
        period = request.query_params.get('period')
        school_id = request.query_params.get('school')
        
        if not year or not period:
            return Response({'error': 'year and period parameters are required'}, status=400)
        
        # 対象テストを取得（出席・欠席問わず）
        test_filter = Q(test__schedule__year=year, test__schedule__period=period)
        
        # リクエスト元を判別してフィルタリングを決定
        # classroom管理者かつclassroomページからのリクエストの場合のみ、自分の教室に制限
        is_classroom_page = 'classroom' in request.META.get('HTTP_REFERER', '') or request.query_params.get('app_context') == 'classroom'

        if request.user.role == 'classroom_admin' and hasattr(request.user, 'classroom_id') and request.user.classroom_id and is_classroom_page:
            # 教室管理者は自分の教室のみに制限
            test_filter &= Q(student__classroom__classroom_id=request.user.classroom_id)
        elif request.user.role == 'school_admin':
            # 塾管理者は必ず自分の塾のみに制限
            if hasattr(request.user, 'school_id') and request.user.school_id:
                test_filter &= Q(student__classroom__school__school_id=request.user.school_id)
            else:
                # school_idが取得できない場合はエラー
                return Response({'error': 'School ID not found for this user'}, status=403)
        elif school_id:
            # その他のケースでschool_idパラメータがある場合
            test_filter &= Q(student__classroom__school_id=school_id)
        else:
            # パラメータもユーザー情報もない場合はエラー
            return Response({'error': 'Insufficient permissions or missing school parameter'}, status=403)
        
        # 生徒別の科目ごと合計点を計算
        student_subject_totals = Score.objects.filter(test_filter).values(
            'student__student_id',
            'student__name', 
            'student__grade',
            'student__classroom__school__name',
            'student__classroom__name',
            'test__subject',
            'attendance'
        ).annotate(
            subject_total=Sum('score'),
            question_count=Count('question_group')
        )
        
        # 生徒別にデータを整理
        student_data = {}
        
        for record in student_subject_totals:
            student_id = record['student__student_id']
            subject = record['test__subject']
            
            if student_id not in student_data:
                student_data[student_id] = {
                    'student_id': student_id,
                    'student_name': record['student__name'],
                    'grade': record['student__grade'],
                    'school_name': record['student__classroom__school__name'],
                    'classroom_name': record['student__classroom__name'],
                    'subjects': {},
                    'combined_total': 0
                }
            
            student_data[student_id]['subjects'][subject] = {
                'total_score': record['subject_total'],
                'question_count': record['question_count'],
                'attendance': record['attendance']
            }
            # 出席者のみ合計点に加算
            if record['attendance']:
                student_data[student_id]['combined_total'] += record['subject_total']
        
        # 【最適化】全生徒の大問別得点を一括取得
        all_question_scores = Score.objects.filter(
            test_filter,
            attendance=True
        ).select_related('student', 'question_group').values(
            'student__student_id',
            'test__subject',
            'question_group__group_number',
            'score',
            'question_group__max_score'
        ).order_by('student__student_id', 'test__subject', 'question_group__group_number')

        # 生徒別・科目別の大問得点を整理
        student_question_scores = {}
        for qs in all_question_scores:
            student_id = qs['student__student_id']
            subject = qs['test__subject']

            if student_id not in student_question_scores:
                student_question_scores[student_id] = {}
            if subject not in student_question_scores[student_id]:
                student_question_scores[student_id][subject] = []

            student_question_scores[student_id][subject].append({
                'question_number': qs['question_group__group_number'],
                'score': qs['score'],
                'max_score': qs['question_group__max_score']
            })

        # 【最適化】大問別平均を一括計算（学年・科目・大問ごと）
        all_question_averages = Score.objects.filter(
            test__schedule__year=year,
            test__schedule__period=period,
            attendance=True
        ).values(
            'student__grade',
            'test__subject',
            'question_group__group_number'
        ).annotate(
            avg_score=Avg('score')
        )

        # 辞書形式で整理: grade -> subject -> question_number -> avg_score
        question_avg_cache = {}
        for q_avg in all_question_averages:
            grade = q_avg['student__grade']
            subject = q_avg['test__subject']
            q_num = q_avg['question_group__group_number']

            if grade not in question_avg_cache:
                question_avg_cache[grade] = {}
            if subject not in question_avg_cache[grade]:
                question_avg_cache[grade][subject] = {}

            question_avg_cache[grade][subject][q_num] = q_avg['avg_score']

        # 各生徒の詳細情報を追加
        results = []

        for student_id, data in student_data.items():
            # 大問別得点を取得（既に一括取得済み）
            detailed_scores = student_question_scores.get(student_id, {})
            
            # 学年ごとの順位と平均を計算
            grade = data['grade']
            
            # 合算での学年順位（全国）
            combined_grade_rank = len([s for s in student_data.values() 
                                     if s['grade'] == grade and s['combined_total'] > data['combined_total']]) + 1
            combined_grade_total = len([s for s in student_data.values() if s['grade'] == grade])
            combined_grade_avg = sum([s['combined_total'] for s in student_data.values() if s['grade'] == grade]) / combined_grade_total if combined_grade_total > 0 else 0
            
            # 塾内順位と平均（同じ学校の生徒のみ）
            school_students = [s for s in student_data.values() 
                             if s['grade'] == grade and s['school_name'] == data['school_name']]
            combined_school_rank = len([s for s in school_students if s['combined_total'] > data['combined_total']]) + 1
            combined_school_total = len(school_students)
            combined_school_avg = sum([s['combined_total'] for s in school_students]) / combined_school_total if combined_school_total > 0 else 0
            
            # 科目別順位・平均
            subject_rankings = {}
            subject_averages = {}
            
            for subject in data['subjects'].keys():
                # 科目別学年順位（全国）
                subject_students = [s for s in student_data.values() 
                                  if s['grade'] == grade and subject in s['subjects']]
                subject_score = data['subjects'][subject]['total_score']
                
                subject_grade_rank = len([s for s in subject_students 
                                        if s['subjects'][subject]['total_score'] > subject_score]) + 1
                subject_grade_total = len(subject_students)
                subject_grade_avg = sum([s['subjects'][subject]['total_score'] for s in subject_students]) / subject_grade_total if subject_grade_total > 0 else 0
                
                # 科目別塾内順位
                subject_school_students = [s for s in subject_students 
                                         if s['school_name'] == data['school_name']]
                subject_school_rank = len([s for s in subject_school_students 
                                         if s['subjects'][subject]['total_score'] > subject_score]) + 1
                subject_school_total = len(subject_school_students)
                subject_school_avg = sum([s['subjects'][subject]['total_score'] for s in subject_school_students]) / subject_school_total if subject_school_total > 0 else 0
                
                subject_rankings[subject] = {
                    'grade_rank': subject_grade_rank,
                    'grade_total': subject_grade_total,
                    'school_rank': subject_school_rank,
                    'school_total': subject_school_total
                }
                
                subject_averages[subject] = {
                    'grade_average': subject_grade_avg,
                    'school_average': subject_school_avg
                }

                # 【最適化】大問別平均をキャッシュから取得
                subject_averages[subject]['question_averages'] = question_avg_cache.get(grade, {}).get(subject, {})
            
            results.append({
                'student_id': student_id,
                'student_name': data['student_name'],
                'grade': grade,
                'school_name': data['school_name'],
                'classroom_name': data['classroom_name'],
                'test_info': {
                    'year': int(year),
                    'period': period,
                },
                'combined_results': {
                    'total_score': data['combined_total'],
                    'grade_rank': combined_grade_rank,
                    'grade_total': combined_grade_total,
                    'grade_average': combined_grade_avg,
                    'school_rank': combined_school_rank,
                    'school_total': combined_school_total,
                    'school_average': combined_school_avg,
                    'attendance': any(data['subjects'][subject]['attendance'] for subject in data['subjects'].keys())
                },
                'subject_results': {
                    subject: {
                        'total_score': data['subjects'][subject]['total_score'],
                        'rankings': subject_rankings[subject],
                        'averages': subject_averages[subject],
                        'question_details': detailed_scores.get(subject, []),
                        'attendance': data['subjects'][subject]['attendance']
                    } for subject in data['subjects'].keys()
                }
            })
        
        # 合算点数でソート
        results.sort(key=lambda x: x['combined_results']['total_score'], reverse=True)
        
        return Response({
            'results': results,
            'total_count': len(results),
            'summary': {
                'year': int(year),
                'period': period,
                'subjects_available': list(set().union(*[list(r['subject_results'].keys()) for r in results])),
                'grade_distribution': {}
            }
        })

    @action(detail=False, methods=['get'], permission_classes=[])
    def available_periods(self, request):
        """利用可能な年度と期間の一覧を返す"""
        from test_schedules.models import TestSchedule

        # 全てのTestScheduleから年度と期間を取得
        schedules = TestSchedule.objects.all().values('year', 'period').distinct().order_by('-year', 'period')

        # 年度のリストを作成
        years = sorted(list(set([s['year'] for s in schedules])), reverse=True)

        # 期間のリストを作成（期間の順序を定義）
        period_order = {'spring': 1, 'summer': 2, 'winter': 3}
        periods_set = set([s['period'] for s in schedules])
        periods = sorted(list(periods_set), key=lambda x: period_order.get(x, 999))

        return Response({
            'years': years,
            'periods': periods
        })

class CommentTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = CommentTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CommentTemplate.objects.all()


class QuestionScoreViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionScoreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return QuestionScore.objects.all()

class TestAttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = TestAttendanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TestAttendance.objects.all()

class IndividualProblemViewSet(viewsets.ModelViewSet):
    serializer_class = IndividualProblemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return IndividualProblem.objects.all()

class IndividualProblemScoreViewSet(viewsets.ModelViewSet):
    serializer_class = IndividualProblemScoreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return IndividualProblemScore.objects.all()
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def generate_individual_report(self, request):
        """個別成績表帳票生成エンドポイント"""
        from .utils import generate_individual_report_template

        try:
            student_id = request.data.get('studentId')
            year = request.data.get('year')
            period = request.data.get('period')
            format_type = request.data.get('format', 'pdf')

            print(f"個別帳票生成開始: studentId={student_id}, year={year}, period={period}, format={format_type}")

            if not all([student_id, year, period]):
                return Response({
                    'success': False,
                    'error': 'studentId, year, periodは必須パラメータです'
                }, status=400)

            result = generate_individual_report_template(
                student_id=student_id,
                year=year,
                period=period,
                format_type=format_type
            )

            print(f"帳票生成結果: {result}")

            return Response(result)

        except Exception as e:
            print(f"個別帳票生成API例外: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], authentication_classes=[], url_path='preview-individual-report')
    def preview_individual_report(self, request):
        """個別成績表HTML印刷プレビュー"""
        from .utils import get_individual_report_data
        from django.template.loader import render_to_string
        import os
        from django.conf import settings

        try:
            student_id = request.query_params.get('studentId')
            year = request.query_params.get('year')
            period = request.query_params.get('period')

            if not all([student_id, year, period]):
                return HttpResponse(
                    '<html><body><h1>エラー</h1><p>studentId, year, periodパラメータが必要です</p></body></html>',
                    content_type='text/html'
                )

            # 成績データを取得
            report_data = get_individual_report_data(student_id, year, period)
            if not report_data:
                return HttpResponse(
                    '<html><body><h1>エラー</h1><p>該当する成績データが見つかりません</p></body></html>',
                    content_type='text/html'
                )

            # CSS読み込み
            css_path = os.path.join(settings.BASE_DIR, 'static', 'reports', 'report.css')
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
            except FileNotFoundError:
                css_content = ''

            # ロゴパス
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'reports', 'logo.svg')

            # テンプレートデータ準備
            from datetime import datetime
            template_data = {
                'css_content': css_content,
                'logo_url': f'file://{logo_path}',
                'issue_date': datetime.now().strftime('%Y年%m月%d日'),
                **report_data
            }

            # HTML生成
            html_content = render_to_string('reports/individual_report.html', template_data)

            # 印刷用のJavaScriptを追加
            print_script = '''
<script>
function printReport() {
    window.print();
}

// Ctrl+P または Cmd+P でも印刷可能
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        printReport();
    }
});
</script>
<style>
@media screen {
    .print-button {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 30px;
        background: #3498db;
        color: white;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 9999;
    }
    .print-button:hover {
        background: #2980b9;
    }
}
@media print {
    .print-button {
        display: none;
    }
}
</style>
<button class="print-button" onclick="printReport()">🖨️ 印刷 / PDF保存</button>
'''
            html_content = html_content.replace('</body>', f'{print_script}</body>')

            return HttpResponse(html_content, content_type='text/html; charset=utf-8')

        except Exception as e:
            import traceback
            traceback.print_exc()
            return HttpResponse(
                f'<html><body><h1>エラー</h1><p>{str(e)}</p></body></html>',
                content_type='text/html'
            )
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def generate_bulk_reports(self, request):
        """一括成績表帳票生成エンドポイント"""
        from .utils import generate_bulk_reports_template

        try:
            student_ids = request.data.get('studentIds', [])
            year = request.data.get('year')
            period = request.data.get('period')
            format_type = request.data.get('format', 'pdf')

            if not all([student_ids, year, period]):
                return Response({
                    'success': False,
                    'error': 'studentIds, year, periodは必須パラメータです'
                }, status=400)

            if not isinstance(student_ids, list) or len(student_ids) == 0:
                return Response({
                    'success': False,
                    'error': 'studentIdsは空でない配列である必要があります'
                }, status=400)

            result = generate_bulk_reports_template(
                student_ids=student_ids,
                year=year,
                period=period,
                format_type=format_type
            )

            return Response(result)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], authentication_classes=[], url_path='preview-bulk-reports')
    def preview_bulk_reports(self, request):
        """一括成績表HTML印刷プレビュー"""
        from .utils import get_individual_report_data
        from django.template.loader import render_to_string
        import os
        from django.conf import settings

        try:
            student_ids_str = request.query_params.get('studentIds', '')
            year = request.query_params.get('year')
            period = request.query_params.get('period')

            if not all([student_ids_str, year, period]):
                return HttpResponse(
                    '<html><body><h1>エラー</h1><p>studentIds, year, periodパラメータが必要です</p></body></html>',
                    content_type='text/html'
                )

            # カンマ区切りのstudent_idsを配列に変換
            student_ids = [s.strip() for s in student_ids_str.split(',') if s.strip()]

            if not student_ids:
                return HttpResponse(
                    '<html><body><h1>エラー</h1><p>有効な生徒IDが指定されていません</p></body></html>',
                    content_type='text/html'
                )

            # CSS読み込み
            css_path = os.path.join(settings.BASE_DIR, 'static', 'reports', 'report.css')
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
            except FileNotFoundError:
                css_content = ''

            # ロゴパス
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'reports', 'logo.svg')

            # 全生徒のHTMLを生成
            all_reports_html = []
            from datetime import datetime

            for student_id in student_ids:
                # 成績データを取得
                report_data = get_individual_report_data(student_id, year, period)
                if not report_data:
                    continue

                # テンプレートデータ準備
                template_data = {
                    'css_content': css_content,
                    'logo_url': f'file://{logo_path}',
                    'issue_date': datetime.now().strftime('%Y年%m月%d日'),
                    **report_data
                }

                # HTML生成
                html_content = render_to_string('reports/individual_report.html', template_data)
                all_reports_html.append(html_content)

            if not all_reports_html:
                return HttpResponse(
                    '<html><body><h1>エラー</h1><p>該当する成績データが見つかりません</p></body></html>',
                    content_type='text/html'
                )

            # 全てのレポートを結合（ページ区切り付き）
            combined_html = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>一括成績表 - 全国学力向上テスト</title>
    <style>
''' + css_content + '''
@media screen {
    .print-button {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 30px;
        background: #3498db;
        color: white;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 9999;
    }
    .print-button:hover {
        background: #2980b9;
    }
}
@media print {
    .print-button {
        display: none;
    }
    .report-page {
        page-break-after: always;
    }
    .report-page:last-child {
        page-break-after: auto;
    }
}
    </style>
</head>
<body>
'''

            for idx, report_html in enumerate(all_reports_html):
                # <html>, <head>, <body>タグを除去してコンテンツのみ抽出
                import re
                body_content = re.search(r'<body>(.*?)</body>', report_html, re.DOTALL)
                if body_content:
                    combined_html += body_content.group(1)

            combined_html += '''
<script>
// Ctrl+P または Cmd+P でも印刷可能
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        window.print();
    }
});
</script>
</body>
</html>
'''

            return HttpResponse(combined_html, content_type='text/html; charset=utf-8')

        except Exception as e:
            import traceback
            traceback.print_exc()
            return HttpResponse(
                f'<html><body><h1>エラー</h1><p>{str(e)}</p></body></html>',
                content_type='text/html'
            )
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def save_student_comments(self, request):
        """生徒コメント保存エンドポイント"""
        try:
            student_id = request.data.get('studentId')
            year = request.data.get('year')
            period = request.data.get('period')
            comments = request.data.get('comments', {})
            
            if not all([student_id, year, period]):
                return Response({
                    'success': False,
                    'error': 'studentId, year, periodは必須パラメータです'
                }, status=400)
            
            # TODO: 実際のコメント保存処理を実装
            # 現在はダミーレスポンスを返す
            
            return Response({
                'success': True,
                'message': 'コメントを保存しました'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

    @action(detail=False, methods=['post'], permission_classes=[])
    def get_score_based_comments(self, request):
        """点数に応じたコメントテンプレート取得エンドポイント"""
        try:
            student_id = request.data.get('studentId')
            year = request.data.get('year')
            period = request.data.get('period')
            
            if not all([student_id, year, period]):
                return Response({
                    'success': False,
                    'error': 'studentId, year, periodは必須パラメータです'
                }, status=400)
            
            from django.db.models import Q
            from students.models import Student
            
            # 生徒情報を取得
            try:
                student = Student.objects.get(student_id=student_id)
            except Student.DoesNotExist:
                return Response({
                    'success': False,
                    'error': '生徒が見つかりません'
                }, status=404)
            
            # 生徒の科目別得点を取得
            subject_scores = {}
            test_filter = Q(
                test__schedule__year=year,
                test__schedule__period=period,
                student=student,
                attendance=True
            )
            
            scores = Score.objects.filter(test_filter).values(
                'test__subject'
            ).annotate(
                total_score=models.Sum('score')
            )
            
            for score_data in scores:
                subject = score_data['test__subject']
                total_score = score_data['total_score']
                subject_scores[subject] = total_score
            
            # 各科目の点数に応じたコメントテンプレートを取得
            suggested_comments = {}
            
            for subject, score in subject_scores.items():
                # 生徒の塾のテンプレートを優先、なければデフォルトテンプレートを使用
                template = CommentTemplate.objects.filter(
                    Q(school=student.classroom.school if student.classroom else None) |
                    Q(is_default=True, school__isnull=True),
                    subject=subject,
                    score_range_min__lte=score,
                    score_range_max__gte=score,
                    is_active=True
                ).order_by('school').first()  # 塾固有のテンプレートを優先
                
                if template:
                    suggested_comments[subject] = {
                        'template_text': template.template_text,
                        'score_range': f'{template.score_range_min}-{template.score_range_max}点',
                        'current_score': score
                    }
                else:
                    # デフォルトコメント
                    suggested_comments[subject] = {
                        'template_text': f'{subject}の成績についてコメントを入力してください。',
                        'score_range': 'デフォルト',
                        'current_score': score
                    }
            
            return Response({
                'success': True,
                'subject_scores': subject_scores,
                'suggested_comments': suggested_comments
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)

# 管理画面用のCSVインポート機能
@staff_member_required
def import_csv_scores(request):
    """CSVから得点をインポートする管理者専用ビュー"""
    
    if request.method == 'POST':
        import csv
        import io
        from tests.models import TestDefinition, TestSchedule, QuestionGroup
        from students.models import Student
        from .models import Score
        
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'CSVファイルを選択してください。')
            return HttpResponseRedirect(request.path)
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'CSVファイルを選択してください。')
            return HttpResponseRedirect(request.path)
        
        try:
            # CSVファイルを読み込み
            file_data = csv_file.read()
            
            # BOMを削除
            if file_data.startswith(b'\xef\xbb\xbf'):
                file_data = file_data[3:]
            
            # CSVを解析
            csv_data = file_data.decode('utf-8')
            reader = csv.DictReader(io.StringIO(csv_data))
            
            success_count = 0
            error_count = 0
            warnings = []
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # 基本情報の取得
                    year = int(row.get('年度', 2025))
                    period = row.get('期間', 'summer')
                    student_id = row.get('生徒ID', '').strip()
                    student_name = row.get('生徒名', '').strip()
                    grade_raw = row.get('学年', '').strip()
                    attendance_str = row.get('出席', '出席').strip()
                    
                    if not student_id:
                        warnings.append(f"行{row_num}: 生徒IDが空です")
                        error_count += 1
                        continue
                    
                    # 出席状況の判定
                    attendance = attendance_str == '出席'
                    
                    # 学年の変換
                    grade_mapping = {
                        '小1': 'elementary_1', '小2': 'elementary_2', '小3': 'elementary_3',
                        '小4': 'elementary_4', '小5': 'elementary_5', '小6': 'elementary_6',
                        '中1': 'middle_1', '中2': 'middle_2', '中3': 'middle_3'
                    }
                    grade = grade_mapping.get(grade_raw, 'elementary_1')
                    
                    # 生徒の検索
                    try:
                        student = Student.objects.get(student_id=student_id)
                    except Student.DoesNotExist:
                        warnings.append(f"行{row_num}: 生徒ID {student_id} が見つかりません（{student_name}）")
                        error_count += 1
                        continue
                    
                    # テストスケジュールとテスト定義の取得
                    period_mapping = {'春期': 'spring', '夏期': 'summer', '冬期': 'winter'}
                    period_code = period_mapping.get(period, period)
                    
                    try:
                        test_schedule = TestSchedule.objects.get(year=year, period=period_code)
                    except TestSchedule.DoesNotExist:
                        warnings.append(f"行{row_num}: {year}年度{period}のテストスケジュールが見つかりません")
                        error_count += 1
                        continue
                    
                    # 国語と算数のテスト定義を取得
                    try:
                        japanese_test = TestDefinition.objects.get(
                            schedule=test_schedule,
                            grade_level=grade,
                            subject='japanese'
                        )
                        math_test = TestDefinition.objects.get(
                            schedule=test_schedule,
                            grade_level=grade,
                            subject='math'
                        )
                    except TestDefinition.DoesNotExist:
                        warnings.append(f"行{row_num}: {grade}のテスト定義が見つかりません")
                        error_count += 1
                        continue
                    
                    # 国語の得点処理（動的に大問数を検出）
                    japanese_questions = [key for key in row.keys() if key.startswith('国語_大問')]
                    for score_key in japanese_questions:
                        # 大問番号を抽出（例：国語_大問1 → 1）
                        try:
                            question_num = int(score_key.replace('国語_大問', ''))
                            # 大問番号の範囲チェック（1〜10）
                            if question_num < 1 or question_num > 10:
                                warnings.append(f"行{row_num}: 国語大問{question_num}は対応範囲外です（1〜10のみ対応）")
                                continue
                        except ValueError:
                            continue
                            
                        score_str = row.get(score_key, '').strip()
                        
                        # 空文字、'欠席'、'-'の場合はスキップ
                        if not score_str or score_str in ['欠席', '-', '×']:
                            continue
                            
                        if score_str.isdigit():
                            score = int(score_str)
                            
                            try:
                                question_group = QuestionGroup.objects.get(
                                    test=japanese_test,
                                    group_number=question_num
                                )
                                
                                Score.objects.update_or_create(
                                    student=student,
                                    test=japanese_test,
                                    question_group=question_group,
                                    defaults={
                                        'score': score,
                                        'attendance': attendance
                                    }
                                )
                            except QuestionGroup.DoesNotExist:
                                warnings.append(f"行{row_num}: 国語大問{question_num}の設定が見つかりません")
                    
                    # 算数の得点処理（動的に大問数を検出）
                    math_questions = [key for key in row.keys() if key.startswith('算数_大問')]
                    for score_key in math_questions:
                        # 大問番号を抽出（例：算数_大問1 → 1）
                        try:
                            question_num = int(score_key.replace('算数_大問', ''))
                            # 大問番号の範囲チェック（1〜10）
                            if question_num < 1 or question_num > 10:
                                warnings.append(f"行{row_num}: 算数大問{question_num}は対応範囲外です（1〜10のみ対応）")
                                continue
                        except ValueError:
                            continue
                            
                        score_str = row.get(score_key, '').strip()
                        
                        # 空文字、'欠席'、'-'の場合はスキップ
                        if not score_str or score_str in ['欠席', '-', '×']:
                            continue
                            
                        if score_str.isdigit():
                            score = int(score_str)
                            
                            try:
                                question_group = QuestionGroup.objects.get(
                                    test=math_test,
                                    group_number=question_num
                                )
                                
                                Score.objects.update_or_create(
                                    student=student,
                                    test=math_test,
                                    question_group=question_group,
                                    defaults={
                                        'score': score,
                                        'attendance': attendance
                                    }
                                )
                            except QuestionGroup.DoesNotExist:
                                warnings.append(f"行{row_num}: 算数大問{question_num}の設定が見つかりません")
                    
                    success_count += 1
                    
                except Exception as e:
                    warnings.append(f"行{row_num}: エラーが発生しました - {str(e)}")
                    error_count += 1
            
            # 結果表示
            if success_count > 0:
                messages.success(request, f"成功: {success_count}名の得点をインポートしました")
            
            if error_count > 0:
                messages.warning(request, f"エラー: {error_count}件の処理に失敗しました")
            
            # 警告メッセージを表示
            for warning in warnings[:5]:  # 最初の5件のみ表示
                messages.warning(request, warning)
            
            if len(warnings) > 5:
                messages.info(request, f"他に{len(warnings) - 5}件の警告があります")
            
            # 成功時は得点一覧に戻る
            if success_count > 0:
                return HttpResponseRedirect('/admin/scores/score/')
            
        except Exception as e:
            messages.error(request, f"CSVファイルの処理中にエラーが発生しました: {str(e)}")
    
    # CSV選択画面を表示
    return render(request, 'admin/scores/import_csv.html', {
        'title': 'CSV得点インポート',
        'subtitle': 'zyukupageテンプレート形式のCSVファイルから得点をインポートします',
        'has_permission': True,
    })


class StudentCommentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'test', 'comment_type', 'visibility']
    search_fields = ['title', 'content', 'student__name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return StudentComment.objects.all()

    @action(detail=False, methods=['post'])
    def auto_generate_comments(self, request):
        """自動コメント生成"""
        student_id = request.data.get('student_id')
        
        if not student_id:
            return Response(
                {'error': 'student_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from students.models import Student
            student = Student.objects.get(id=student_id)
            
            # 基本的な自動コメント生成ロジック
            # 最新のテスト結果を基にコメントを生成
            test_results = TestResult.objects.filter(student=student).order_by('-created_at')[:5]
            
            if not test_results.exists():
                return Response(
                    {'message': 'テスト結果が見つかりません'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 自動生成コメントの作成
            generated_comments = []
            
            for result in test_results:
                if result.total_score >= 80:
                    comment_type = 'strength'
                    title = f"{result.test.subject}の優秀な成績"
                    content = f"{result.test.subject}で{result.total_score}点の優秀な成績を収めました。この調子で頑張りましょう。"
                elif result.total_score >= 60:
                    comment_type = 'general'
                    title = f"{result.test.subject}の成績"
                    content = f"{result.test.subject}で{result.total_score}点でした。更なる向上を目指しましょう。"
                else:
                    comment_type = 'improvement'
                    title = f"{result.test.subject}の改善点"
                    content = f"{result.test.subject}で{result.total_score}点でした。復習を重点的に行い、次回の向上を目指しましょう。"
                
                comment, created = StudentComment.objects.get_or_create(
                    student=student,
                    test=result.test,
                    comment_type=comment_type,
                    defaults={
                        'title': title,
                        'content': content,
                        'visibility': 'parent_visible',
                        'is_auto_generated': True
                    }
                )
                
                if created:
                    generated_comments.append({
                        'id': comment.id,
                        'title': comment.title,
                        'content': comment.content,
                        'comment_type': comment.comment_type
                    })
            
            return Response({
                'message': f'{len(generated_comments)}件のコメントを自動生成しました',
                'generated_comments': generated_comments
            })
            
        except Student.DoesNotExist:
            return Response(
                {'error': '生徒が見つかりません'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'コメント生成中にエラーが発生しました: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TestCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'test', 'comment_type', 'subject']
    search_fields = ['content', 'student__name', 'test__name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return TestComment.objects.all()


class CommentTemplateV2ViewSet(viewsets.ModelViewSet):
    serializer_class = CommentTemplateV2Serializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['template_type', 'subject', 'grade_level', 'score_range', 'is_active']
    search_fields = ['title', 'content_template', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'priority']
    ordering = ['-priority', '-created_at']

    def get_queryset(self):
        return CommentTemplateV2.objects.filter(is_active=True)

    @action(detail=False, methods=['get'], url_path='subject-comments')
    def get_subject_comments(self, request):
        """教科別・点数範囲別のコメントテンプレートを取得"""
        subject = request.query_params.get('subject')

        if not subject:
            return Response(
                {'error': 'subject parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5つの点数範囲のテンプレートを取得
        score_ranges = ['0-20', '21-40', '41-60', '61-80', '81-100']
        templates = []

        for score_range in score_ranges:
            template = CommentTemplateV2.objects.filter(
                category=f"{subject}_{score_range}",
                is_active=True
            ).first()

            templates.append({
                'score_range': score_range,
                'template_id': template.id if template else None,
                'title': template.title if template else f'{subject} {score_range}点',
                'content': template.template_text if template else ''
            })

        return Response(templates)

    @action(detail=False, methods=['post'], url_path='update-subject-comment')
    def update_subject_comment(self, request):
        """教科別コメントテンプレートを更新"""
        subject = request.data.get('subject')
        score_range = request.data.get('score_range')
        content = request.data.get('content')

        if not all([subject, score_range, content]):
            return Response(
                {'error': 'subject, score_range, and content are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        category = f"{subject}_{score_range}"
        template, created = CommentTemplateV2.objects.update_or_create(
            category=category,
            defaults={
                'title': f'{subject} {score_range}点',
                'template_text': content,
                'applicable_scope': 'specific_subject',
                'subject_filter': subject,
                'is_active': True
            }
        )

        return Response({
            'success': True,
            'template_id': template.id,
            'created': created
        })