from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .models import Classroom, ClassroomPermission, AttendanceRecord, SchoolBillingReport
from .serializers import ClassroomSerializer
from .utils import (
    get_billing_student_count,
    get_classroom_attendance_summary,
    generate_school_billing_report,
)
from schools.models import School

User = get_user_model()

class ClassroomViewSet(viewsets.ModelViewSet):
    serializer_class = ClassroomSerializer
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _get_period_display(period):
        return {
            'spring': '春期',
            'summer': '夏期',
            'winter': '冬期',
        }.get(period, period)

    def get_queryset(self):
        user = self.request.user
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"DEBUG Classroom queryset: user={user.username}, role={user.role}, school_id={getattr(user, 'school_id', None)}, classroom_id={getattr(user, 'classroom_id', None)}")

        if user.role == 'school_admin':
            queryset = Classroom.objects.filter(school__school_id=user.school_id)
            logger.error(f"DEBUG School admin queryset count: {queryset.count()}")
            return queryset
        elif user.role == 'classroom_admin':
            queryset = Classroom.objects.filter(classroom_id=user.classroom_id)
            logger.error(f"DEBUG Classroom admin queryset count: {queryset.count()}")
            return queryset
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
        """塾単位の課金サマリーを取得"""
        year = request.query_params.get('year', timezone.now().year)
        period = request.query_params.get('period', 'summer')
        force_refresh = request.query_params.get('force') in {'1', 'true', 'True'}

        try:
            year = int(year)
        except ValueError:
            return Response(
                {'error': '年度は数字で指定してください'},
                status=status.HTTP_400_BAD_REQUEST
            )

        classrooms = self.get_queryset()
        school_ids = list(classrooms.values_list('school_id', flat=True).distinct())

        if not school_ids:
            return Response({
                'year': year,
                'period': period,
                'period_display': self._get_period_display(period),
                'total_schools': 0,
                'total_classrooms': 0,
                'total_billing_students': 0,
                'total_amount': 0,
                'schools': [],
            })

        schools = School.objects.filter(id__in=school_ids).order_by('school_id')

        summary_entries = []
        total_schools = 0
        total_classrooms = 0
        total_billing_students = 0
        total_amount = 0
        errors = []

        for school in schools:
            report = SchoolBillingReport.objects.filter(
                school=school,
                year=year,
                period=period,
            ).first()

            try:
                if force_refresh or not report:
                    generate_school_billing_report(
                        school=school,
                        year=year,
                        period=period,
                        force=True,
                    )
                    report = SchoolBillingReport.objects.filter(
                        school=school,
                        year=year,
                        period=period,
                    ).first()
            except Exception as exc:
                errors.append({
                    'school_id': school.school_id,
                    'school_name': school.name,
                    'error': str(exc),
                })
                continue

            if not report:
                continue

            total_schools += 1
            total_classrooms += report.total_classrooms
            total_billing_students += report.billed_students
            total_amount += report.total_amount

            summary_entries.append({
                'school_id': school.school_id,
                'school_name': school.name,
                'membership_type': school.get_membership_type_display(),
                'price_per_student': report.price_per_student,
                'total_classrooms': report.total_classrooms,
                'total_students': report.total_students,
                'billed_students': report.billed_students,
                'total_amount': report.total_amount,
                'average_per_classroom': report.get_average_per_classroom(),
                'classroom_details': report.classroom_details,
                'generated_at': report.generated_at.isoformat(),
                'updated_at': report.updated_at.isoformat(),
            })

        response_payload = {
            'year': year,
            'period': period,
            'period_display': self._get_period_display(period),
            'total_schools': total_schools,
            'total_classrooms': total_classrooms,
            'total_billing_students': total_billing_students,
            'total_amount': total_amount,
            'schools': summary_entries,
        }

        if errors:
            response_payload['errors'] = errors

        return Response(response_payload)
    
    @action(detail=False, methods=['get'])
    def billing_details(self, request):
        """塾別の請求詳細（生徒・教室内訳）を取得"""
        year = request.query_params.get('year')
        period = request.query_params.get('period')
        school_identifier = request.query_params.get('school_id')
        force_refresh = request.query_params.get('force') in {'1', 'true', 'True'}

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

        classrooms = self.get_queryset()
        accessible_school_ids = list(classrooms.values_list('school_id', flat=True).distinct())

        if not accessible_school_ids:
            return Response({
                'year': year,
                'period': period,
                'period_display': self._get_period_display(period),
                'summary': {
                    'total_schools': 0,
                    'total_classrooms': 0,
                    'total_students': 0,
                    'total_amount': 0,
                },
                'schools': [],
            })

        schools_qs = School.objects.filter(id__in=accessible_school_ids)
        if school_identifier:
            schools_qs = schools_qs.filter(school_id=school_identifier)

        schools = list(schools_qs.order_by('school_id'))

        if school_identifier and not schools:
            return Response(
                {'error': f'指定された塾ID {school_identifier} の課金情報が見つかりません'},
                status=status.HTTP_404_NOT_FOUND
            )

        detailed_entries = []
        total_classrooms = 0
        total_students = 0
        total_amount = 0
        errors = []
        latest_generated_at = None
        latest_updated_at = None

        for school in schools:
            report = SchoolBillingReport.objects.filter(
                school=school,
                year=year,
                period=period,
            ).first()

            try:
                if force_refresh or not report:
                    generate_school_billing_report(
                        school=school,
                        year=year,
                        period=period,
                        force=True,
                    )
                    report = SchoolBillingReport.objects.filter(
                        school=school,
                        year=year,
                        period=period,
                    ).first()
            except Exception as exc:
                errors.append({
                    'school_id': school.school_id,
                    'school_name': school.name,
                    'error': str(exc),
                })
                continue

            if not report:
                continue

            total_classrooms += report.total_classrooms
            total_students += report.billed_students
            total_amount += report.total_amount

            if latest_generated_at is None or report.generated_at > latest_generated_at:
                latest_generated_at = report.generated_at
            if latest_updated_at is None or report.updated_at > latest_updated_at:
                latest_updated_at = report.updated_at

            classroom_details = []
            for classroom_name, detail in (report.classroom_details or {}).items():
                detail_copy = dict(detail)
                detail_copy['classroom_name'] = classroom_name
                classroom_details.append(detail_copy)
            classroom_details.sort(key=lambda item: item.get('classroom_name', ''))

            students = []
            for student in (report.student_details or {}).values():
                student_copy = dict(student)
                student_copy['billing_amount'] = report.price_per_student
                students.append(student_copy)
            students.sort(key=lambda item: (item.get('classroom_name', ''), item.get('student_name', '')))

            detailed_entries.append({
                'school_id': school.school_id,
                'school_name': school.name,
                'membership_type': school.get_membership_type_display(),
                'price_per_student': report.price_per_student,
                'total_classrooms': report.total_classrooms,
                'total_students': report.total_students,
                'billed_students': report.billed_students,
                'total_amount': report.total_amount,
                'classroom_details': classroom_details,
                'students': students,
                'generated_at': report.generated_at.isoformat(),
                'updated_at': report.updated_at.isoformat(),
            })

        response_payload = {
            'year': year,
            'period': period,
            'period_display': self._get_period_display(period),
            'summary': {
                'total_schools': len(detailed_entries),
                'total_classrooms': total_classrooms,
                'total_students': total_students,
                'total_amount': total_amount,
            },
            'schools': detailed_entries,
        }

        if latest_generated_at:
            response_payload['generated_at'] = latest_generated_at.isoformat()
        if latest_updated_at:
            response_payload['updated_at'] = latest_updated_at.isoformat()
        if errors:
            response_payload['errors'] = errors

        return Response(response_payload)
    
    @action(detail=False, methods=['post'])
    def generate_billing_report(self, request):
        """塾別課金レポートを生成・保存"""
        year = request.data.get('year')
        period = request.data.get('period')
        school_ids_param = request.data.get('school_ids')
        force_param = request.data.get('force')

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

        force_refresh = False
        if isinstance(force_param, str):
            force_refresh = force_param.lower() in {'1', 'true', 'yes'}
        elif isinstance(force_param, bool):
            force_refresh = force_param

        classrooms = self.get_queryset()
        accessible_school_ids = list(classrooms.values_list('school_id', flat=True).distinct())

        if not accessible_school_ids:
            return Response(
                {'error': '課金レポートを生成できる塾がありません'},
                status=status.HTTP_400_BAD_REQUEST
            )

        schools_qs = School.objects.filter(id__in=accessible_school_ids)

        selected_school_codes = None
        if school_ids_param:
            if isinstance(school_ids_param, (list, tuple)):
                selected_school_codes = [str(code) for code in school_ids_param]
            elif isinstance(school_ids_param, str):
                selected_school_codes = [code.strip() for code in school_ids_param.split(',') if code.strip()]
            else:
                return Response(
                    {'error': 'school_ids はカンマ区切り文字列またはリストで指定してください'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if selected_school_codes:
            schools_qs = schools_qs.filter(school_id__in=selected_school_codes)

        schools = list(schools_qs.order_by('school_id'))

        if selected_school_codes and not schools:
            return Response(
                {'error': '指定された塾IDの課金レポートを生成できません'},
                status=status.HTTP_404_NOT_FOUND
            )

        results = []
        errors = []

        for school in schools:
            try:
                result = generate_school_billing_report(
                    school=school,
                    year=year,
                    period=period,
                    force=force_refresh,
                )
                report = SchoolBillingReport.objects.filter(
                    school=school,
                    year=year,
                    period=period,
                ).first()

                results.append({
                    'school_id': school.school_id,
                    'school_name': school.name,
                    'created': result.get('created', False),
                    'updated': result.get('updated', False),
                    'reason': result.get('reason'),
                    'billed_students': result.get('billed_students', report.billed_students if report else 0),
                    'total_amount': result.get('total_amount', report.total_amount if report else 0),
                    'price_per_student': report.price_per_student if report else school.get_price_per_student(),
                    'total_classrooms': report.total_classrooms if report else 0,
                    'generated_at': report.generated_at.isoformat() if report else None,
                    'updated_at': report.updated_at.isoformat() if report else None,
                })
            except Exception as exc:
                errors.append({
                    'school_id': school.school_id,
                    'school_name': school.name,
                    'error': str(exc),
                })

        response_payload = {
            'message': '塾別課金レポートを生成しました',
            'year': year,
            'period': period,
            'period_display': self._get_period_display(period),
            'results': results,
            'processed_schools': len(results),
        }

        if errors:
            response_payload['errors'] = errors

        return Response(response_payload)
    
    @action(detail=False, methods=['get'])
    def billing_reports(self, request):
        """保存済み塾別課金レポート一覧を取得"""
        year = request.query_params.get('year')
        period = request.query_params.get('period')
        school_identifier = request.query_params.get('school_id')

        classrooms = self.get_queryset()
        accessible_school_ids = list(classrooms.values_list('school_id', flat=True).distinct())

        if not accessible_school_ids:
            return Response({'reports': [], 'count': 0})

        reports_query = SchoolBillingReport.objects.filter(
            school__id__in=accessible_school_ids
        ).select_related('school')

        if year:
            try:
                reports_query = reports_query.filter(year=int(year))
            except ValueError:
                return Response(
                    {'error': '年度は数字で指定してください'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if period:
            reports_query = reports_query.filter(period=period)

        if school_identifier:
            reports_query = reports_query.filter(school__school_id=school_identifier)

        reports_data = []
        for report in reports_query.order_by('-generated_at'):
            reports_data.append({
                'school_id': report.school.school_id,
                'school_name': report.school.name,
                'year': report.year,
                'period': report.period,
                'period_display': self._get_period_display(report.period),
                'membership_type': report.school.get_membership_type_display(),
                'total_students': report.total_students,
                'billed_students': report.billed_students,
                'total_classrooms': report.total_classrooms,
                'price_per_student': report.price_per_student,
                'total_amount': report.total_amount,
                'generated_at': report.generated_at.isoformat(),
                'updated_at': report.updated_at.isoformat(),
            })

        return Response({
            'reports': reports_data,
            'count': len(reports_data),
        })
