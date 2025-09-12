from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.http import HttpResponse
from django.db import IntegrityError, models
from .models import Student, StudentEnrollment
from .serializers import StudentSerializer, StudentImportSerializer, StudentEnrollmentSerializer
from schools.utils import import_students_from_excel, export_student_template
import tempfile
import os
import pandas as pd

class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['classroom', 'grade', 'is_active']
    search_fields = ['name', 'student_id']
    ordering_fields = ['student_id', 'name', 'created_at']
    ordering = ['student_id']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Student.objects.none()
        
        if user.role == 'school_admin':
            queryset = Student.objects.filter(classroom__school__school_id=user.school_id)
        elif user.role == 'classroom_admin':
            queryset = Student.objects.filter(classroom__classroom_id=user.classroom_id)
        
        # Add membership type filtering (via school)
        membership_type = self.request.query_params.get('membership_type')
        if membership_type and membership_type != 'all':
            queryset = queryset.filter(classroom__school__membership_type__type_code=membership_type)
        
        return queryset.select_related('classroom', 'classroom__school')
    
    def create(self, request, *args, **kwargs):
        """生徒の新規作成"""
        try:
            user = request.user
            data = request.data.copy()
            
            # 教室管理者の場合、教室を自動設定
            if user.role == 'classroom_admin':
                from classrooms.models import Classroom
                classroom = Classroom.objects.filter(classroom_id=user.classroom_id).first()
                if not classroom:
                    return Response(
                        {'error': '教室が見つかりません'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                data['classroom'] = classroom.id
            
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                student = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except IntegrityError as e:
            return Response(
                {'error': 'この生徒IDは既に存在します'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'作成エラー: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """生徒情報の更新"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            
            if serializer.is_valid():
                self.perform_update(serializer)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except IntegrityError as e:
            return Response(
                {'error': 'データベース制約エラー: 既に存在する生徒IDまたは教室との組み合わせです'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'更新エラー: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def next_id(self, request):
        classroom_id = request.query_params.get('classroom')
        if not classroom_id:
            return Response(
                {'error': 'classroom パラメータが必要です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        last_student = Student.objects.filter(
            classroom__classroom_id=classroom_id
        ).order_by('-student_id').first()
        
        if last_student:
            next_id = str(int(last_student.student_id) + 1).zfill(6)
        else:
            next_id = '000001'
        
        return Response({'next_id': next_id})
    
    @action(detail=False, methods=['post'])
    def import_students(self, request):
        serializer = StudentImportSerializer(data=request.data)
        if serializer.is_valid():
            # 現在は簡単なレスポンスのみ
            return Response({
                'message': 'インポート機能は実装予定です',
                'filename': serializer.validated_data['file'].name
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def import_excel(self, request):
        """CSVファイルから生徒を一括インポート（新形式：塾情報・教室情報・受講履歴を含む）"""
        if 'file' not in request.FILES:
            return Response({'error': 'ファイルが必要です。'}, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            for chunk in file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            # CSVファイルを読み込み（BOM対応）
            try:
                df = pd.read_csv(tmp_file_path, encoding='utf-8-sig')  # BOM付きUTF-8
            except:
                try:
                    df = pd.read_csv(tmp_file_path, encoding='utf-8')  # 通常のUTF-8
                except:
                    df = pd.read_csv(tmp_file_path, encoding='shift_jis')  # Shift_JIS
            
            # 列名を正規化（空白文字除去）
            df.columns = df.columns.str.strip()
            
            # 列名の確認
            expected_columns = ['塾ID', '塾名', '教室ID', '教室名', '生徒ID', '生徒名', '学年', '年度', '期間']
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                return Response(
                    {'error': f'必要な列が不足しています: {", ".join(missing_columns)}\n実際の列: {list(df.columns)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 空行を除去
            df = df.dropna(how='all')
            
            # データ型を文字列に統一し、数値フィールドの小数点を除去
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # 数値IDフィールドの小数点を除去（例: "999004.0" -> "999004"）
                if col in ['塾ID', '教室ID', '生徒ID']:
                    df[col] = df[col].str.replace('.0', '', regex=False)
                    # ExcelエラーやNaN値をクリーンアップ
                    df[col] = df[col].replace(['nan', '#N/A', '#REF!', '#VALUE!', '#DIV/0!', '#NAME?', '#NULL!', '#NUM!'], '')
            
            # 権限チェック - ユーザーがアクセス可能な塾/教室のみ許可
            user = request.user
            created_students = 0
            created_enrollments = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # 空行をスキップ
                    if pd.isna(row['生徒ID']) or str(row['生徒ID']).strip() == '' or str(row['生徒ID']).strip() == 'nan':
                        continue
                    
                    # 必須フィールドの検証
                    if str(row['塾ID']).strip() == '' or str(row['塾ID']).strip() == 'nan':
                        errors.append(f'行 {index + 2}: 塾IDが空です')
                        continue
                    
                    if str(row['教室ID']).strip() == '' or str(row['教室ID']).strip() == 'nan':
                        errors.append(f'行 {index + 2}: 教室IDが空です (塾ID: {row["塾ID"]})')
                        continue
                    # 権限チェック
                    if user.role == 'school_admin':
                        if str(row['塾ID']).strip() != str(user.school_id).strip():
                            errors.append(f'行 {index + 2}: 権限のない塾ID ({row["塾ID"]}) です')
                            continue
                    elif user.role == 'classroom_admin':
                        if str(row['教室ID']).strip() != str(user.classroom_id).strip():
                            errors.append(f'行 {index + 2}: 権限のない教室ID ({row["教室ID"]}) です')
                            continue
                    
                    # 教室を取得
                    from classrooms.models import Classroom
                    classroom = Classroom.objects.filter(
                        classroom_id=row['教室ID'],
                        school__school_id=row['塾ID']
                    ).first()
                    
                    if not classroom:
                        errors.append(f'行 {index + 2}: 教室が見つかりません (塾ID: {row["塾ID"]}, 教室ID: {row["教室ID"]})')
                        continue
                    
                    # 塾名・教室名の整合性チェック（空でない場合のみ）
                    if (str(row['塾名']).strip() not in ['', 'nan'] and 
                        str(row['塾名']).strip() != classroom.school.name):
                        errors.append(f'行 {index + 2}: 塾名が一致しません (CSV: "{row["塾名"]}", 実際: "{classroom.school.name}")')
                        continue
                        
                    if (str(row['教室名']).strip() not in ['', 'nan'] and 
                        str(row['教室名']).strip() != classroom.name):
                        errors.append(f'行 {index + 2}: 教室名が一致しません (CSV: "{row["教室名"]}", 実際: "{classroom.name}")')
                        continue
                    
                    # 学年フォーマットを数値に変換
                    grade_value = self._parse_grade_format(row['学年'])
                    
                    # デバッグ: 学年変換の確認
                    if index < 5:  # 最初の5件だけログ出力
                        print(f"学年変換 - 元: '{row['学年']}' → 変換後: '{grade_value}'")
                    
                    # 生徒を取得または作成
                    student, student_created = Student.objects.get_or_create(
                        student_id=row['生徒ID'],
                        classroom=classroom,
                        defaults={
                            'name': row['生徒名'],
                            'grade': grade_value,
                            'is_active': True
                        }
                    )
                    
                    if student_created:
                        created_students += 1
                    else:
                        # 既存の生徒の場合、名前と学年を更新
                        student.name = row['生徒名']
                        student.grade = grade_value
                        student.save()
                    
                    # 受講履歴を作成（年度・期間が指定されている場合）
                    year_str = str(row['年度']).strip()
                    period_str = str(row['期間']).strip()
                    
                    if (year_str not in ['', 'nan'] and period_str not in ['', 'nan']):
                        try:
                            # 期間の変換
                            period_mapping = {
                                '春期': 'spring',
                                '夏期': 'summer',
                                '冬期': 'winter'
                            }
                            period = period_mapping.get(period_str, period_str)
                            
                            enrollment, enrollment_created = StudentEnrollment.objects.get_or_create(
                                student=student,
                                year=int(year_str),
                                period=period,
                                defaults={
                                    'is_active': True
                                }
                            )
                            
                            if enrollment_created:
                                created_enrollments += 1
                        except ValueError:
                            errors.append(f'行 {index + 2}: 年度が数値ではありません ({year_str})')
                            continue
                
                except Exception as e:
                    errors.append(f'行 {index + 2}: {str(e)}')
            
            result = {
                'message': 'インポートが完了しました',
                'created_students': created_students,
                'created_enrollments': created_enrollments,
                'total_rows': len(df),
                'error_count': len(errors)
            }
            
            if errors:
                result['errors'] = errors[:10]  # 最初の10件のエラーのみ表示
                if len(errors) > 10:
                    result['errors'].append(f'... 他 {len(errors) - 10} 件のエラー')
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': f'インポートエラー: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # 一時ファイルを削除
            os.unlink(tmp_file_path)
    
    def _parse_grade_format(self, grade_display):
        """学年表示形式（小6、中1など）を数値に変換"""
        if not grade_display or pd.isna(grade_display):
            return ''
        
        grade_str = str(grade_display).strip()
        
        # 小学生の場合
        if grade_str.startswith('小'):
            return grade_str.replace('小', '')
        # 中学生の場合
        elif grade_str.startswith('中'):
            middle_grade = int(grade_str.replace('中', ''))
            return str(middle_grade + 6)
        # 数字のみの場合はそのまま
        elif grade_str.isdigit():
            return grade_str
        else:
            return grade_str
    
    def _format_grade_for_display(self, grade):
        """数値学年を表示形式（小6、中1など）に変換"""
        if not grade:
            return ''
        
        try:
            grade_num = int(grade)
            if 1 <= grade_num <= 6:
                return f'小{grade_num}'
            elif 7 <= grade_num <= 9:
                return f'中{grade_num - 6}'
            else:
                return str(grade)
        except (ValueError, TypeError):
            return str(grade)
    
    @action(detail=False, methods=['get'])
    def export_template(self, request):
        """生徒登録用テンプレートをダウンロード（CSV形式）"""
        # 新形式のテンプレートデータを作成
        template_data = [
            {
                '塾ID': '100001',
                '塾名': 'サンプル学習塾',
                '教室ID': '001001', 
                '教室名': 'メイン教室',
                '生徒ID': '123456',
                '生徒名': '田中太郎',
                '学年': '小6',
                '年度': '2025',
                '期間': '夏期'
            },
            {
                '塾ID': '100001',
                '塾名': 'サンプル学習塾',
                '教室ID': '001001',
                '教室名': 'メイン教室', 
                '生徒ID': '123456',
                '生徒名': '田中太郎',
                '学年': '小6',
                '年度': '2025',
                '期間': '冬期'
            },
            {
                '塾ID': '100001',
                '塾名': 'サンプル学習塾',
                '教室ID': '001001',
                '教室名': 'メイン教室',
                '生徒ID': '123457', 
                '生徒名': '佐藤花子',
                '学年': '小5',
                '年度': '2025',
                '期間': '夏期'
            },
            {
                '塾ID': '100001',
                '塾名': 'サンプル学習塾',
                '教室ID': '001001',
                '教室名': 'メイン教室',
                '生徒ID': '123458', 
                '生徒名': '高橋次郎',
                '学年': '中1',
                '年度': '2025',
                '期間': '夏期'
            },
            # 空行を追加
            {col: '' for col in ['塾ID', '塾名', '教室ID', '教室名', '生徒ID', '生徒名', '学年', '年度', '期間']},
            {col: '' for col in ['塾ID', '塾名', '教室ID', '教室名', '生徒ID', '生徒名', '学年', '年度', '期間']},
        ]
        
        df = pd.DataFrame(template_data)
        
        # CSVファイルを生成（BOM付きUTF-8）
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8-sig') as tmp_file:
            df.to_csv(tmp_file, index=False)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='text/csv; charset=utf-8-sig'
                )
                response['Content-Disposition'] = 'attachment; filename="student_import_template.csv"'
                return response
        finally:
            os.unlink(tmp_file_path)
    
    @action(detail=False, methods=['get'])
    def export_data(self, request):
        """生徒データをExcelファイルでエクスポート（新形式：受講履歴を含む）"""
        students = self.get_queryset().select_related('classroom__school').prefetch_related('enrollments')
        
        # データをDataFrameに変換（受講履歴ごとに行を作成）
        data = []
        for student in students:
            enrollments = student.enrollments.all()
            
            if not enrollments:
                # 受講履歴がない場合でも基本情報は出力
                data.append({
                    '塾ID': student.classroom.school.school_id,
                    '塾名': student.classroom.school.name,
                    '教室ID': student.classroom.classroom_id,
                    '教室名': student.classroom.name,
                    '生徒ID': student.student_id,
                    '生徒名': student.name,
                    '学年': self._format_grade_for_display(student.grade),
                    '年度': '',
                    '期間': '',
                })
            else:
                # 各受講履歴ごとに行を作成
                for enrollment in enrollments:
                    period_display = {
                        'spring': '春期',
                        'summer': '夏期', 
                        'winter': '冬期'
                    }.get(enrollment.period, enrollment.period)
                    
                    data.append({
                        '塾ID': student.classroom.school.school_id,
                        '塾名': student.classroom.school.name,
                        '教室ID': student.classroom.classroom_id,
                        '教室名': student.classroom.name,
                        '生徒ID': student.student_id,
                        '生徒名': student.name,
                        '学年': self._format_grade_for_display(student.grade),
                        '年度': enrollment.year,
                        '期間': period_display,
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
                response['Content-Disposition'] = 'attachment; filename="students_data.xlsx"'
                return response
        finally:
            os.unlink(tmp_file_path)
    
    @action(detail=False, methods=['get'])
    def export_data_csv(self, request):
        """生徒データをCSVファイルでエクスポート（新形式：受講履歴を含む）"""
        students = self.get_queryset().select_related('classroom__school').prefetch_related('enrollments')
        
        # データをDataFrameに変換（受講履歴ごとに行を作成）
        data = []
        for student in students:
            enrollments = student.enrollments.all()
            
            if not enrollments:
                # 受講履歴がない場合でも基本情報は出力
                data.append({
                    '塾ID': student.classroom.school.school_id,
                    '塾名': student.classroom.school.name,
                    '教室ID': student.classroom.classroom_id,
                    '教室名': student.classroom.name,
                    '生徒ID': student.student_id,
                    '生徒名': student.name,
                    '学年': self._format_grade_for_display(student.grade),
                    '年度': '',
                    '期間': '',
                })
            else:
                # 各受講履歴ごとに行を作成
                for enrollment in enrollments:
                    period_display = {
                        'spring': '春期',
                        'summer': '夏期', 
                        'winter': '冬期'
                    }.get(enrollment.period, enrollment.period)
                    
                    data.append({
                        '塾ID': student.classroom.school.school_id,
                        '塾名': student.classroom.school.name,
                        '教室ID': student.classroom.classroom_id,
                        '教室名': student.classroom.name,
                        '生徒ID': student.student_id,
                        '生徒名': student.name,
                        '学年': self._format_grade_for_display(student.grade),
                        '年度': enrollment.year,
                        '期間': period_display,
                    })
        
        df = pd.DataFrame(data)
        
        # CSVファイルを生成（BOM付きUTF-8）
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', encoding='utf-8-sig') as tmp_file:
            df.to_csv(tmp_file, index=False)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='text/csv; charset=utf-8-sig'
                )
                response['Content-Disposition'] = 'attachment; filename="students_data.csv"'
                return response
        finally:
            os.unlink(tmp_file_path)
    
    @action(detail=False, methods=['get'])
    def by_enrollment(self, request):
        """受講情報で生徒を絞り込み"""
        year = request.query_params.get('year')
        period = request.query_params.get('period')
        
        if not year or not period:
            return Response(
                {'error': 'year と period パラメータが必要です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollments = StudentEnrollment.objects.filter(
            year=year,
            period=period,
            is_active=True
        ).select_related('student')
        
        students = [enrollment.student for enrollment in enrollments]
        serializer = self.get_serializer(students, many=True)
        
        return Response({
            'results': serializer.data,
            'count': len(students)
        })
    
    @action(detail=False, methods=['get'])
    def export_test_participants(self, request):
        """テスト受講生徒一覧をExcelファイルでエクスポート"""
        year = request.query_params.get('year')
        period = request.query_params.get('period')
        
        if not year or not period:
            return Response(
                {'error': 'year と period パラメータが必要です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 指定された年度・期間の受講生徒を取得
            enrollments = StudentEnrollment.objects.filter(
                year=year,
                period=period,
                is_active=True
            ).select_related(
                'student',
                'student__classroom',
                'student__classroom__school'
            ).order_by(
                'student__classroom__school__school_id',
                'student__classroom__classroom_id',
                'student__student_id'
            )
            
            # 権限チェック（ユーザーがアクセス可能な生徒のみ）
            user = request.user
            if user.role == 'school_admin':
                enrollments = enrollments.filter(
                    student__classroom__school__school_id=user.school_id
                )
            elif user.role == 'classroom_admin':
                enrollments = enrollments.filter(
                    student__classroom__classroom_id=user.classroom_id
                )
            
            # データをExcel用に整理
            data = []
            for enrollment in enrollments:
                student = enrollment.student
                classroom = student.classroom
                school = classroom.school
                
                data.append({
                    '塾ID': school.school_id,
                    '塾名': school.name,
                    '教室名': classroom.name,
                    '生徒ID': student.student_id,
                    '生徒名': student.name,
                    '学年': student.grade,
                    '年度': enrollment.year,
                    '期間': enrollment.get_period_display(),
                    '受講開始日': enrollment.enrolled_at.strftime('%Y-%m-%d'),
                    'アクティブ': '有効' if student.is_active else '無効'
                })
            
            if not data:
                return Response(
                    {'message': '指定された条件の受講生徒が見つかりません'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # DataFrameを作成してExcelファイルを生成
            df = pd.DataFrame(data)
            
            # Excelファイルを生成
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                # Excelライターを使用してフォーマットを設定
                with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='テスト受講生徒一覧', index=False)
                    
                    # ワークシートを取得
                    worksheet = writer.sheets['テスト受講生徒一覧']
                    
                    # 列幅を自動調整
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 30)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                    
                    # ヘッダー行のスタイルを設定
                    from openpyxl.styles import Font, PatternFill
                    header_font = Font(bold=True)
                    header_fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')
                    
                    for cell in worksheet[1]:
                        cell.font = header_font
                        cell.fill = header_fill
                
                tmp_file_path = tmp_file.name
            
            try:
                with open(tmp_file_path, 'rb') as f:
                    response = HttpResponse(
                        f.read(),
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    filename = f'test_participants_{year}_{period}.xlsx'
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    return response
            finally:
                os.unlink(tmp_file_path)
                
        except Exception as e:
            return Response(
                {'error': f'エクスポートエラー: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentEnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student', 'year', 'period', 'is_active']
    search_fields = ['student__name', 'student__student_id']
    ordering_fields = ['year', 'period', 'enrolled_at']
    ordering = ['-year', '-period']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'school_admin':
            return StudentEnrollment.objects.filter(
                student__classroom__school__school_id=user.school_id
            ).select_related('student', 'student__classroom')
        elif user.role == 'classroom_admin':
            return StudentEnrollment.objects.filter(
                student__classroom__classroom_id=user.classroom_id
            ).select_related('student', 'student__classroom')
        return StudentEnrollment.objects.none()
    
    def create(self, request, *args, **kwargs):
        """受講情報の新規作成"""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                enrollment = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except IntegrityError as e:
            return Response(
                {'error': '同じ生徒、年度、期間の組み合わせは既に存在します'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'作成エラー: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """特定の生徒の受講履歴を取得"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id パラメータが必要です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollments = self.get_queryset().filter(student_id=student_id)
        serializer = self.get_serializer(enrollments, many=True)
        
        return Response({
            'results': serializer.data,
            'count': len(enrollments)
        })
    
    @action(detail=False, methods=['get'])
    def for_score_entry(self, request):
        """スコア入力用：年度・期間・学年に基づく生徒一覧を取得"""
        year = request.query_params.get('year')
        period = request.query_params.get('period')
        grade = request.query_params.get('grade')  # elementary_1, elementary_2, middle_1 etc.
        
        if not all([year, period]):
            return Response(
                {'error': 'year, period パラメータが必要です'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
            
            # StudentEnrollmentから該当期間の生徒を取得（学校・教室・生徒IDでソート）
            enrollments = StudentEnrollment.objects.filter(
                year=year,
                period=period,
                is_active=True
            ).select_related('student', 'student__classroom', 'student__classroom__school').order_by(
                'student__classroom__school__school_id',
                'student__classroom__classroom_id', 
                'student__student_id'
            )
            
            # 権限チェック
            user = request.user
            if user.role == 'school_admin':
                enrollments = enrollments.filter(student__classroom__school__school_id=user.school_id)
            elif user.role == 'classroom_admin':
                enrollments = enrollments.filter(student__classroom__classroom_id=user.classroom_id)
            
            # 学年フィルタ
            if grade:
                # フロントエンドの学年形式をデータベース形式に変換
                if grade.startswith('elementary_'):
                    grade_num = grade.replace('elementary_', '')
                    # データベースには数値形式と日本語形式の両方があるため、両方で検索
                    enrollments = enrollments.filter(
                        models.Q(student__grade=grade_num) |
                        models.Q(student__grade=f'小{grade_num}')
                    )
                elif grade.startswith('middle_'):
                    grade_num = int(grade.replace('middle_', ''))
                    middle_grade_db = str(grade_num + 6)  # 中1=7, 中2=8, 中3=9
                    enrollments = enrollments.filter(
                        models.Q(student__grade=middle_grade_db) |
                        models.Q(student__grade=f'中{grade_num}')
                    )
                else:
                    enrollments = enrollments.filter(student__grade=grade)
            
            # レスポンス用データを構築
            students_data = []
            for enrollment in enrollments:
                student = enrollment.student
                
                # 学年を表示用に変換
                if student.grade.startswith('小'):
                    grade_num = student.grade.replace('小', '')
                    grade_display = f'elementary_{grade_num}'
                    grade_label = f'小学{grade_num}年生'
                elif student.grade.startswith('中'):
                    grade_num = student.grade.replace('中', '')
                    grade_display = f'middle_{grade_num}'
                    grade_label = f'中学{grade_num}年生'
                else:
                    grade_display = student.grade
                    grade_label = student.grade
                
                students_data.append({
                    'id': str(student.student_id),
                    'student_id': student.student_id,
                    'name': student.name,
                    'grade': grade_display,  # フロントエンド用の形式
                    'grade_label': grade_label,
                    'classroom': student.classroom.name,
                    'classroom_id': student.classroom.classroom_id,
                    'school_name': student.classroom.school.name,
                    'school_id': student.classroom.school.school_id,
                    'is_active': student.is_active,
                    'created_at': student.created_at.isoformat() if student.created_at else '',
                    'updated_at': student.updated_at.isoformat() if student.updated_at else ''
                })
            
            return Response({
                'results': students_data,
                'count': len(students_data)
            })
            
        except ValueError:
            return Response(
                {'error': 'year は数値である必要があります'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'データ取得エラー: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )