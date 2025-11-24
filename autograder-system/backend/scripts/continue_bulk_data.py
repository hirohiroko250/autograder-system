"""
継続的大量ダミーデータ生成スクリプト
既存のデータから続きを生成（メモリ効率改善版）
"""

import os
import sys
import django
import random
import gc
from datetime import date

# Djangoセットアップ
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from schools.models import School
from classrooms.models import Classroom
from students.models import Student, StudentEnrollment
from tests.models import TestSchedule, TestDefinition, QuestionGroup
from scores.models import Score

# 小学生の学年表記
GRADE_NAMES = ['小1', '小2', '小3', '小4', '小5', '小6']

# 日本の都道府県（一部）
PREFECTURES = [
    '東京都', '神奈川県', '埼玉県', '千葉県', '大阪府', '兵庫県', '京都府',
    '愛知県', '福岡県', '北海道', '宮城県', '広島県', '静岡県', '茨城県',
    '栃木県', '群馬県', '新潟県', '長野県', '岐阜県', '三重県'
]

# 名字
LAST_NAMES = [
    '佐藤', '鈴木', '高橋', '田中', '伊藤', '渡辺', '山本', '中村', '小林', '加藤',
    '吉田', '山田', '佐々木', '山口', '松本', '井上', '木村', '林', '斎藤', '清水',
    '山崎', '森', '池田', '橋本', '阿部', '石川', '山下', '中島', '石井', '小川'
]

# 名前
FIRST_NAMES_MALE = ['翔太', '蓮', '大翔', '颯太', '陽翔', '湊', '悠真', '陽向', '朝陽', '樹']
FIRST_NAMES_FEMALE = ['陽菜', '結菜', '咲良', '凛', '葵', '美月', '結衣', '心春', '莉子', '花']

def generate_student_id():
    """10桁の生徒IDを生成"""
    return f"{random.randint(1000000000, 9999999999)}"

# 既存データを確認
existing_schools = School.objects.filter(school_id__startswith='2000').count()
print(f"既存の塾数: {existing_schools}")

# 続きから開始
start_index = existing_schools
target_schools = 100

print("=" * 70)
print("継続的大量ダミーデータ生成スクリプト（メモリ効率改善版）")
print("=" * 70)
print()
print(f"開始位置: 塾 {start_index + 1}校目から")
print(f"目標: 塾 {target_schools}校")
print()

# 既存のテストスケジュールとテスト定義を確認
test_schedule = TestSchedule.objects.filter(year=2025, period='summer').first()
if not test_schedule:
    print("エラー: 2025年夏季のテストスケジュールが見つかりません")
    sys.exit(1)

existing_tests = TestDefinition.objects.filter(schedule=test_schedule)
if not existing_tests.exists():
    print("エラー: 2025年夏季のテスト定義が見つかりません")
    sys.exit(1)

print(f"✓ テストスケジュール: {test_schedule}")
print(f"✓ テスト定義: {existing_tests.count()}件")
print()

skip_confirm = '--skip-confirm' in sys.argv or '-y' in sys.argv

if not skip_confirm:
    confirm = input("実行しますか？ (yes/no): ")
    if confirm.lower() != 'yes':
        print("キャンセルしました")
        sys.exit(0)
else:
    print("確認をスキップして実行します...")

print()
print("データ生成を開始します...")
print()

# カウンター
total_schools = 0
total_classrooms = 0
total_students = 0
total_scores = 0

# 塾を1校ずつ処理（メモリ効率改善）
for i in range(start_index, target_schools):
    prefecture = PREFECTURES[i % len(PREFECTURES)]
    school_name = f"{prefecture}学習塾{i+1:03d}号校"

    print(f"Processing school {i+1}/{target_schools}: {school_name}")

    school = School.objects.create(
        name=school_name,
        school_id=f"{200000 + i}",
        address=f"{prefecture}○○市△△町{i+1}-{i+1}",
        email=f"school{i+1:03d}@example.com",
        phone=f"03-1234-{i:04d}",
        status='active',
        membership_type='general',
        can_register_students=True,
        can_input_scores=True,
        can_view_reports=True,
    )
    total_schools += 1

    # 各塾に20教室を作成
    for j in range(20):
        classroom_name = f"{school.name.split('塾')[0]}教室{j+1:02d}"

        classroom = Classroom.objects.create(
            school=school,
            name=classroom_name,
            classroom_id=f"{school.school_id}{j+1:06d}",
        )
        total_classrooms += 1

        # 各教室に60名の生徒（小学1〜6年生、各学年10名）
        students_batch = []
        enrollments_batch = []

        for grade_idx in range(6):  # 0-5 for 小1-小6
            for k in range(10):
                gender = random.choice(['male', 'female'])
                last_name = random.choice(LAST_NAMES)

                if gender == 'male':
                    first_name = random.choice(FIRST_NAMES_MALE)
                else:
                    first_name = random.choice(FIRST_NAMES_FEMALE)

                student_name = f"{last_name} {first_name}"
                student_id = generate_student_id()

                # 生徒を作成（classroomに直接紐付け）
                student = Student(
                    student_id=student_id,
                    name=student_name,
                    grade=GRADE_NAMES[grade_idx],
                    classroom=classroom,
                    is_active=True,
                )
                students_batch.append(student)

        # 生徒を一括作成
        created_students = Student.objects.bulk_create(students_batch)
        total_students += len(created_students)

        # 登録情報を一括作成
        for student in created_students:
            enrollments_batch.append(StudentEnrollment(
                student=student,
                year=2025,
                period='summer',
                is_active=True,
            ))

        StudentEnrollment.objects.bulk_create(enrollments_batch)

        # 得点データを作成（教室ごとに処理してメモリを解放）
        tests = TestDefinition.objects.filter(schedule=test_schedule)
        score_batch = []

        for student in created_students:
            for test in tests:
                question_groups = QuestionGroup.objects.filter(test=test)

                for qg in question_groups:
                    max_score = qg.max_score
                    percentage = random.gauss(0.7, 0.15)
                    percentage = max(0, min(1, percentage))
                    score_value = int(max_score * percentage)

                    score_batch.append(Score(
                        student=student,
                        test=test,
                        question_group=qg,
                        score=score_value,
                        attendance=True,
                    ))
                    total_scores += 1

                    # バッチサイズを500に制限してメモリ使用を抑える
                    if len(score_batch) >= 500:
                        Score.objects.bulk_create(score_batch)
                        score_batch = []
                        gc.collect()  # ガベージコレクション実行

        # 残りを挿入
        if score_batch:
            Score.objects.bulk_create(score_batch)
            score_batch = []
            gc.collect()

    # 10校ごとに進捗を表示
    if (i + 1) % 10 == 0:
        print(f"  進捗: {i + 1}/{target_schools} schools")
        print(f"  合計: {total_schools}塾, {total_classrooms}教室, {total_students}生徒, {total_scores}得点")
        gc.collect()  # ガベージコレクション実行

print()
print("=" * 70)
print("データ生成完了！")
print("=" * 70)
print(f"新規作成:")
print(f"  塾: {total_schools}校")
print(f"  教室: {total_classrooms}教室")
print(f"  生徒: {total_students}名")
print(f"  得点: {total_scores}件")
print()

# 全体の集計
all_schools = School.objects.filter(school_id__startswith='2000').count()
all_classrooms = Classroom.objects.count()
all_students = Student.objects.count()
all_scores = Score.objects.count()

print(f"データベース全体:")
print(f"  塾: {all_schools}校")
print(f"  教室: {all_classrooms}教室")
print(f"  生徒: {all_students}名")
print(f"  得点: {all_scores}件")
print()
