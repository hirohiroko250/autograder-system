from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
from .models import Classroom, ClassroomPermission, AttendanceRecord, BillingReport
from .serializers import ClassroomSerializer
from .utils import get_billing_student_count, get_classroom_attendance_summary
from schools.models import School
from students.models import Student, StudentEnrollment

User = get_user_model()

class ClassroomViewSet(viewsets.ModelViewSet):
    serializer_class = ClassroomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'school_admin':
            return Classroom.objects.filter(school__school_id=user.school_id)
        elif user.role == 'classroom_admin':
            return Classroom.objects.filter(classroom_id=user.classroom_id)
        return Classroom.objects.all()
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'count': queryset.count()
        })
    
    def create(self, request, *args, **kwargs):
        """教室を作成する"""
        user = request.user
        if user.role != 'school_admin':
            return Response(
                {'error': '教室の作成権限がありません'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        school = School.objects.filter(school_id=user.school_id).first()
        if not school:
            return Response(
                {'error': '所属する学校が見つかりません'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        classroom_data = request.data.copy()
        
        # 塾固有の教室IDを生成（school_id + 連番の形式）
        # school_idの下3桁 + 3桁の連番で6桁のclassroom_idを作成
        school_suffix = str(school.school_id)[-3:].zfill(3)  # 下3桁、0埋め
        
        # この塾の既存教室IDから連番部分を取得
        school_classrooms = Classroom.objects.filter(
            school=school,
            classroom_id__startswith=school_suffix,  # 塾の接頭辞で始まる
            classroom_id__regex=r'^\d{6}$'  # 6桁の数字のみ
        ).order_by('-classroom_id')
        
        if school_classrooms.exists():
            # 最後の教室IDから連番部分を取得して +1
            last_classroom = school_classrooms.first()
            last_sequence = int(last_classroom.classroom_id[-3:])  # 末尾3桁
            next_sequence = str(last_sequence + 1).zfill(3)
            next_id = f"{school_suffix}{next_sequence}"
        else:
            # この塾の最初の教室: school_suffix + "001"
            next_id = f"{school_suffix}001"
        
        classroom_data['classroom_id'] = next_id
        classroom_data['school'] = school.id
        
        serializer = self.get_serializer(data=classroom_data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    classroom = serializer.save(school=school)
                    
                    # 教室管理者アカウント作成（重複チェック）
                    # ログインIDは塾ID + 教室ID の形式（12桁）
                    login_id = f"{school.school_id}{classroom.classroom_id}"
                    if User.objects.filter(username=login_id).exists():
                        # 既存のユーザーがいる場合は削除して再作成
                        User.objects.filter(username=login_id).delete()
                    
                    classroom_user = User.objects.create_user(
                        username=login_id,
                        email=f"{login_id}@classroom.local",
                        password=classroom.classroom_id,
                        role='classroom_admin',
                        school_id=school.school_id,
                        classroom_id=classroom.classroom_id
                    )
                    
                    return Response({
                        'classroom': serializer.data,
                        'credentials': {
                            'login_id': login_id,
                            'classroom_id': classroom.classroom_id,
                            'password': classroom.classroom_id
                        }
                    }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {'error': f'教室作成エラー: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """教室を更新する（PUT）"""
        return self._update_classroom(request, partial=False)
    
    def partial_update(self, request, *args, **kwargs):
        """教室を部分更新する（PATCH）"""
        return self._update_classroom(request, partial=True)
    
    def _update_classroom(self, request, partial=False):
        """教室更新の共通処理"""
        user = request.user
        instance = self.get_object()
        
        # 権限チェック
        if user.role == 'school_admin':
            # 自分の学校の教室のみ更新可能
            if instance.school.school_id != user.school_id:
                return Response(
                    {'error': 'この教室の更新権限がありません'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': '教室の更新権限がありません'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 権限データを処理
        permissions_data = request.data.get('permissions', {})
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 教室の基本情報を更新
        classroom = serializer.save()
        
        # 権限データを更新
        if permissions_data:
            permission, created = ClassroomPermission.objects.get_or_create(
                classroom=classroom,
                defaults=permissions_data
            )
            if not created:
                for key, value in permissions_data.items():
                    setattr(permission, key, value)
                permission.save()
        
        # 更新後のデータを返す（権限情報も含む）
        updated_serializer = self.get_serializer(classroom)
        return Response(updated_serializer.data)
    
    @action(detail=True, methods=['get'])
    def attendance_count(self, request, pk=None):
        """教室の受講者数・課金対象者数を取得"""
        classroom = self.get_object()
        year = request.query_params.get('year', 2025)
        period = request.query_params.get('period', 'summer')
        
        try:
            year = int(year)
        except ValueError:
            return Response(
                {'error': '年度は数字で指定してください'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 課金対象の受講者数
        billing_count = get_billing_student_count(classroom, year, period)
        
        # 受講状況サマリー
        summary = get_classroom_attendance_summary(classroom, year, period)
        
        return Response({
            'classroom_id': classroom.classroom_id,
            'classroom_name': classroom.name,
            'year': year,
            'period': period,
            'billing_student_count': billing_count,
            'attendance_summary': summary,
        })
    
    @action(detail=False, methods=['get'])
    def billing_summary(self, request):
        """全教室の課金サマリーを取得"""
        user = request.user
        year = request.query_params.get('year', 2025)
        period = request.query_params.get('period', 'summer')
        
        try:
            year = int(year)
        except ValueError:
            return Response(
                {'error': '年度は数字で指定してください'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ユーザーの権限に応じて教室を取得
        classrooms = self.get_queryset()
        
        summary_data = []
        total_billing_count = 0
        
        for classroom in classrooms:
            billing_count = get_billing_student_count(classroom, year, period)
            attendance_summary = get_classroom_attendance_summary(classroom, year, period)
            
            summary_data.append({
                'classroom_id': classroom.classroom_id,
                'classroom_name': classroom.name,
                'membership_type': classroom.get_membership_type_display(),
                'billing_student_count': billing_count,
                'attendance_summary': attendance_summary,
            })
            
            total_billing_count += billing_count
        
        return Response({
            'year': year,
            'period': period,
            'total_billing_count': total_billing_count,
            'classrooms': summary_data,
        })
    
    @action(detail=False, methods=['get'])
    def billing_details(self, request):
        """請求詳細データ取得（出席かつ点数入力済み生徒のみ）"""
        user = request.user
        year = request.query_params.get('year')
        period = request.query_params.get('period')
        classroom_id = request.query_params.get('classroom_id')
        
        if not year or not period:
            return Response(
                {'error': '年度と期間を指定してください'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
        except ValueError:
            return Response(
                {'error': '年度は数字で指定してください'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ユーザーの権限に応じて教室を取得
        classrooms = self.get_queryset()
        if classroom_id:
            classrooms = classrooms.filter(classroom_id=classroom_id)
        
        billing_data = []
        total_amount = 0
        total_students = 0
        
        for classroom in classrooms:
            # 出席かつ点数入力済みの生徒を取得
            billing_records = AttendanceRecord.objects.filter(
                classroom=classroom,
                year=year,
                period=period,
                has_score_input=True  # 点数入力済み = 課金対象
            ).order_by('student_id', 'subject')
            
            # 生徒ごとにグループ化
            student_billing = {}
            for record in billing_records:
                if record.student_id not in student_billing:
                    student_billing[record.student_id] = {
                        'student_id': record.student_id,
                        'student_name': record.student_name,
                        'subjects': [],
                        'billing_amount': 0,
                        'score_input_dates': []
                    }
                
                student_billing[record.student_id]['subjects'].append({
                    'subject': record.subject,
                    'score_input_date': record.score_input_date.isoformat() if record.score_input_date else None,
                    'amount': record.get_billing_amount()
                })
                
                if record.score_input_date:
                    student_billing[record.student_id]['score_input_dates'].append(
                        record.score_input_date.isoformat()
                    )
            
            # 教室ごとの料金計算
            classroom_total = 0
            classroom_students = list(student_billing.values())
            
            for student_data in classroom_students:
                # 生徒単位の料金（1名あたり料金）
                student_amount = classroom.get_price_per_student()
                student_data['billing_amount'] = student_amount
                classroom_total += student_amount
            
            billing_data.append({
                'classroom_id': classroom.classroom_id,
                'classroom_name': classroom.name,
                'school_name': classroom.school.name,
                'membership_type': classroom.school.membership_type,
                'price_per_student': classroom.get_price_per_student(),
                'students': classroom_students,
                'student_count': len(classroom_students),
                'total_amount': classroom_total,
            })
            
            total_amount += classroom_total
            total_students += len(classroom_students)
        
        return Response({
            'year': year,
            'period': period,
            'summary': {
                'total_students': total_students,
                'total_amount': total_amount,
                'classroom_count': len(billing_data),
            },
            'classrooms': billing_data,
            'generated_at': timezone.now().isoformat(),
        })
    
    @action(detail=False, methods=['post'])
    def generate_billing_report(self, request):
        """請求レポート生成・保存"""
        user = request.user
        year = request.data.get('year')
        period = request.data.get('period')
        
        if not year or not period:
            return Response(
                {'error': '年度と期間を指定してください'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year = int(year)
        except ValueError:
            return Response(
                {'error': '年度は数字で指定してください'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ユーザーの権限に応じて教室を取得
        classrooms = self.get_queryset()
        
        created_reports = []
        
        for classroom in classrooms:
            # 既存のレポートがある場合は更新、なければ作成
            report, created = BillingReport.objects.get_or_create(
                classroom=classroom,
                year=year,
                period=period,
                defaults={
                    'price_per_student': classroom.get_price_per_student(),
                }
            )
            
            # 出席かつ点数入力済みの生徒を集計
            billing_records = AttendanceRecord.objects.filter(
                classroom=classroom,
                year=year,
                period=period,
                has_score_input=True
            )
            
            # 生徒数とデータを集計
            unique_students = billing_records.values('student_id', 'student_name').distinct()
            billed_student_count = unique_students.count()
            
            # 全受講生徒数（参考用）
            total_students = StudentEnrollment.objects.filter(
                student__classroom=classroom,
                year=year,
                period=period,
                is_active=True
            ).count()
            
            # 生徒詳細データを作成
            student_details = {}
            for student_data in unique_students:
                student_id = student_data['student_id']
                student_records = billing_records.filter(student_id=student_id)
                
                student_details[student_id] = {
                    'student_name': student_data['student_name'],
                    'subjects': list(student_records.values_list('subject', flat=True)),
                    'score_input_dates': [
                        record.score_input_date.isoformat() if record.score_input_date else None
                        for record in student_records
                    ],
                    'billing_amount': classroom.get_price_per_student(),
                }
            
            # レポートを更新
            report.total_students = total_students
            report.billed_students = billed_student_count
            report.price_per_student = classroom.get_price_per_student()
            report.total_amount = billed_student_count * classroom.get_price_per_student()
            report.student_details = student_details
            report.save()
            
            created_reports.append({
                'classroom_id': classroom.classroom_id,
                'classroom_name': classroom.name,
                'total_students': total_students,
                'billed_students': billed_student_count,
                'total_amount': report.total_amount,
                'created': created,
            })
        
        return Response({
            'message': '請求レポートを生成しました',
            'year': year,
            'period': period,
            'reports': created_reports,
        })
    
    @action(detail=False, methods=['get'])
    def billing_reports(self, request):
        """保存済み請求レポート一覧取得"""
        user = request.user
        year = request.query_params.get('year')
        period = request.query_params.get('period')
        
        # ユーザーの権限に応じて教室を取得
        classrooms = self.get_queryset()
        
        # レポートをフィルタリング
        reports_query = BillingReport.objects.filter(
            classroom__in=classrooms
        ).select_related('classroom', 'classroom__school')
        
        if year:
            try:
                reports_query = reports_query.filter(year=int(year))
            except ValueError:
                pass
        
        if period:
            reports_query = reports_query.filter(period=period)
        
        reports_data = []
        for report in reports_query.order_by('-generated_at'):
            reports_data.append({
                'id': report.id,
                'classroom_id': report.classroom.classroom_id,
                'classroom_name': report.classroom.name,
                'school_name': report.classroom.school.name,
                'year': report.year,
                'period': report.get_period_display(),
                'total_students': report.total_students,
                'billed_students': report.billed_students,
                'price_per_student': report.price_per_student,
                'total_amount': report.total_amount,
                'generated_at': report.generated_at.isoformat(),
                'updated_at': report.updated_at.isoformat(),
            })
        
        return Response({
            'reports': reports_data,
            'count': len(reports_data),
        })
