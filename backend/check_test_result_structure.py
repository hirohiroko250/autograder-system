#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from scores.models import TestResult, Score
from students.models import Student

def check_test_result_structure():
    student_id = '10574'
    
    try:
        student = Student.objects.get(student_id=student_id)
        print(f"生徒: {student.name} ({student.student_id})")
        
        # TestResultを取得
        test_results = TestResult.objects.filter(student=student)
        print(f"\nTestResult件数: {test_results.count()}")
        
        for result in test_results:
            print(f"\n=== テスト結果 {result.id} ===")
            print(f"テストID: {result.test.id}")
            print(f"テスト名: {result.test.get_subject_display()}")
            print(f"年度: {result.test.schedule.year}")
            print(f"期間: {result.test.schedule.get_period_display()}")
            print(f"総合点: {result.total_score}")
            print(f"学年順位: {result.grade_rank}")
            print(f"学年総数: {result.grade_total}")
            
            # 関連するスコアを取得
            scores = Score.objects.filter(student=student, test=result.test).order_by('question_group__group_number')
            print(f"大問別スコア:")
            total_max_score = 0
            for score in scores:
                print(f"  大問{score.question_group.group_number}: {score.score}/{score.question_group.max_score}点")
                total_max_score += score.question_group.max_score
            print(f"満点: {total_max_score}")
            
    except Student.DoesNotExist:
        print(f"生徒ID {student_id} が見つかりません")
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_test_result_structure()