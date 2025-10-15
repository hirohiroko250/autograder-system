from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from schools.models import School
from classrooms.models import Classroom
from students.models import Student
from tests.models import TestSchedule, TestDefinition
from scores.models import CommentTemplate

User = get_user_model()

class Command(BaseCommand):
    help = 'AutoGrader Pro の初期データを作成'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--demo',
            action='store_true',
            help='デモ用データも作成'
        )
    
    def handle(self, *args, **options):
        with transaction.atomic():
            self.create_superuser()
            self.create_test_schedules()
            
            if options['demo']:
                self.create_demo_data()
                self.create_comment_templates()
            
            self.stdout.write(
                self.style.SUCCESS('初期データの作成が完了しました')
            )
    
    def create_superuser(self):
        """管理者ユーザーの作成"""
        if not User.objects.filter(is_superuser=True).exists():
            user = User.objects.create_superuser(
                username='admin',
                password='admin123',
                email='admin@autograder.pro',
                role='school_admin',
                school_id='000000'
            )
            self.stdout.write('管理者ユーザーを作成しました')
    
    def create_test_schedules(self):
        """テストスケジュールの作成"""
        current_year = datetime.now().year
        schedules = [
            {
                'year': current_year,
                'period': 'spring',
                'planned_date': datetime(current_year, 3, 15),
                'deadline_at': timezone.make_aware(datetime(current_year, 3, 31, 23, 59, 59))
            },
            {
                'year': current_year,
                'period': 'summer',
                'planned_date': datetime(current_year, 7, 15),
                'deadline_at': timezone.make_aware(datetime(current_year, 7, 31, 23, 59, 59))
            },
            {
                'year': current_year,
                'period': 'winter',
                'planned_date': datetime(current_year, 12, 15),
                'deadline_at': timezone.make_aware(datetime(current_year, 12, 31, 23, 59, 59))
            }
        ]
        
        for schedule_data in schedules:
            schedule, created = TestSchedule.objects.get_or_create(
                year=schedule_data['year'],
                period=schedule_data['period'],
                defaults={
                    'planned_date': schedule_data['planned_date'],
                    'deadline_at': schedule_data['deadline_at']
                }
            )
            
            if created:
                # 各スケジュールに対して科目別テストを作成
                subjects = ['japanese', 'math', 'english', 'science', 'social']
                subject_names = {'japanese': '国語', 'math': '数学', 'english': '英語', 'science': '理科', 'social': '社会'}
                
                for subject in subjects:
                    TestDefinition.objects.get_or_create(
                        schedule=schedule,
                        subject=subject,
                        defaults={
                            'name': f'{schedule.get_period_display()} {subject_names[subject]}',
                            'max_score': 100
                        }
                    )
        
        self.stdout.write('テストスケジュールを作成しました')
    
    def create_demo_data(self):
        """デモ用データの作成"""
        # デモ用学校
        demo_school, created = School.objects.get_or_create(
            school_id='100001',
            defaults={
                'name': 'サンプル学習塾',
                'email': 'demo@autograder.pro',
                'phone': '03-1234-5678',
                'address': '東京都渋谷区サンプル1-2-3'
            }
        )
        
        # 学校管理者
        school_admin, created = User.objects.get_or_create(
            username='100001',
            defaults={
                'role': 'school_admin',
                'school_id': '100001',
                'email': 'school@demo.com'
            }
        )
        if created:
            school_admin.set_password('100001')
            school_admin.save()
        
        # デモ用教室
        demo_classrooms = [
            {'classroom_id': '100101', 'name': 'A教室'},
            {'classroom_id': '100102', 'name': 'B教室'},
            {'classroom_id': '100103', 'name': 'C教室'},
        ]
        
        for classroom_data in demo_classrooms:
            classroom, created = Classroom.objects.get_or_create(
                classroom_id=classroom_data['classroom_id'],
                defaults={
                    'school': demo_school,
                    'name': classroom_data['name']
                }
            )
            
            # 教室管理者
            classroom_admin, created = User.objects.get_or_create(
                username=classroom_data['classroom_id'],
                defaults={
                    'role': 'classroom_admin',
                    'school_id': demo_school.school_id,
                    'classroom_id': classroom_data['classroom_id'],
                    'email': f'classroom{classroom_data["classroom_id"]}@demo.com'
                }
            )
            if created:
                classroom_admin.set_password(classroom_data['classroom_id'])
                classroom_admin.save()
        
        # デモ用生徒
        demo_students = [
            {'student_id': '100001', 'name': '佐藤太郎', 'grade': '中学1年', 'classroom_id': '100101'},
            {'student_id': '100002', 'name': '田中花子', 'grade': '中学1年', 'classroom_id': '100101'},
            {'student_id': '100003', 'name': '山田次郎', 'grade': '中学2年', 'classroom_id': '100102'},
            {'student_id': '100004', 'name': '鈴木三郎', 'grade': '中学2年', 'classroom_id': '100102'},
            {'student_id': '100005', 'name': '高橋四郎', 'grade': '中学3年', 'classroom_id': '100103'},
        ]
        
        for student_data in demo_students:
            classroom = Classroom.objects.get(classroom_id=student_data['classroom_id'])
            Student.objects.get_or_create(
                student_id=student_data['student_id'],
                classroom=classroom,
                defaults={
                    'name': student_data['name'],
                    'grade': student_data['grade'],
                    'email': f'student{student_data["student_id"]}@demo.com'
                }
            )
        
        self.stdout.write('デモデータを作成しました')
    
    def create_comment_templates(self):
        """コメントテンプレートの作成"""
        demo_school = School.objects.get(school_id='100001')
        
        templates = [
            {
                'subject': 'japanese',
                'ranges': [
                    (90, 100, 'よくできました。この調子で頑張りましょう。'),
                    (70, 89, 'もう少し頑張りましょう。'),
                    (50, 69, '基礎から復習しましょう。'),
                    (0, 49, '先生と一緒に勉強し直しましょう。')
                ]
            },
            {
                'subject': 'math',
                'ranges': [
                    (90, 100, '計算力が身についています。応用問題にも挑戦しましょう。'),
                    (70, 89, '基本はできています。ケアレスミスに注意しましょう。'),
                    (50, 69, '計算練習を増やしましょう。'),
                    (0, 49, '基本的な計算から復習しましょう。')
                ]
            },
            {
                'subject': 'english',
                'ranges': [
                    (90, 100, 'Great job! Keep up the good work.'),
                    (70, 89, '単語の練習を増やしましょう。'),
                    (50, 69, '基本的な文法を復習しましょう。'),
                    (0, 49, 'アルファベットから復習しましょう。')
                ]
            }
        ]
        
        for template in templates:
            for min_score, max_score, text in template['ranges']:
                CommentTemplate.objects.get_or_create(
                    school=demo_school,
                    subject=template['subject'],
                    score_range_min=min_score,
                    score_range_max=max_score,
                    defaults={'template_text': text}
                )
        
        self.stdout.write('コメントテンプレートを作成しました')