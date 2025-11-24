"""
テスト結果を一括集計する管理コマンド
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Avg, StdDev
from django.utils import timezone
from django.db import OperationalError
from scores.models import Score, TestResult
from tests.models import TestDefinition
import gc
import time

class Command(BaseCommand):
    help = 'ScoreからTestResultを生成し、順位・偏差値を計算します'

    def handle(self, *args, **options):
        self.stdout.write('=' * 70)
        self.stdout.write('テスト結果一括集計開始')
        self.stdout.write('=' * 70)
        
        # STEP 1: ScoreからTestResultを生成
        self.stdout.write('\n[STEP 1] TestResult生成中...')
        generated_count = 0
        tests = TestDefinition.objects.all()
        batch_size = 100  # バッチサイズを小さく

        for test in tests:
            student_totals = Score.objects.filter(
                test=test,
                attendance=True,
                score__gte=0
            ).values('student').annotate(
                total_score=Sum('score'),
                question_count=Count('question_group')
            ).filter(
                question_count__gt=0
            )

            # 既存のTestResultを取得（更新用）
            existing_results = {
                (r.student_id, r.test_id): r
                for r in TestResult.objects.filter(test=test).select_related('student')
            }

            create_batch = []
            update_batch = []

            for idx, student_total in enumerate(student_totals):
                student_id = student_total['student']
                total_score = student_total['total_score']
                correct_rate = (total_score / 100.0) * 100 if total_score else 0

                key = (student_id, test.id)
                if key in existing_results:
                    # 既存レコードを更新
                    result = existing_results[key]
                    if result.total_score != total_score:
                        result.total_score = total_score
                        result.correct_rate = correct_rate
                        update_batch.append(result)
                else:
                    # 新規レコードを作成
                    create_batch.append(TestResult(
                        student_id=student_id,
                        test=test,
                        total_score=total_score,
                        correct_rate=correct_rate,
                        is_rank_finalized=False
                    ))

                # バッチ処理（リトライロジック付き）
                if len(create_batch) >= batch_size:
                    for retry in range(3):
                        try:
                            TestResult.objects.bulk_create(create_batch, ignore_conflicts=True)
                            generated_count += len(create_batch)
                            create_batch = []
                            gc.collect()
                            self.stdout.write(f'  生成: {generated_count}件')
                            break
                        except OperationalError as e:
                            if 'database is locked' in str(e) and retry < 2:
                                self.stdout.write(f'  [警告] DBロック検出、{retry+1}秒待機...')
                                time.sleep(retry + 1)
                            else:
                                raise

                if len(update_batch) >= batch_size:
                    for retry in range(3):
                        try:
                            TestResult.objects.bulk_update(update_batch, ['total_score', 'correct_rate'])
                            generated_count += len(update_batch)
                            update_batch = []
                            gc.collect()
                            break
                        except OperationalError as e:
                            if 'database is locked' in str(e) and retry < 2:
                                time.sleep(retry + 1)
                            else:
                                raise

            # 残りのバッチを処理
            if create_batch:
                TestResult.objects.bulk_create(create_batch, ignore_conflicts=True)
                generated_count += len(create_batch)
            if update_batch:
                TestResult.objects.bulk_update(update_batch, ['total_score', 'correct_rate'])
                generated_count += len(update_batch)

        self.stdout.write(self.style.SUCCESS(f'✓ TestResult生成/更新: {generated_count}件'))

        # STEP 2: 順位・偏差値を計算
        self.stdout.write('\n[STEP 2] 順位・偏差値計算中...')
        updated_count = 0

        for test in tests:
            grades = TestResult.objects.filter(test=test).values_list('student__grade', flat=True).distinct()

            for grade in grades:
                if not grade:
                    continue

                stats = TestResult.objects.filter(
                    test=test,
                    student__grade=grade
                ).aggregate(
                    avg_score=Avg('total_score'),
                    std_dev=StdDev('total_score'),
                    total_count=Count('id')
                )

                total_students = stats['total_count'] or 0
                if total_students == 0:
                    continue

                avg_score = stats['avg_score'] or 0
                std_dev = stats['std_dev'] or 1

                grade_results = TestResult.objects.filter(
                    test=test,
                    student__grade=grade
                ).select_related('student', 'student__classroom', 'student__classroom__school').order_by('-total_score')

                rank = 1
                prev_score = None
                actual_rank = 1
                update_batch = []

                for result in grade_results.iterator(chunk_size=100):
                    if prev_score is not None and result.total_score < prev_score:
                        rank = actual_rank

                    if std_dev > 0:
                        deviation_score = 50 + (result.total_score - avg_score) / std_dev * 10
                        deviation_score = max(0, min(100, deviation_score))
                    else:
                        deviation_score = 50

                    result.grade_rank = rank
                    result.grade_total = total_students
                    result.grade_deviation_score = round(deviation_score, 2)

                    school_id = result.student.classroom.school.id if result.student.classroom else None
                    if school_id:
                        better_school_results = TestResult.objects.filter(
                            test=test,
                            student__classroom__school_id=school_id,
                            student__grade=grade,
                            total_score__gt=result.total_score
                        ).count()
                        school_total = TestResult.objects.filter(
                            test=test,
                            student__classroom__school_id=school_id,
                            student__grade=grade
                        ).count()
                        result.school_rank_final = better_school_results + 1
                        result.school_total_final = school_total

                    result.is_rank_finalized = True
                    result.rank_finalized_at = timezone.now()

                    update_batch.append(result)

                    if len(update_batch) >= 100:
                        TestResult.objects.bulk_update(
                            update_batch,
                            ['grade_rank', 'grade_total', 'grade_deviation_score',
                             'school_rank_final', 'school_total_final',
                             'is_rank_finalized', 'rank_finalized_at']
                        )
                        updated_count += len(update_batch)
                        self.stdout.write(f'  処理中: {updated_count}件')
                        update_batch = []
                        gc.collect()

                    prev_score = result.total_score
                    actual_rank += 1

                if update_batch:
                    TestResult.objects.bulk_update(
                        update_batch,
                        ['grade_rank', 'grade_total', 'grade_deviation_score',
                         'school_rank_final', 'school_total_final',
                         'is_rank_finalized', 'rank_finalized_at']
                    )
                    updated_count += len(update_batch)

        self.stdout.write(self.style.SUCCESS(f'✓ 順位・偏差値計算: {updated_count}件'))

        # STEP 3: 0点(欠席者)を削除
        self.stdout.write('\n[STEP 3] 欠席者削除中...')
        deleted_count = TestResult.objects.filter(total_score=0).delete()[0]
        self.stdout.write(self.style.SUCCESS(f'✓ 欠席者削除: {deleted_count}件'))

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✅ 一括集計完了！'))
        self.stdout.write(f'  TestResult生成/更新: {generated_count}件')
        self.stdout.write(f'  順位・偏差値計算: {updated_count}件')
        self.stdout.write(f'  欠席者削除: {deleted_count}件')
        self.stdout.write('=' * 70)
