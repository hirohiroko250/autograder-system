from django.utils import timezone
from django.db import transaction
from .models import AttendanceRecord, MembershipType, SchoolBillingReport
import logging

logger = logging.getLogger(__name__)

def update_attendance_record(student, test_definition):
    """
    点数入力時に受講記録を更新する
    
    Args:
        student: Student model instance
        test_definition: TestDefinition model instance
    """
    from students.models import Student
    from tests.models import TestDefinition
    
    # 必要な情報を取得
    classroom = student.classroom
    
    # テスト定義から年度・期・教科を取得
    # テスト定義の構造に応じて調整が必要
    year = getattr(test_definition, 'year', 2025)
    period = getattr(test_definition, 'period', 'summer')
    subject = getattr(test_definition, 'subject', '算数')
    
    # 受講記録を作成または更新
    attendance_record, created = AttendanceRecord.objects.update_or_create(
        classroom=classroom,
        student_id=student.student_id,
        year=year,
        period=period,
        subject=subject,
        defaults={
            'student_name': student.name,
            'has_score_input': True,
            'score_input_date': timezone.now(),
        }
    )
    
    if created:
        print(f"新規受講記録を作成: {student.name} ({classroom.name})")
    else:
        print(f"受講記録を更新: {student.name} ({classroom.name})")
    
    return attendance_record


def get_billing_student_count(classroom, year, period):
    """
    課金対象の受講者数を取得する
    
    Args:
        classroom: Classroom model instance
        year: int (年度)
        period: str (期間: 'spring', 'summer', 'winter')
    
    Returns:
        int: 課金対象の受講者数（点数入力済みの生徒数）
    """
    return AttendanceRecord.objects.filter(
        classroom=classroom,
        year=year,
        period=period,
        has_score_input=True
    ).values('student_id').distinct().count()


def get_classroom_attendance_summary(classroom, year, period):
    """
    教室の受講状況サマリーを取得する
    
    Args:
        classroom: Classroom model instance  
        year: int (年度)
        period: str (期間)
    
    Returns:
        dict: 受講状況サマリー
    """
    records = AttendanceRecord.objects.filter(
        classroom=classroom,
        year=year,
        period=period
    )
    
    total_records = records.count()
    completed_records = records.filter(has_score_input=True).count()
    unique_students = records.values('student_id').distinct().count()
    billing_students = records.filter(has_score_input=True).values('student_id').distinct().count()
    
    return {
        'total_records': total_records,
        'completed_records': completed_records,
        'unique_students': unique_students,
        'billing_students': billing_students,
        'completion_rate': (completed_records / total_records * 100) if total_records > 0 else 0,
    }


def generate_classroom_billing_report(classroom, year, period, force=False):
    """
    指定された教室・年度・期間の課金レポートを生成

    Args:
        classroom: Classroomインスタンス
        year: 年度（整数）
        period: 期間（'spring', 'summer', 'winter'）
        force: 既存レポートを上書きするか（bool）

    Returns:
        dict: 生成結果（created, updated, reason, billed_students, total_amount）
    """

    # 既存レポートをチェック
    # BillingReport（教室ベース）は廃止されました
    existing_report = None

    if existing_report and not force:
        return {
            'created': False,
            'updated': False,
            'reason': '既存レポートあり',
            'billed_students': existing_report.billed_students,
            'total_amount': existing_report.total_amount
        }

    # 受講記録を取得（点数入力済みの生徒のみ）
    attendance_records = AttendanceRecord.objects.filter(
        classroom=classroom,
        year=year,
        period=period,
        has_score_input=True  # 点数入力済みのみが課金対象
    )

    # 生徒詳細を作成
    student_details = {}
    for record in attendance_records:
        student_key = f"{record.student_id}_{record.student_name}"
        if student_key not in student_details:
            student_details[student_key] = {
                'student_id': record.student_id,
                'student_name': record.student_name,
                'subjects': [],
                'score_input_dates': []
            }

        student_details[student_key]['subjects'].append(record.subject)
        if record.score_input_date:
            student_details[student_key]['score_input_dates'].append(
                record.score_input_date.strftime('%Y-%m-%d')
            )

    # 課金対象生徒数
    billed_students = len(student_details)

    # 料金計算
    # 教室の会員種別から単価を取得
    if hasattr(classroom, 'school') and hasattr(classroom.school, 'membership_type'):
        # membership_typeが文字列として保存されている場合
        membership_type_code = classroom.school.membership_type
        try:
            membership_type = MembershipType.objects.get(type_code=membership_type_code)
            price_per_student = membership_type.price_per_student
        except MembershipType.DoesNotExist:
            # フォールバック: 一般料金
            try:
                general_membership = MembershipType.objects.get(type_code='general')
                price_per_student = general_membership.price_per_student
            except MembershipType.DoesNotExist:
                price_per_student = 500  # デフォルト料金
    else:
        # フォールバック: 一般料金
        try:
            general_membership = MembershipType.objects.get(type_code='general')
            price_per_student = general_membership.price_per_student
        except MembershipType.DoesNotExist:
            price_per_student = 500  # デフォルト料金

    total_amount = billed_students * price_per_student

    # レポートデータを準備
    report_data = {
        'classroom': classroom,
        'year': year,
        'period': period,
        'total_students': attendance_records.values('student_id').distinct().count(),
        'billed_students': billed_students,
        'price_per_student': price_per_student,
        'total_amount': total_amount,
        'student_details': student_details,
    }

    with transaction.atomic():
        if existing_report:
            # 既存レポートを更新
            for key, value in report_data.items():
                if key != 'classroom':  # classroom は更新しない
                    setattr(existing_report, key, value)
            existing_report.save()

            return {
                'created': False,
                'updated': True,
                'reason': '既存レポートを更新',
                'billed_students': billed_students,
                'total_amount': total_amount
            }
        else:
            # 新規レポートを作成
            # BillingReport.objects.create(**report_data)  # 廃止

            return {
                'created': True,
                'updated': False,
                'reason': '新規レポート作成',
                'billed_students': billed_students,
                'total_amount': total_amount
            }


def get_billing_summary(year, period):
    """
    指定期間の課金サマリーを取得

    Args:
        year: 年度（整数）
        period: 期間（'spring', 'summer', 'winter'）

    Returns:
        dict: サマリー情報
    """
    # reports = BillingReport.objects.filter(year=year, period=period)  # 廃止
    reports = []

    if not reports:  # 空のリストをチェック
        return {
            'total_classrooms': 0,
            'total_students': 0,
            'total_amount': 0,
            'reports': []
        }

    total_classrooms = reports.count()
    total_students = sum(report.billed_students for report in reports)
    total_amount = sum(report.total_amount for report in reports)

    return {
        'total_classrooms': total_classrooms,
        'total_students': total_students,
        'total_amount': total_amount,
        'reports': reports
    }


def generate_school_billing_report(school, year, period, force=False):
    """
    指定された塾・年度・期間の課金レポートを生成

    Args:
        school: Schoolインスタンス
        year: 年度（整数）
        period: 期間（'spring', 'summer', 'winter'）
        force: 既存レポートを上書きするか（bool）

    Returns:
        dict: 生成結果（created, updated, reason, billed_students, total_amount）
    """

    # 既存レポートをチェック
    existing_report = SchoolBillingReport.objects.filter(
        school=school,
        year=year,
        period=period
    ).first()

    if existing_report and not force:
        return {
            'created': False,
            'updated': False,
            'reason': '既存レポートあり',
            'billed_students': existing_report.billed_students,
            'total_amount': existing_report.total_amount
        }

    # 塾の全教室を取得
    classrooms = school.classrooms.filter(is_active=True)

    # 塾全体の集計データを初期化
    total_classrooms = 0
    total_students = 0
    billed_students = 0
    classroom_details = {}
    all_student_details = {}

    # 各教室の受講記録を取得して集計
    for classroom in classrooms:
        attendance_records = AttendanceRecord.objects.filter(
            classroom=classroom,
            year=year,
            period=period,
            has_score_input=True
        )

        if attendance_records.exists():
            total_classrooms += 1

            # 教室ごとの生徒詳細を作成
            classroom_student_details = {}
            for record in attendance_records:
                student_key = f"{record.student_id}_{record.student_name}"
                if student_key not in classroom_student_details:
                    classroom_student_details[student_key] = {
                        'student_id': record.student_id,
                        'student_name': record.student_name,
                        'classroom_name': classroom.name,
                        'subjects': [],
                        'score_input_dates': []
                    }

                classroom_student_details[student_key]['subjects'].append(record.subject)
                if record.score_input_date:
                    classroom_student_details[student_key]['score_input_dates'].append(
                        record.score_input_date.strftime('%Y-%m-%d')
                    )

            # 教室別詳細を保存
            classroom_billed_students = len(classroom_student_details)
            classroom_details[classroom.name] = {
                'classroom_id': classroom.classroom_id,
                'billed_students': classroom_billed_students,
                'student_list': list(classroom_student_details.keys())
            }

            # 全体の集計に加算
            total_students += attendance_records.values('student_id').distinct().count()
            billed_students += classroom_billed_students
            all_student_details.update(classroom_student_details)

    # 料金計算（塾の会員種別を使用）
    if hasattr(school, 'membership_type'):
        membership_type_code = school.membership_type
        try:
            membership_type = MembershipType.objects.get(type_code=membership_type_code)
            price_per_student = membership_type.price_per_student
        except MembershipType.DoesNotExist:
            try:
                general_membership = MembershipType.objects.get(type_code='general')
                price_per_student = general_membership.price_per_student
            except MembershipType.DoesNotExist:
                price_per_student = 500
    else:
        try:
            general_membership = MembershipType.objects.get(type_code='general')
            price_per_student = general_membership.price_per_student
        except MembershipType.DoesNotExist:
            price_per_student = 500

    total_amount = billed_students * price_per_student

    # レポートデータを準備
    report_data = {
        'school': school,
        'year': year,
        'period': period,
        'total_classrooms': total_classrooms,
        'total_students': total_students,
        'billed_students': billed_students,
        'price_per_student': price_per_student,
        'total_amount': total_amount,
        'classroom_details': classroom_details,
        'student_details': all_student_details,
    }

    with transaction.atomic():
        if existing_report:
            # 既存レポートを更新
            for key, value in report_data.items():
                if key != 'school':
                    setattr(existing_report, key, value)
            existing_report.save()

            return {
                'created': False,
                'updated': True,
                'reason': '既存レポートを更新',
                'billed_students': billed_students,
                'total_amount': total_amount
            }
        else:
            # 新規レポートを作成
            SchoolBillingReport.objects.create(**report_data)

            return {
                'created': True,
                'updated': False,
                'reason': '新規レポート作成',
                'billed_students': billed_students,
                'total_amount': total_amount
            }


def get_school_billing_summary(year, period):
    """
    指定期間の塾ベース課金サマリーを取得

    Args:
        year: 年度（整数）
        period: 期間（'spring', 'summer', 'winter'）

    Returns:
        dict: サマリー情報
    """
    reports = SchoolBillingReport.objects.filter(year=year, period=period)

    if not reports.exists():
        return {
            'total_schools': 0,
            'total_classrooms': 0,
            'total_students': 0,
            'total_amount': 0,
            'reports': []
        }

    total_schools = reports.count()
    total_classrooms = sum(report.total_classrooms for report in reports)
    total_students = sum(report.billed_students for report in reports)
    total_amount = sum(report.total_amount for report in reports)

    return {
        'total_schools': total_schools,
        'total_classrooms': total_classrooms,
        'total_students': total_students,
        'total_amount': total_amount,
        'reports': reports
    }