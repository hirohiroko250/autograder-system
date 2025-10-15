import pandas as pd
from django.core.exceptions import ValidationError
from .models import Student
from classrooms.models import Classroom
from django.db import transaction
import random
import string

def generate_student_id(classroom):
    """生徒IDを生成（教室ID + 連番3桁）"""
    existing_students = Student.objects.filter(classroom=classroom).count()
    next_number = existing_students + 1
    return f"{classroom.classroom_id}{next_number:03d}"

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
                    student_id = generate_student_id(classroom)
                    
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

def export_student_template():
    """生徒登録用のExcelテンプレートを生成"""
    data = {
        '生徒名': ['田中太郎', '佐藤花子', '鈴木次郎'],
        '学年': ['小学4年', '小学5年', '小学6年'],
        'メールアドレス': ['tanaka@example.com', 'sato@example.com', 'suzuki@example.com']
    }
    
    df = pd.DataFrame(data)
    return df

def import_students_by_school_from_excel(file_path, school_id):
    """
    Excelファイルから塾全体の生徒情報を一括インポート
    
    必要な列:
    - 教室ID (classroom_id)
    - 生徒名 (name)
    - 学年 (grade)
    - メールアドレス (email) - オプション
    """
    try:
        df = pd.read_excel(file_path)
        
        # 必要な列をチェック
        required_columns = ['教室ID', '生徒名', '学年']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(f"必要な列が不足しています: {', '.join(missing_columns)}")
        
        created_students = []
        errors = []
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # 教室の存在確認
                    classroom_id = str(row['教室ID'])
                    try:
                        classroom = Classroom.objects.get(
                            classroom_id=classroom_id, 
                            school__school_id=school_id
                        )
                    except Classroom.DoesNotExist:
                        errors.append(f"行{index + 2}: 教室ID {classroom_id} が見つかりません")
                        continue
                    
                    # 生徒IDを生成
                    student_id = generate_student_id(classroom)
                    
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
                    'grade': student.grade,
                    'classroom_id': student.classroom.classroom_id
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

def export_students_by_school_template():
    """塾全体の生徒登録用Excelテンプレートを生成"""
    data = {
        '教室ID': ['10000101', '10000101', '10000102'],
        '生徒名': ['田中太郎', '佐藤花子', '鈴木次郎'],
        '学年': ['小学4年', '小学5年', '小学6年'],
        'メールアドレス': ['tanaka@example.com', 'sato@example.com', 'suzuki@example.com']
    }
    
    df = pd.DataFrame(data)
    return df