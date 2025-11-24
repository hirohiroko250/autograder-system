"""
ダミーデータを2万名に削減するスクリプト
"""
import os
import sys
import django

# プロジェクトのルートディレクトリをパスに追加
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from students.models import Student
from schools.models import School
from classrooms.models import Classroom
from scores.models import Score, TestResult

print('=' * 70)
print('ダミーデータ削減スクリプト')
print('目標: 生徒数を76,625名 → 20,000名に削減')
print('=' * 70)

# 現在のダミーデータを確認
dummy_schools = School.objects.filter(school_id__gte='200000').order_by('school_id')
dummy_students = Student.objects.filter(classroom__school__school_id__gte='200000')

print(f'\n現在のダミーデータ:')
print(f'  学校数: {dummy_schools.count()}')
print(f'  生徒数: {dummy_students.count()}')

# 20,000名に減らすため、保持する学校数を計算
# 各学校は約1,178名 (76,625 / 65)
# 20,000名 ÷ 1,178 ≈ 17校
target_students = 20000
schools_to_keep = 17

print(f'\n削減計画:')
print(f'  保持する学校数: {schools_to_keep}校')
print(f'  削除する学校数: {dummy_schools.count() - schools_to_keep}校')

# 最初の17校を保持、残りを削除
schools_to_delete = list(dummy_schools[schools_to_keep:])

print(f'\n削除対象の学校ID: {[s.school_id for s in schools_to_delete[:5]]}... (計{len(schools_to_delete)}校)')

# 削除対象の生徒を確認
students_to_delete = Student.objects.filter(classroom__school__in=schools_to_delete)
print(f'削除対象の生徒数: {students_to_delete.count()}名')

# 関連データも削除されることを確認
scores_to_delete = Score.objects.filter(student__classroom__school__in=schools_to_delete)
test_results_to_delete = TestResult.objects.filter(student__classroom__school__in=schools_to_delete)

print(f'削除対象のScore数: {scores_to_delete.count()}件')
print(f'削除対象のTestResult数: {test_results_to_delete.count()}件')

# 確認
print('\n削除を実行しますか? (この操作は取り消せません)')
confirm = input('yes と入力して続行: ')

if confirm.lower() == 'yes':
    print('\n削除を開始します...')

    # TestResultを削除
    deleted_tr = test_results_to_delete.delete()
    print(f'✓ TestResult削除: {deleted_tr[0]}件')

    # Scoreを削除
    deleted_scores = scores_to_delete.delete()
    print(f'✓ Score削除: {deleted_scores[0]}件')

    # 学校を削除（カスケード削除で教室・生徒も削除される）
    deleted_schools = 0
    for school in schools_to_delete:
        school.delete()
        deleted_schools += 1
        if deleted_schools % 5 == 0:
            print(f'  進捗: {deleted_schools}/{len(schools_to_delete)}校削除')

    print(f'✓ 学校削除: {deleted_schools}校（教室・生徒も自動削除）')

    # 結果確認
    remaining_students = Student.objects.filter(classroom__school__school_id__gte='200000').count()
    remaining_schools = School.objects.filter(school_id__gte='200000').count()

    print('\n' + '=' * 70)
    print('削除完了！')
    print(f'  残りの学校数: {remaining_schools}校')
    print(f'  残りの生徒数: {remaining_students}名')
    print('=' * 70)
else:
    print('キャンセルしました。')
