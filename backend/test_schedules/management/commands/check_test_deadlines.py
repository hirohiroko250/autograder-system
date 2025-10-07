from django.core.management.base import BaseCommand
from django.utils import timezone
from test_schedules.models import TestScheduleInfo


class Command(BaseCommand):
    help = 'テストの締切時刻をチェックし、締切を過ぎたテストを自動的に完了状態にする'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際の更新は行わず、対象データのみ表示する'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        # 締切を過ぎた実施中のテストを取得
        expired_tests = TestScheduleInfo.objects.filter(
            status='in_progress',
            deadline__lt=now
        )

        if not expired_tests.exists():
            self.stdout.write(
                self.style.SUCCESS('締切を過ぎたテストはありません。')
            )
            return

        self.stdout.write(f'締切を過ぎたテスト: {expired_tests.count()}件')

        for test in expired_tests:
            period_display = test.get_period_display()
            deadline_str = test.deadline.strftime('%Y-%m-%d %H:%M')

            if dry_run:
                self.stdout.write(
                    f'[DRY RUN] 完了予定: {test.year}年度{period_display} '
                    f'(締切: {deadline_str})'
                )
            else:
                test.status = 'completed'
                test.actual_date = now.date()
                test.save()  # シグナルが課金レポートを自動生成

                self.stdout.write(
                    self.style.SUCCESS(
                        f'完了処理済み: {test.year}年度{period_display} '
                        f'(締切: {deadline_str})'
                    )
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n{expired_tests.count()}件のテストを完了状態にしました。'
                    '課金レポートが自動生成されています。'
                )
            )