from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from scores.models import TestResult
from tests.models import TestDefinition, TestSchedule
from scores.utils import calculate_test_results
from datetime import datetime


class Command(BaseCommand):
    help = 'テスト結果の順位を確定させる'

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
            '--subject',
            type=str,
            choices=['japanese', 'math', 'english', 'mathematics'],
            help='対象科目を指定（省略時は全科目）'
        )
        parser.add_argument(
            '--test_id',
            type=int,
            help='特定のテストIDを指定'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='締切前でも強制的に確定する'
        )
        parser.add_argument(
            '--recalculate',
            action='store_true',
            help='順位を再計算してから確定する'
        )

    def handle(self, *args, **options):
        year = options['year']
        period = options['period']
        subject = options.get('subject')
        test_id = options.get('test_id')
        force = options['force']
        recalculate = options['recalculate']
        
        period_display = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}[period]
        
        self.stdout.write(
            self.style.SUCCESS(f'順位確定処理開始: {year}年度 {period_display}')
        )
        
        # 対象テストを取得
        if test_id:
            tests = TestDefinition.objects.filter(id=test_id)
        else:
            query = TestDefinition.objects.filter(
                schedule__year=year,
                schedule__period=period,
                is_active=True
            )
            if subject:
                query = query.filter(subject=subject)
            tests = query
        
        if not tests.exists():
            self.stdout.write(
                self.style.ERROR('対象のテストが見つかりません')
            )
            return
        
        total_tests = tests.count()
        processed_tests = 0
        total_results = 0
        finalized_results = 0
        errors = 0
        
        for test in tests:
            try:
                self.stdout.write(f'処理中: {test}')
                
                # 締切チェック
                if not force and timezone.now() <= test.schedule.deadline_at:
                    self.stdout.write(
                        self.style.WARNING(f'スキップ: {test} - 締切前です (締切: {test.schedule.deadline_at})')
                    )
                    continue
                
                # テスト結果を取得
                test_results = TestResult.objects.filter(test=test)
                
                if not test_results.exists():
                    self.stdout.write(
                        self.style.WARNING(f'スキップ: {test} - テスト結果がありません')
                    )
                    continue
                
                result_count = test_results.count()
                finalized_count = 0
                
                with transaction.atomic():
                    if recalculate:
                        # 順位を再計算
                        self.stdout.write(f'順位を再計算中...')
                        for result in test_results:
                            try:
                                calculate_test_results(result.student, test, force_temporary=False)
                                finalized_count += 1
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(f'再計算エラー: {result.student} - {str(e)}')
                                )
                                errors += 1
                    else:
                        # 既存の一時的順位を確定
                        for result in test_results:
                            try:
                                if not result.is_rank_finalized:
                                    result.finalize_ranks()
                                    finalized_count += 1
                                else:
                                    self.stdout.write(
                                        f'既に確定済み: {result.student.name}'
                                    )
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(f'確定エラー: {result.student} - {str(e)}')
                                )
                                errors += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'完了: {test} - {finalized_count}/{result_count}件確定')
                )
                
                total_results += result_count
                finalized_results += finalized_count
                processed_tests += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'テスト処理エラー: {test} - {str(e)}')
                )
                errors += 1
        
        # 結果サマリー
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== 処理完了 ===\n'
                f'処理済みテスト: {processed_tests}/{total_tests}\n'
                f'確定済み結果: {finalized_results}/{total_results}\n'
                f'エラー: {errors}件'
            )
        )
        
        # 確定状況の確認
        self.display_finalization_status(year, period, subject)

    def display_finalization_status(self, year, period, subject=None):
        """確定状況を表示"""
        
        query = TestDefinition.objects.filter(
            schedule__year=year,
            schedule__period=period,
            is_active=True
        )
        if subject:
            query = query.filter(subject=subject)
        
        tests = query
        
        if not tests.exists():
            return
        
        period_display = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}[period]
        
        self.stdout.write(
            self.style.SUCCESS(f'\n=== {year}年度 {period_display} 確定状況 ===')
        )
        
        for test in tests:
            total_results = TestResult.objects.filter(test=test).count()
            finalized_results = TestResult.objects.filter(
                test=test, 
                is_rank_finalized=True
            ).count()
            
            status = "完了" if finalized_results == total_results else f"{finalized_results}/{total_results}"
            deadline_status = "締切後" if timezone.now() > test.schedule.deadline_at else "締切前"
            
            self.stdout.write(
                f'{test.get_subject_display()}: {status} ({deadline_status})'
            )
        
        # 全体の確定率
        total_all = TestResult.objects.filter(test__in=tests).count()
        finalized_all = TestResult.objects.filter(
            test__in=tests,
            is_rank_finalized=True
        ).count()
        
        if total_all > 0:
            finalization_rate = (finalized_all / total_all) * 100
            self.stdout.write(
                self.style.SUCCESS(f'\n全体確定率: {finalization_rate:.1f}% ({finalized_all}/{total_all})')
            )