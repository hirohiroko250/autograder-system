"""
名大SKYのデータを復元するスクリプト
"""
import os
import sys
import django
import random

# プロジェクトのルートディレクトリをパスに追加
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from students.models import Student
from schools.models import School
from classrooms.models import Classroom
from scores.models import Score
from tests.models import TestDefinition

print('=' * 70)
print('名大SKY データ復元スクリプト')
print('=' * 70)

# 学校を作成
school, created = School.objects.get_or_create(
    school_id='999999',
    defaults={
        'name': '名大SKY',
        'address': '愛知県名古屋市',
        'phone': '052-000-0000'
    }
)

if created:
    print(f'✓ 学校作成: {school.name} (ID: {school.school_id})')
else:
    print(f'  学校既存: {school.name} (ID: {school.school_id})')

# 教室を作成（60教室）
# 小1〜中3 = 9学年 × 約7教室/学年 ≈ 60教室
classrooms = []
classroom_count = 0
students_per_grade = {
    1: 150,  # 小1
    2: 150,  # 小2
    3: 160,  # 小3
    4: 160,  # 小4
    5: 160,  # 小5
    6: 170,  # 小6
    7: 150,  # 中1
    8: 150,  # 中2
    9: 150,  # 中3
}

classroom_id_counter = 1
for grade in range(1, 10):  # 小1〜中3
    num_students = students_per_grade[grade]
    students_per_classroom = 25  # 各教室約25名
    num_classrooms = (num_students + students_per_classroom - 1) // students_per_classroom

    for cls_num in range(1, num_classrooms + 1):
        classroom_id = f'99{classroom_id_counter:04d}'
        classroom, created = Classroom.objects.get_or_create(
            classroom_id=classroom_id,
            defaults={
                'school': school,
                'name': f'{grade}年{cls_num}組'
            }
        )
        classrooms.append((classroom, grade, num_students // num_classrooms, cls_num))
        if created:
            classroom_count += 1
        classroom_id_counter += 1

print(f'✓ 教室作成: {classroom_count}教室')

# 生徒を作成（約1400名）
student_count = 0
all_students = []

for classroom, grade, num_students, cls_num in classrooms:
    for i in range(1, num_students + 1):
        student_id = f'999999{grade:02d}{cls_num:02d}{i:03d}'
        student, created = Student.objects.get_or_create(
            student_id=student_id,
            defaults={
                'classroom': classroom,
                'name': f'生徒{student_id}',
                'grade': str(grade)
            }
        )
        if created:
            student_count += 1
            all_students.append(student)

print(f'✓ 生徒作成: {student_count}名')

# 2025年夏季テストを取得 (TestDefinitionにtest_nameフィールドがないので、最初のテストを使う)
test = TestDefinition.objects.first()

if not test:
    print('⚠ テストが見つかりません')
else:
    print(f'テスト使用: ID={test.id}')

if test:
    print(f'\nテストデータ作成: {test.test_name}')

    # 問題グループを取得
    question_groups = test.question_groups.all()

    if question_groups:
        score_count = 0
        batch_size = 500
        score_batch = []

        for student in all_students:
            # 80%の確率で出席
            if random.random() < 0.8:
                for qg in question_groups:
                    # ランダムに得点を生成（0〜満点）
                    score_value = random.randint(0, qg.max_score)

                    score_batch.append(Score(
                        student=student,
                        test=test,
                        question_group=qg,
                        score=score_value,
                        attendance=True
                    ))

                    if len(score_batch) >= batch_size:
                        Score.objects.bulk_create(score_batch, ignore_conflicts=True)
                        score_count += len(score_batch)
                        score_batch = []
                        print(f'  Score作成中: {score_count}件', end='\r')

        # 残りのバッチを処理
        if score_batch:
            Score.objects.bulk_create(score_batch, ignore_conflicts=True)
            score_count += len(score_batch)

        print(f'\n✓ Score作成: {score_count}件')
    else:
        print('⚠ 問題グループが見つかりません')
else:
    print('✗ テストが見つかりません。得点データは作成されませんでした。')

print('\n' + '=' * 70)
print('✅ 名大SKY データ復元完了！')
print(f'  学校: {school.name}')
print(f'  教室数: {len(classrooms)}教室')
print(f'  生徒数: {student_count}名')
if test and question_groups:
    print(f'  得点データ: {score_count}件')
print('=' * 70)
