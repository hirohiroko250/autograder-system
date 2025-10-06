"""
テスト結果を一括集計する管理コマンド
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Avg, StdDev
from django.utils import timezone
from scores.models import Score, TestResult
from tests.models import TestDefinition
import gc

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
        batch_size = 500

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

            for idx, student_total in enumerate(student_totals):
                student_id = student_total['student']
                total_score = student_total['total_score']
                correct_rate = (total_score / 100.0) * 100 if total_score else 0

                test_result, created = TestResult.objects.get_or_create(
                    student_id=student_id,
                    test=test,
                    defaults={
                        'total_score': total_score,
                        'correct_rate': correct_rate,
                        'is_rank_finalized': False
                    }
                )

                if created:
                    generated_count += 1
                elif test_result.total_score != total_score:
                    test_result.total_score = total_score
                    test_result.correct_rate = correct_rate
                    test_result.save()
                    generated_count += 1

                if (idx + 1) % batch_size == 0:
                    gc.collect()
                    self.stdout.write(f'  処理中: {idx + 1}件')

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
