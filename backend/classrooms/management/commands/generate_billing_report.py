from django.core.management.base import BaseCommand
from django.db import transaction
from classrooms.models import Classroom, BillingReport, AttendanceRecord
from datetime import datetime


class Command(BaseCommand):
    help = '指定期間の課金レポートを生成'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            required=True,
            help='対象年度を指定してください'
        )
        parser.add_argument(
            '--period',
            type=str,
            choices=['spring', 'summer', 'winter'],
            required=True,
            help='対象期間を指定してください (spring/summer/winter)'
        )
        parser.add_argument(
            '--classroom_id',
            type=str,
            help='特定の教室IDを指定（省略時は全教室）'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='既存のレポートを上書きする'
        )

    def handle(self, *args, **options):
        year = options['year']
        period = options['period']
        classroom_id = options.get('classroom_id')
        force = options['force']
        
        period_display = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}[period]
        
        self.stdout.write(
            self.style.SUCCESS(f'課金レポート生成開始: {year}年度 {period_display}')
        )
        
        # 対象教室を取得
        if classroom_id:
            classrooms = Classroom.objects.filter(
                classroom_id=classroom_id,
                is_active=True
            )
            if not classrooms.exists():
                self.stdout.write(
                    self.style.ERROR(f'教室ID {classroom_id} が見つかりません')
                )
                return
        else:
            classrooms = Classroom.objects.filter(is_active=True)
        
        total_classrooms = classrooms.count()
        processed = 0
        created = 0
        updated = 0
        errors = 0
        
        self.stdout.write(f'対象教室数: {total_classrooms}')
        
        with transaction.atomic():
            for classroom in classrooms:
                try:
                    result = self.generate_classroom_billing_report(
                        classroom, year, period, force
                    )
                    
                    if result['created']:
                        created += 1
                        self.stdout.write(
                            f'作成: {classroom.name} - {result["billed_students"]}名 {result["total_amount"]}円'
                        )
                    elif result['updated']:
                        updated += 1
                        self.stdout.write(
                            f'更新: {classroom.name} - {result["billed_students"]}名 {result["total_amount"]}円'
                        )
                    else:
                        self.stdout.write(
                            f'スキップ: {classroom.name} - {result.get("reason", "")}'
                        )
                    
                    processed += 1
                    
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'エラー: {classroom.name} - {str(e)}')
                    )
        
        # 結果サマリー
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== 処理完了 ===\n'
                f'処理済み教室: {processed}/{total_classrooms}\n'
                f'新規作成: {created}件\n'
                f'更新: {updated}件\n'
                f'エラー: {errors}件'
            )
        )
        
        # 全体サマリーの表示
        self.display_summary(year, period)

    def generate_classroom_billing_report(self, classroom, year, period, force):
        """教室の課金レポートを生成"""
        
        # 既存レポートをチェック
        existing_report = BillingReport.objects.filter(
            classroom=classroom,
            year=year,
            period=period
        ).first()
        
        if existing_report and not force:
            return {
                'created': False,
                'updated': False,
                'reason': '既存レポートあり（--force で上書き可能）'
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
                    record.score_input_date.strftime('%Y-%m-%d %H:%M')
                )
        
        # 集計データを作成
        total_students = len(student_details)  # 点数入力がない生徒も含む全体数
        billed_students = attendance_records.count()  # 課金対象（点数入力済み）
        price_per_student = classroom.school.get_price_per_student()  # 塾の会員種別から料金取得
        total_amount = billed_students * price_per_student
        
        # レポートデータを準備
        report_data = {
            'classroom': classroom,
            'year': year,
            'period': period,
            'total_students': total_students,
            'billed_students': billed_students,
            'price_per_student': price_per_student,
            'total_amount': total_amount,
            'student_details': student_details,
        }
        
        if existing_report:
            # 更新
            for key, value in report_data.items():
                if key != 'classroom':  # classroom は更新不要
                    setattr(existing_report, key, value)
            existing_report.save()
            
            return {
                'created': False,
                'updated': True,
                'billed_students': billed_students,
                'total_amount': total_amount
            }
        else:
            # 新規作成
            BillingReport.objects.create(**report_data)
            
            return {
                'created': True,
                'updated': False,
                'billed_students': billed_students,
                'total_amount': total_amount
            }

    def display_summary(self, year, period):
        """全体サマリーを表示"""
        period_display = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}[period]
        
        reports = BillingReport.objects.filter(year=year, period=period)
        
        if not reports.exists():
            self.stdout.write(
                self.style.WARNING('生成されたレポートがありません')
            )
            return
        
        # 会員種別ごとの集計
        membership_summary = {}
        total_amount = 0
        total_students = 0
        
        for report in reports.select_related('classroom', 'classroom__school'):
            membership_type = report.classroom.school.get_membership_type_display()
            
            if membership_type not in membership_summary:
                membership_summary[membership_type] = {
                    'classrooms': 0,
                    'students': 0,
                    'amount': 0,
                    'price': report.classroom.school.get_price_per_student()
                }
            
            membership_summary[membership_type]['classrooms'] += 1
            membership_summary[membership_type]['students'] += report.billed_students
            membership_summary[membership_type]['amount'] += report.total_amount
            
            total_amount += report.total_amount
            total_students += report.billed_students
        
        # サマリー表示
        self.stdout.write(
            self.style.SUCCESS(f'\n=== {year}年度 {period_display} 課金サマリー ===')
        )
        
        for membership_type, data in membership_summary.items():
            self.stdout.write(
                f'{membership_type}: {data["classrooms"]}教室 '
                f'{data["students"]}名 {data["amount"]:,}円 '
                f'({data["price"]}円/名)'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n合計: {reports.count()}教室 {total_students}名 {total_amount:,}円'
            )
        )