import pandas as pd
from django.core.exceptions import ValidationError
from .models import School
from classrooms.models import Classroom
from students.models import Student
from accounts.models import User
from django.db import transaction
import random
import string

def generate_classroom_id(school_id):
    """教室IDを生成（塾ID + 連番2桁）"""
    existing_classrooms = Classroom.objects.filter(
        classroom_id__startswith=school_id
    ).count()
    next_number = existing_classrooms + 1
    return f"{school_id}{next_number:02d}"

def generate_student_id(classroom_id):
    """生徒IDを生成（教室ID + 連番2桁）"""
    existing_students = Student.objects.filter(
        classroom=Classroom.objects.get(classroom_id=classroom_id)
    ).count()
    next_number = existing_students + 1
    return f"{classroom_id}{next_number:02d}"

def generate_password(length=8):
    """ランダムパスワード生成"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def import_schools_from_excel(file_path):
    """
    Excelファイルから塾情報を一括インポート
    
    必要な列:
    - 塾ID (school_id)
    - 塾名 (name)
    - メールアドレス (email)
    - 電話番号 (phone) - オプション
    - 住所 (address) - オプション
    """
    try:
        df = pd.read_excel(file_path)
        
        # 必要な列をチェック
        required_columns = ['塾ID', '塾名', '担当者名', 'メールアドレス']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(f"必要な列が不足しています: {', '.join(missing_columns)}")
        
        created_schools = []
        created_users = []
        errors = []
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # 担当者名を取得
                    contact_name = row.get('担当者名', f"{row['塾名']}管理者")
                    
                    # 塾データを作成
                    school_data = {
                        'school_id': str(row['塾ID']).zfill(6),  # 6桁にゼロパディング
                        'name': row['塾名'],
                        'contact_person': contact_name,
                        'email': row['メールアドレス'],
                        'phone': row.get('電話番号', ''),
                        'address': row.get('住所', ''),
                    }
                    
                    # 塾IDの重複チェック
                    if School.objects.filter(school_id=school_data['school_id']).exists():
                        errors.append(f"行{index + 2}: 塾ID {school_data['school_id']} は既に存在します")
                        continue
                    
                    # 塾を作成
                    school = School.objects.create(**school_data)
                    created_schools.append(school)
                    
                    # 塾管理者ユーザーを作成
                    password = generate_password()
                    user = User.objects.create_user(
                        username=school.school_id,
                        email=school.email,
                        password=password,
                        role='school_admin',
                        school_id=school.school_id,
                        first_name=contact_name,
                    )
                    created_users.append({'user': user, 'password': password})
                    
                except Exception as e:
                    errors.append(f"行{index + 2}: {str(e)}")
        
        return {
            'success': True,
            'created_schools': len(created_schools),
            'created_users': len(created_users),
            'user_credentials': [
                {
                    'school_name': item['user'].first_name,
                    'username': item['user'].username,
                    'password': item['password']
                }
                for item in created_users
            ],
            'errors': errors
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def import_students_from_excel(file_path, classroom_id):
    """
    Excelファイルから生徒情報を一括インポート
    
    必要な列:
    - 生徒名 (name)
    - 学年 (grade)
    - メールアドレス (email) - オプション
    """
    try:
        df = pd.read_excel(file_path)
        
        # 必要な列をチェック
        required_columns = ['生徒名', '学年']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(f"必要な列が不足しています: {', '.join(missing_columns)}")
        
        # 教室の存在確認
        try:
            classroom = Classroom.objects.get(classroom_id=classroom_id)
        except Classroom.DoesNotExist:
            raise ValidationError(f"教室ID {classroom_id} が見つかりません")
        
        created_students = []
        errors = []
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # 生徒IDを生成
                    student_id = generate_student_id(classroom_id)
                    
                    # 生徒データを作成
                    student_data = {
                        'student_id': student_id,
                        'classroom': classroom,
                        'name': row['生徒名'],
                        'grade': row['学年'],
                        'email': row.get('メールアドレス', ''),
                    }
                    
                    # 生徒を作成
                    student = Student.objects.create(**student_data)
                    created_students.append(student)
                    
                except Exception as e:
                    errors.append(f"行{index + 2}: {str(e)}")
        
        return {
            'success': True,
            'created_students': len(created_students),
            'students': [
                {
                    'student_id': student.student_id,
                    'name': student.name,
                    'grade': student.grade
                }
                for student in created_students
            ],
            'errors': errors
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def export_school_template():
    """塾登録用のExcelテンプレートを生成"""
    data = {
        '塾ID': ['100001', '100002', '100003'],
        '塾名': ['サンプル塾A', 'サンプル塾B', 'サンプル塾C'],
        '担当者名': ['田中太郎', '佐藤花子', '鈴木次郎'],
        'メールアドレス': ['admin@jukua.com', 'admin@jukub.com', 'admin@jukuc.com'],
        '電話番号': ['03-1234-5678', '03-8765-4321', '03-1111-2222'],
        '住所': ['東京都渋谷区サンプル1-1-1', '東京都新宿区サンプル2-2-2', '東京都千代田区サンプル3-3-3']
    }
    
    df = pd.DataFrame(data)
    return df

def export_student_template():
    """生徒登録用のExcelテンプレートを生成"""
    data = {
        '生徒名': ['田中太郎', '佐藤花子', '鈴木次郎'],
        '学年': ['小学4年', '小学5年', '小学6年'],
        'メールアドレス': ['tanaka@example.com', 'sato@example.com', 'suzuki@example.com']
    }
    
    df = pd.DataFrame(data)
    return df