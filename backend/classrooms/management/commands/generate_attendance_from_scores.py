from django.core.management.base import BaseCommand
from django.db import transaction
from classrooms.models import AttendanceRecord
from scores.models import Score
from tests.models import TestSchedule, TestDefinition
from collections import defaultdict
from django.utils import timezone


class Command(BaseCommand):
    help = '得点データ（Score）から出席記録（AttendanceRecord）を生成'

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
            '--force',
            action='store_true',
            help='既存の出席記録を上書きする'
        )

    def handle(self, *args, **options):
        year = options['year']
        period = options['period']
        force = options['force']
        
        period_display = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}[period]
        
        self.stdout.write(
            self.style.SUCCESS(f'出席記録生成開始: {year}年度 {period_display}')
        )
        
        # 対象テストを取得
        try:
            test_schedules = TestSchedule.objects.filter(year=year, period=period)
            test_definitions = TestDefinition.objects.filter(schedule__in=test_schedules)
            
            if not test_definitions.exists():
                self.stdout.write(
                    self.style.ERROR(f'{year}年度 {period_display} のテストが見つかりません')
                )
                return
                
            self.stdout.write(f'対象テスト数: {test_definitions.count()}')
            for test in test_definitions:
                self.stdout.write(f'  - {test}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'テスト取得エラー: {str(e)}')
            )
            return

        # 出席済み（attendance=True）の得点データを取得
        try:
            attended_scores = Score.objects.filter(
                test__in=test_definitions,
                attendance=True
            ).select_related(
                'student',
                'student__classroom',
                'test'
            )
            
            self.stdout.write(f'出席済み得点データ: {attended_scores.count()}件')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'得点データ取得エラー: {str(e)}')
            )
            return

        # 生徒・テスト・科目の組み合わせでグループ化
        attendance_records = {}
        processed_combinations = set()
        
        for score in attended_scores:
            # 生徒・テストの組み合わせをチェック（重複排除）
            combination_key = (score.student.student_id, score.test.id)
            if combination_key in processed_combinations:
                continue
            processed_combinations.add(combination_key)
            
            # AttendanceRecord用のキー
            record_key = (
                score.student.classroom.id,
                score.student.student_id,
                score.student.name,
                year,
                period,
                score.test.get_subject_display()
            )
            
            attendance_records[record_key] = {
                'classroom': score.student.classroom,
                'student_id': score.student.student_id,
                'student_name': score.student.name,
                'year': year,
                'period': period,
                'subject': score.test.get_subject_display(),
                'has_score_input': True,
                'score_input_date': timezone.now()
            }

        self.stdout.write(f'生成対象の出席記録: {len(attendance_records)}件')

        # 既存記録の確認と処理
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for record_key, record_data in attendance_records.items():
                classroom, student_id, student_name, year, period, subject = record_key
                
                try:
                    # 既存記録をチェック
                    existing_record = AttendanceRecord.objects.filter(
                        classroom=record_data['classroom'],
                        student_id=student_id,
                        year=year,
                        period=period,
                        subject=subject
                    ).first()
                    
                    if existing_record:
                        if force:
                            # 更新
                            existing_record.has_score_input = True
                            existing_record.score_input_date = record_data['score_input_date']
                            existing_record.save()
                            updated_count += 1
                        else:
                            skipped_count += 1
                    else:
                        # 新規作成
                        AttendanceRecord.objects.create(**record_data)
                        created_count += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'記録作成エラー ({student_name}): {str(e)}')
                    )

        # 結果表示
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== 処理完了 ===\n'
                f'新規作成: {created_count}件\n'
                f'更新: {updated_count}件\n'
                f'スキップ: {skipped_count}件'
            )
        )

        # 集計表示
        self.display_summary(year, period)

    def display_summary(self, year, period):
        """生成結果のサマリー表示"""
        period_display = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}[period]
        
        records = AttendanceRecord.objects.filter(
            year=year,
            period=period,
            has_score_input=True
        ).select_related('classroom', 'classroom__school')
        
        if not records.exists():
            self.stdout.write(
                self.style.WARNING('生成された出席記録がありません')
            )
            return

        # 塾ごとの集計
        school_summary = defaultdict(lambda: {
            'classrooms': set(),
            'students': set(),
            'subjects': set()
        })
        
        for record in records:
            school = record.classroom.school
            school_summary[school.name]['classrooms'].add(record.classroom.name)
            school_summary[school.name]['students'].add((record.student_id, record.student_name))
            school_summary[school.name]['subjects'].add(record.subject)

        self.stdout.write(
            self.style.SUCCESS(f'\n=== {year}年度 {period_display} 出席記録サマリー ===')
        )
        
        for school_name, data in school_summary.items():
            self.stdout.write(
                f'{school_name}: '
                f'{len(data["classrooms"])}教室 '
                f'{len(data["students"])}名 '
                f'{len(data["subjects"])}科目'
            )
            
            # 科目別詳細
            for subject in sorted(data["subjects"]):
                subject_count = records.filter(
                    classroom__school__name=school_name,
                    subject=subject
                ).count()
                self.stdout.write(f'  - {subject}: {subject_count}件')