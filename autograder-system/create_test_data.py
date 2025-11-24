#!/usr/bin/env python
import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from students.models import Student
from tests.models import TestDefinition, QuestionGroup
from scores.models import Score, TestResult

def create_test_data_for_student(student_id='10574'):
    """生徒10574用のテストデータを作成"""
    try:
        student = Student.objects.get(student_id=student_id)
        print(f"生徒: {student.name} ({student.grade})")
        
        # 5年生用のテストを取得
        tests = TestDefinition.objects.filter(grade_level='elementary_5')
        print(f"利用可能なテスト: {tests.count()}件")
        
        for test in tests:
            print(f"\nテスト: {test.get_subject_display()} (ID: {test.id})")
            
            # このテストの大問を取得
            question_groups = QuestionGroup.objects.filter(test=test).order_by('group_number')
            print(f"大問数: {question_groups.count()}")
            
            total_score = 0
            
            # 各大問にスコアを作成
            for group in question_groups:
                # サンプルスコアを生成（実際の点数は適当に設定）
                if test.subject == 'japanese':  # 国語
                    sample_scores = [8, 7, 9, 6, 8]  # 大問別の点数例
                else:  # 算数
                    sample_scores = [9, 8, 7, 9, 8]  # 大問別の点数例
                
                group_index = group.group_number - 1
                if group_index < len(sample_scores):
                    score_value = sample_scores[group_index]
                else:
                    score_value = 7  # デフォルト値
                
                # Scoreオブジェクト作成
                score, created = Score.objects.get_or_create(
                    student=student,
                    test=test,
                    question_group=group,
                    defaults={
                        'score': score_value,
                        'attendance': True,
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    }
                )
                
                if created:
                    print(f"  大問{group.group_number}: {score_value}点 (作成)")
                else:
                    print(f"  大問{group.group_number}: {score_value}点 (既存)")
                
                total_score += score_value
            
            # TestResultオブジェクト作成
            test_result, created = TestResult.objects.get_or_create(
                student=student,
                test=test,
                defaults={
                    'total_score': total_score,
                    'rank': 1,  # とりあえず1位
                    'created_at': timezone.now(),
                    'updated_at': timezone.now()
                }
            )
            
            if created:
                print(f"  テスト結果作成: 総合点{total_score}点")
            else:
                print(f"  テスト結果既存: 総合点{test_result.total_score}点")
        
        print(f"\n生徒{student_id}のテストデータ作成完了!")
        
    except Student.DoesNotExist:
        print(f"生徒ID {student_id} が見つかりません")
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_data_for_student('10574')