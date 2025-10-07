#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from students.models import Student
from tests.models import TestDefinition
from scores.models import Score, TestResult

def debug_student_relations():
    student_id = '10574'
    
    try:
        student = Student.objects.get(student_id=student_id)
        print(f"生徒: {student.name} (ID: {student.id}, student_id: {student.student_id})")
        
        # このstudentオブジェクトを使ってスコアを検索
        scores_by_student = Score.objects.filter(student=student)
        print(f"Student objectでのScore検索: {scores_by_student.count()}件")
        
        # student_idフィールドでスコアを検索
        scores_by_student_id = Score.objects.filter(student_id=student.student_id)
        print(f"student_idでのScore検索: {scores_by_student_id.count()}件")
        
        # 同様にTestResult
        results_by_student = TestResult.objects.filter(student=student)
        print(f"Student objectでのTestResult検索: {results_by_student.count()}件")
        
        results_by_student_id = TestResult.objects.filter(student_id=student.student_id)
        print(f"student_idでのTestResult検索: {results_by_student_id.count()}件")
        
        # Score modelのフィールド構造を確認
        print(f"\nScore modelのフィールド:")
        for field in Score._meta.fields:
            print(f"  {field.name}: {field}")
        
        print(f"\nTestResult modelのフィールド:")
        for field in TestResult._meta.fields:
            print(f"  {field.name}: {field}")
            
        # 実際のスコアデータのサンプル
        print(f"\nScore テーブルの最初の5件:")
        for score in Score.objects.all()[:5]:
            print(f"  student_id: '{score.student_id}' (型: {type(score.student_id)})")
            
        print(f"\nTestResult テーブルの最初の5件:")
        for result in TestResult.objects.all()[:5]:
            print(f"  student_id: '{result.student_id}' (型: {type(result.student_id)})")
            
    except Student.DoesNotExist:
        print(f"生徒ID {student_id} が見つかりません")
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_student_relations()