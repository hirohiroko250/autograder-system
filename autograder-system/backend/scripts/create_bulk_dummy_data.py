"""
大量ダミーデータ生成スクリプト
- 100校の塾
- 各塾に20教室
- 各教室に60名の生徒（小学1年生〜6年生、各学年10名）
- 2025年夏季テストの得点をランダムに生成
"""

import os
import sys
import django
import random
from datetime import date, datetime

# Djangoセットアップ
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

from schools.models import School
from classrooms.models import Classroom
from students.models import Student, StudentEnrollment
from test_schedules.models import TestScheduleInfo
from scores.models import Score

# 日本の都道府県
PREFECTURES = [
    '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
    '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
    '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
    '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
    '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
    '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
    '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
]

# 名字
LAST_NAMES = [
    '佐藤', '鈴木', '高橋', '田中', '伊藤', '渡辺', '山本', '中村', '小林', '加藤',
    '吉田', '山田', '佐々木', '山口', '松本', '井上', '木村', '林', '斎藤', '清水',
    '山崎', '森', '池田', '橋本', '阿部', '石川', '山下', '中島', '石井', '小川',
    '前田', '藤田', '後藤', '岡田', '長谷川', '村上', '近藤', '石田', '斉藤', '坂本',
    '遠藤', '青木', '藤井', '西村', '福田', '太田', '三浦', '岡本', '藤原', '松田'
]

# 名前（男女共通）
FIRST_NAMES_MALE = [
    '翔太', '蓮', '大翔', '颯太', '陽翔', '湊', '悠真', '陽向', '朝陽', '樹',
    '大和', '海斗', '蒼', '陸', '颯', '翼', '律', '碧', '暖', '新'
]

FIRST_NAMES_FEMALE = [
    '陽菜', '結菜', '咲良', '凛', '葵', '美月', '結衣', '心春', '莉子', '花',
    '美咲', '七海', '優奈', '愛莉', '彩花', '美羽', '心愛', '菜々子', '優衣', '結愛'
]

# 小学生の教科
ELEMENTARY_SUBJECTS = ['国語', '算数']

def generate_student_id():
    """10桁の生徒IDを生成"""
    return f"{random.randint(1000000000, 9999999999)}"

def create_schools(count=100):
    """塾を作成"""
    print(f"Creating {count} schools...")
    schools = []

    for i in range(count):
        prefecture = random.choice(PREFECTURES)
        school_name = f"{prefecture}学習塾{i+1:03d}号校"

        school = School.objects.create(
            name=school_name,
            school_id=f"{100000 + i}",
            address=f"{prefecture}○○市△△町{i+1}-{i+1}",
            contact_info=f"03-1234-{i:04d}",
            is_active=True,
            can_register_students=True,
            can_input_scores=True,
            can_view_reports=True,
        )
        schools.append(school)

        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1} schools...")

    print(f"✓ Created {count} schools")
    return schools

def create_classrooms_for_school(school, count=20):
    """1つの塾に教室を作成"""
    classrooms = []

    for i in range(count):
        classroom_name = f"{school.name.split('塾')[0]}教室{i+1:02d}"

        classroom = Classroom.objects.create(
            school=school,
            name=classroom_name,
            classroom_id=f"{school.school_id}{i+1:06d}",
            is_active=True,
        )
        classrooms.append(classroom)

    return classrooms

def create_students_for_classroom(classroom, students_per_grade=10):
    """1つの教室に生徒を作成（小学1〜6年生、各学年10名）"""
    students = []

    for grade in range(1, 7):  # 小学1年生〜6年生
        for j in range(students_per_grade):
            # 性別をランダムに決定
            gender = random.choice(['male', 'female'])
            last_name = random.choice(LAST_NAMES)

            if gender == 'male':
                first_name = random.choice(FIRST_NAMES_MALE)
            else:
                first_name = random.choice(FIRST_NAMES_FEMALE)

            student_name = f"{last_name} {first_name}"
            student_id = generate_student_id()

            # 生年月日を計算（2025年時点での学年から逆算）
            birth_year = 2025 - grade - 6  # 小学1年生は2018年生まれ
            birth_month = random.randint(4, 12)  # 4月〜12月生まれ
            if birth_month == 2:
                birth_day = random.randint(1, 28)
            elif birth_month in [4, 6, 9, 11]:
                birth_day = random.randint(1, 30)
            else:
                birth_day = random.randint(1, 31)

            student = Student.objects.create(
                student_id=student_id,
                name=student_name,
                grade=grade,
                date_of_birth=date(birth_year, birth_month, birth_day),
                school=classroom.school,
            )

            # 教室への登録
            StudentEnrollment.objects.create(
                student=student,
                classroom=classroom,
                enrollment_date=date(2025, 4, 1),
                is_active=True,
            )

            students.append(student)

    return students

def create_test_schedule():
    """2025年夏季テストのスケジュールを作成"""
    # 既存のスケジュールを確認
    existing = TestScheduleInfo.objects.filter(
        year='2025',
        period='summer'
    ).first()

    if existing:
        print("2025年夏季テストのスケジュールは既に存在します")
        return existing

    test_schedule = TestScheduleInfo.objects.create(
        year='2025',
        period='summer',
        planned_date=date(2025, 7, 15),
        actual_date=date(2025, 7, 15),
        deadline=datetime(2025, 7, 31, 23, 59, 59),
        status='completed',
    )

    print("✓ Created 2025年夏季テストスケジュール")
    return test_schedule

def create_scores_for_students(students, test_schedule):
    """生徒の得点を生成"""
    scores_created = 0

    for student in students:
        for subject in ELEMENTARY_SUBJECTS:
            # 得点をランダムに生成（0〜100点）
            # 正規分布で生成（平均70点、標準偏差15）
            score = int(random.gauss(70, 15))
            score = max(0, min(100, score))  # 0〜100の範囲に制限

            Score.objects.create(
                student=student,
                test_schedule=test_schedule,
                subject=subject,
                score=score,
            )
            scores_created += 1

    return scores_created

def main():
    print("=" * 60)
    print("大量ダミーデータ生成スクリプト")
    print("=" * 60)
    print()
    print("生成するデータ:")
    print("  - 塾: 100校")
    print("  - 教室: 各塾20教室 (合計2,000教室)")
    print("  - 生徒: 各教室60名 (合計120,000名)")
    print("  - 得点: 2025年夏季テスト (合計240,000件)")
    print()

    confirm = input("実行しますか？ (yes/no): ")
    if confirm.lower() != 'yes':
        print("キャンセルしました")
        return

    print()
    print("データ生成を開始します...")
    print()

    # 2025年夏季テストスケジュールを作成
    test_schedule = create_test_schedule()
    print()

    # 塾を作成
    schools = create_schools(100)
    print()

    # 各塾に教室と生徒を作成
    total_classrooms = 0
    total_students = 0
    total_scores = 0

    for idx, school in enumerate(schools):
        print(f"Processing school {idx + 1}/100: {school.name}")

        # 教室を作成
        classrooms = create_classrooms_for_school(school, 20)
        total_classrooms += len(classrooms)

        # 各教室に生徒を作成
        for classroom in classrooms:
            students = create_students_for_classroom(classroom, students_per_grade=10)
            total_students += len(students)

            # 得点を作成
            scores = create_scores_for_students(students, test_schedule)
            total_scores += scores

        if (idx + 1) % 10 == 0:
            print(f"  Progress: {idx + 1}/100 schools completed")
            print(f"  Current totals: {total_classrooms} classrooms, {total_students} students, {total_scores} scores")
            print()

    print()
    print("=" * 60)
    print("データ生成完了！")
    print("=" * 60)
    print(f"塾: {len(schools)}校")
    print(f"教室: {total_classrooms}教室")
    print(f"生徒: {total_students}名")
    print(f"得点: {total_scores}件")
    print()

if __name__ == '__main__':
    main()
