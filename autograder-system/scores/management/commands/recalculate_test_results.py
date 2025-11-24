from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from scores.utils import bulk_calculate_test_results
from tests.models import TestDefinition
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'テスト結果を一括再計算します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-id',
            type=int,
            help='特定のテストIDを指定して再計算'
        )
        parser.add_argument(
            '--year',
            type=int,
            help='年度を指定して再計算（periodと組み合わせて使用）'
        )
        parser.add_argument(
            '--period',
            type=str,
            choices=['spring', 'summer', 'winter'],
            help='期間を指定して再計算（yearと組み合わせて使用）'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='全テストの結果を再計算'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際の変更を行わずに処理内容を表示'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN モード: 実際の変更は行いません')
            )

        try:
            if options.get('test_id'):
                # 特定テストの再計算
                test_id = options['test_id']
                try:
                    test = TestDefinition.objects.get(id=test_id)
                    self.stdout.write(f"テスト「{test}」の結果を再計算します...")

                    if not dry_run:
                        count = bulk_calculate_test_results(test)
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {count}件の結果を再計算しました')
                        )
                    else:
                        self.stdout.write(f"対象テスト: {test}")

                except TestDefinition.DoesNotExist:
                    raise CommandError(f'テストID {test_id} が見つかりません')

            elif options.get('year') and options.get('period'):
                # 年度・期間指定の再計算
                year = options['year']
                period = options['period']

                tests = TestDefinition.objects.filter(
                    schedule__year=year,
                    schedule__period=period
                )

                if not tests.exists():
                    raise CommandError(f'{year}年度{period}期のテストが見つかりません')

                self.stdout.write(f"{year}年度{period}期の{tests.count()}件のテストを処理します...")

                total_count = 0
                for test in tests:
                    self.stdout.write(f"  - {test}")
                    if not dry_run:
                        count = bulk_calculate_test_results(test)
                        total_count += count
                        self.stdout.write(f"    → {count}件処理完了")

                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 合計 {total_count}件の結果を再計算しました')
                    )

            elif options.get('all'):
                # 全テストの再計算
                tests = TestDefinition.objects.all().order_by('schedule__year', 'schedule__period')

                if not tests.exists():
                    raise CommandError('テストが見つかりません')

                self.stdout.write(f"全{tests.count()}件のテストを処理します...")

                if not dry_run:
                    self.stdout.write(
                        self.style.WARNING('これには時間がかかる場合があります。続行しますか? [y/N]')
                    )
                    response = input().lower()
                    if response != 'y':
                        self.stdout.write('処理をキャンセルしました')
                        return

                total_count = 0
                for i, test in enumerate(tests, 1):
                    self.stdout.write(f"[{i}/{tests.count()}] {test}")
                    if not dry_run:
                        count = bulk_calculate_test_results(test)
                        total_count += count
                        self.stdout.write(f"    → {count}件処理完了")

                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ 全体で {total_count}件の結果を再計算しました')
                    )

            else:
                raise CommandError(
                    'オプションを指定してください: --test-id, --year と --period, または --all'
                )

        except Exception as e:
            logger.error(f"テスト結果再計算エラー: {str(e)}")
            raise CommandError(f'処理中にエラーが発生しました: {str(e)}')