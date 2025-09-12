from django.utils import timezone
from .models import AttendanceRecord

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