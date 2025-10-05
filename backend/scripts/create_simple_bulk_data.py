"""
簡易版大量ダミーデータ生成スクリプト
既存のテスト定義を使用してデータを生成
"""

import os
import sys
import django
import random
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

print("=" * 70)
print("簡易版 大量ダミーデータ生成スクリプト")
print("=" * 70)
print()
print("生成するデータ:")
print("  - 塾: 100校")
print("  - 教室: 各塾20教室 (合計2,000教室)")
print("  - 生徒: 各教室60名、小学1〜6年生各10名 (合計120,000名)")
print()

# 既存のテストスケジュールとテスト定義を確認
test_schedule = TestSchedule.objects.filter(year=2025, period='summer').first()
if not test_schedule:
    print("エラー: 2025年夏季のテストスケジュールが見つかりません")
    print("先にテストスケジュールを作成してください")
    sys.exit(1)

existing_tests = TestDefinition.objects.filter(schedule=test_schedule)
if not existing_tests.exists():
    print("エラー: 2025年夏季のテスト定義が見つかりません")
    print("先にテスト定義を作成してください")
    sys.exit(1)

print(f"✓ テストスケジュール: {test_schedule}")
print(f"✓ テスト定義: {existing_tests.count()}件")
print()

confirm = input("実行しますか？ (yes/no): ")
if confirm.lower() != 'yes':
    print("キャンセルしました")
    sys.exit(0)

print()
print("データ生成を開始します...")
print()

# カウンター
total_schools = 0
total_classrooms = 0
total_students = 0
total_scores = 0

# 100校の塾を作成
print("Step 1/4: 塾を作成中...")
for i in range(100):
    prefecture = PREFECTURES[i % len(PREFECTURES)]
    school_name = f"{prefecture}学習塾{i+1:03d}号校"

    school = School.objects.create(
        name=school_name,
        school_id=f"{100000 + i}",
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
        for grade in range(1, 7):
            for k in range(10):
                gender = random.choice(['male', 'female'])
                last_name = random.choice(LAST_NAMES)

                if gender == 'male':
                    first_name = random.choice(FIRST_NAMES_MALE)
                else:
                    first_name = random.choice(FIRST_NAMES_FEMALE)

                student_name = f"{last_name} {first_name}"
                student_id = generate_student_id()

                # 生年月日を計算
                birth_year = 2025 - grade - 6
                birth_month = random.randint(4, 12)
                birth_day = random.randint(1, 28)

                student = Student.objects.create(
                    student_id=student_id,
                    name=student_name,
                    grade=grade,
                    date_of_birth=date(birth_year, birth_month, birth_day),
                    school=school,
                )

                # 教室への登録
                StudentEnrollment.objects.create(
                    student=student,
                    classroom=classroom,
                    enrollment_date=date(2025, 4, 1),
                )

                total_students += 1

    if (i + 1) % 10 == 0:
        print(f"  進捗: {i + 1}/100 schools, {total_classrooms} classrooms, {total_students} students")

print(f"✓ 塾・教室・生徒の作成完了")
print(f"  塾: {total_schools}校")
print(f"  教室: {total_classrooms}教室")
print(f"  生徒: {total_students}名")
print()

# 得点データを作成
print("Step 2/4: 得点データを作成中...")
print("注意: この処理には時間がかかります（数分〜数十分）")
print()

students = Student.objects.all()
tests = TestDefinition.objects.filter(schedule=test_schedule)

batch_size = 1000
score_batch = []

for idx, student in enumerate(students):
    for test in tests:
        # テストの問題グループを取得
        question_groups = QuestionGroup.objects.filter(test=test)

        for qg in question_groups:
            # 得点をランダムに生成（0〜max_score）
            max_score = qg.max_score
            # 正規分布で生成（平均70%、標準偏差15%）
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

    # バッチ挿入
    if len(score_batch) >= batch_size:
        Score.objects.bulk_create(score_batch)
        score_batch = []

    if (idx + 1) % 1000 == 0:
        print(f"  進捗: {idx + 1}/{students.count()} students, {total_scores} scores")

# 残りを挿入
if score_batch:
    Score.objects.bulk_create(score_batch)

print(f"✓ 得点データの作成完了: {total_scores}件")
print()

print("=" * 70)
print("データ生成完了！")
print("=" * 70)
print(f"塾: {total_schools}校")
print(f"教室: {total_classrooms}教室")
print(f"生徒: {total_students}名")
print(f"得点: {total_scores}件")
print()
