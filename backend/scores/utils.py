from django.db.models import Sum, Count, Q
from .models import Score, TestResult, CommentTemplate
from schools.models import School
from students.models import Student
from tests.models import TestDefinition, QuestionGroup
import pandas as pd
from django.core.exceptions import ValidationError
from django.db import transaction

def calculate_test_results(student, test, force_temporary=False):
    """学生のテスト結果を計算"""
    from django.utils import timezone
    
    # スコアの合計を計算
    scores = Score.objects.filter(student=student, test=test)
    total_score = scores.aggregate(total=Sum('score'))['total'] or 0
    
    # 正答率を計算
    max_possible_score = test.max_score
    correct_rate = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
    
    # 締切状況を確認
    is_deadline_passed = timezone.now() > test.schedule.deadline_at
    is_final_calculation = is_deadline_passed and not force_temporary
    
    # 順位計算
    school_rank, school_total = calculate_school_rank_enhanced(student, test, total_score, is_final_calculation)
    national_rank, national_total = calculate_national_rank_enhanced(test, total_score, is_final_calculation)
    
    # コメント生成
    comment = generate_comment(student.classroom.school, test.subject, total_score)
    
    # TestResultを作成または更新
    defaults = {
        'total_score': total_score,
        'correct_rate': correct_rate,
        'comment': comment,
    }
    
    if is_final_calculation:
        # 確定後の順位更新
        defaults.update({
            'school_rank_final': school_rank,
            'national_rank_final': national_rank,
            'school_total_final': school_total,
            'national_total_final': national_total,
            'is_rank_finalized': True,
            'rank_finalized_at': timezone.now(),
        })
    else:
        # 一時的な順位更新
        defaults.update({
            'school_rank_temporary': school_rank,
            'national_rank_temporary': national_rank,
            'school_total_temporary': school_total,
            'national_total_temporary': national_total,
        })
    
    result, created = TestResult.objects.update_or_create(
        student=student,
        test=test,
        defaults=defaults
    )
    
    return result

def calculate_school_rank_enhanced(student, test, total_score, is_final=False):
    """塾内順位を計算（拡張版：一時的・確定後に対応）"""
    school = student.classroom.school
    
    # 同じ塾の学生のテスト結果を取得
    school_results = TestResult.objects.filter(
        test=test,
        student__classroom__school=school
    ).exclude(student=student).order_by('-total_score')
    
    # 順位計算（同点の場合は同順位）
    rank = 1
    for result in school_results:
        if result.total_score > total_score:
            rank += 1
    
    total_participants = school_results.count() + 1  # 自分を含める
    
    return rank, total_participants

def calculate_school_rank(student, test, total_score):
    """塾内順位を計算（後方互換性のため維持）"""
    return calculate_school_rank_enhanced(student, test, total_score, is_final=False)

def calculate_national_rank_enhanced(test, total_score, is_final=False):
    """全国順位を計算（拡張版：一時的・確定後に対応）"""
    
    # 全国のテスト結果を取得
    national_results = TestResult.objects.filter(
        test=test
    ).order_by('-total_score')
    
    # 順位計算（同点の場合は同順位）
    rank = 1
    for result in national_results:
        if result.total_score > total_score:
            rank += 1
    
    total_participants = national_results.count() + 1  # 自分を含める（新規の場合）
    
    # 既存の結果がある場合は参加者数を調整
    existing_count = national_results.filter(total_score=total_score).count()
    if existing_count > 0:
        total_participants = national_results.count()
    
    return rank, total_participants

def calculate_national_rank(test, total_score):
    """全国順位を計算（後方互換性のため維持）"""
    return calculate_national_rank_enhanced(test, total_score, is_final=False)

def calculate_grade_rank_enhanced(student, test, total_score, is_final=False):
    """学年順位を計算（拡張版：一時的・確定後に対応）"""
    
    # 同じ学年のテスト結果を取得
    grade_results = TestResult.objects.filter(
        test=test,
        student__grade=student.grade
    ).order_by('-total_score')
    
    # 順位計算（同点の場合は同順位）
    rank = 1
    for result in grade_results:
        if result.total_score > total_score:
            rank += 1
    
    total_participants = grade_results.count() + 1  # 自分を含める（新規の場合）
    
    # 既存の結果がある場合は参加者数を調整
    existing_count = grade_results.filter(total_score=total_score).count()
    if existing_count > 0:
        total_participants = grade_results.count()
    
    return rank, total_participants

def calculate_grade_rank(student, test, total_score):
    """学年順位を計算"""
    return calculate_grade_rank_enhanced(student, test, total_score, is_final=False)

def convert_student_grade_to_test_grade_level(student_grade):
    """学生の学年文字列をTestDefinitionのgrade_levelに変換"""
    if not student_grade:
        return None
    
    try:
        # 数字のみの場合
        grade_num = int(student_grade)
        if 1 <= grade_num <= 6:
            return f'elementary_{grade_num}'
        elif grade_num == 7:
            return 'middle_1'
        elif grade_num == 8:
            return 'middle_2'
        elif grade_num == 9:
            return 'middle_3'
    except (ValueError, TypeError):
        # 数字変換に失敗した場合、文字列から判定
        if '小' in student_grade:
            try:
                grade_num = int(student_grade.replace('小', '').replace('年', '').replace('生', ''))
                if 1 <= grade_num <= 6:
                    return f'elementary_{grade_num}'
            except:
                pass
        elif '中' in student_grade:
            try:
                grade_num = int(student_grade.replace('中', '').replace('年', '').replace('生', ''))
                if 1 <= grade_num <= 3:
                    return f'middle_{grade_num}'
            except:
                pass
    
    return None

def calculate_grade_statistics(student, test):
    """学年ごとの統計情報（平均点・偏差値）を計算"""
    import numpy as np
    from django.db.models import Avg
    
    # 同じ学年のテスト結果を取得
    grade_results = TestResult.objects.filter(
        test=test,
        student__grade=student.grade
    )
    
    if not grade_results.exists():
        return {
            'average': 0,
            'deviation_score': 50,  # デフォルト偏差値
            'participant_count': 0
        }
    
    # 平均点計算
    average = grade_results.aggregate(Avg('total_score'))['total_score__avg'] or 0
    
    # 偏差値計算用のスコアリスト取得
    scores = list(grade_results.values_list('total_score', flat=True))
    
    if len(scores) <= 1:
        deviation_score = 50  # 1人以下の場合はデフォルト偏差値
    else:
        scores_array = np.array(scores)
        mean_score = np.mean(scores_array)
        std_score = np.std(scores_array, ddof=1)  # 標本標準偏差
        
        if std_score == 0:
            deviation_score = 50  # 標準偏差が0の場合はデフォルト偏差値
        else:
            # 学生の成績を取得
            student_result = grade_results.filter(student=student).first()
            if student_result:
                student_score = student_result.total_score
                deviation_score = 50 + (student_score - mean_score) / std_score * 10
            else:
                deviation_score = 50
    
    return {
        'average': round(average, 1),
        'deviation_score': round(deviation_score, 1),
        'participant_count': len(scores)
    }

def generate_comment(school, subject, score):
    """点数に応じたコメントを生成"""
    # まず塾専用のコメントテンプレートを探す
    template = CommentTemplate.objects.filter(
        school=school,
        subject=subject,
        score_range_min__lte=score,
        score_range_max__gte=score,
        is_active=True
    ).first()
    
    # 塾専用がない場合はデフォルトテンプレートを使用
    if not template:
        template = CommentTemplate.objects.filter(
            school=None,
            subject=subject,
            score_range_min__lte=score,
            score_range_max__gte=score,
            is_active=True,
            is_default=True
        ).first()
    
    return template.template_text if template else "よく頑張りました。"

# SchoolStatistics機能は削除されました

def bulk_calculate_test_results(test, force_create=False):
    """指定されたテストの全学生の結果を一括計算（改善版）"""
    from django.utils import timezone
    from django.db import transaction
    from students.models import Student
    
    print(f"=== 一括集計開始: {test} ===")
    
    # 点数が入力されている学生を取得
    students_with_scores = Score.objects.filter(test=test).values_list('student', flat=True).distinct()
    
    # 各学生の合計点を計算
    student_totals = []
    
    with transaction.atomic():
        for student_id in students_with_scores:
            student = Student.objects.get(id=student_id)
            
            # 各学生の合計点を計算
            scores = Score.objects.filter(student=student, test=test)
            total_score = scores.aggregate(total=Sum('score'))['total'] or 0
            
            # 正答率を計算
            max_possible_score = test.max_score
            correct_rate = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
            
            student_totals.append({
                'student': student,
                'total_score': total_score,
                'correct_rate': correct_rate
            })
            
            print(f"学生: {student.name} - 合計点: {total_score}")
        
        # 合計点でソート（降順）
        student_totals.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 全国順位を計算
        print("=== 全国順位計算 ===")
        national_ranks = calculate_bulk_national_ranks(student_totals)
        
        # 塾別順位を計算
        print("=== 塾別順位計算 ===")
        school_ranks = calculate_bulk_school_ranks(student_totals)
        
        # 平均点を計算
        total_scores = [item['total_score'] for item in student_totals]
        average_score = sum(total_scores) / len(total_scores) if total_scores else 0
        print(f"全体平均点: {average_score:.1f}")
        
        # 締切状況を確認
        is_deadline_passed = timezone.now() > test.schedule.deadline_at
        is_final_calculation = is_deadline_passed
        
        # TestResultを更新
        results = []
        for i, item in enumerate(student_totals):
            student = item['student']
            total_score = item['total_score']
            correct_rate = item['correct_rate']
            
            # 全国順位と塾内順位を取得
            national_rank = national_ranks.get(student.id, len(student_totals))
            school_rank = school_ranks.get(student.id, 1)
            
            # コメント生成
            comment = generate_comment(student.classroom.school, test.subject, total_score)
            
            # TestResultを作成または更新
            defaults = {
                'total_score': total_score,
                'correct_rate': correct_rate,
                'comment': comment,
            }
            
            if is_final_calculation:
                # 確定後の順位更新
                defaults.update({
                    'school_rank_final': school_rank,
                    'national_rank_final': national_rank,
                    'school_total_final': len([s for s in student_totals if s['student'].classroom.school == student.classroom.school]),
                    'national_total_final': len(student_totals),
                    'is_rank_finalized': True,
                    'rank_finalized_at': timezone.now(),
                })
            else:
                # 一時的な順位更新
                defaults.update({
                    'school_rank_temporary': school_rank,
                    'national_rank_temporary': national_rank,
                    'school_total_temporary': len([s for s in student_totals if s['student'].classroom.school == student.classroom.school]),
                    'national_total_temporary': len(student_totals),
                })
            
            result, created = TestResult.objects.update_or_create(
                student=student,
                test=test,
                defaults=defaults
            )
            
            results.append(result)
            print(f"更新: {student.name} - 全国順位: {national_rank}/{len(student_totals)}, 塾内順位: {school_rank}")
        
        print(f"=== 一括集計完了: {len(results)}件 ===")
        return results

def calculate_bulk_national_ranks(student_totals):
    """全国順位を一括計算"""
    ranks = {}
    current_rank = 1
    
    for i, item in enumerate(student_totals):
        student = item['student']
        total_score = item['total_score']
        
        # 前の学生より点数が低い場合、順位を更新
        if i > 0 and student_totals[i-1]['total_score'] > total_score:
            current_rank = i + 1
        
        ranks[student.id] = current_rank
    
    return ranks

def calculate_bulk_school_ranks(student_totals):
    """塾別順位を一括計算"""
    # 塾ごとに学生をグループ化
    schools_data = {}
    
    for item in student_totals:
        student = item['student']
        school = student.classroom.school
        
        if school.id not in schools_data:
            schools_data[school.id] = []
        
        schools_data[school.id].append(item)
    
    # 各塾内での順位を計算
    school_ranks = {}
    
    for school_id, school_students in schools_data.items():
        # 塾内で合計点順にソート（降順）
        school_students.sort(key=lambda x: x['total_score'], reverse=True)
        
        current_rank = 1
        for i, item in enumerate(school_students):
            student = item['student']
            total_score = item['total_score']
            
            # 前の学生より点数が低い場合、順位を更新
            if i > 0 and school_students[i-1]['total_score'] > total_score:
                current_rank = i + 1
            
            school_ranks[student.id] = current_rank
            print(f"塾内順位: {student.name} - {current_rank}位 (点数: {total_score})")
    
    return school_ranks

def get_test_template_structure(year, period, subject, grade_level=None):
    """
    指定された年度・時期・科目・学年のテスト構造を取得
    """
    try:
        query = TestDefinition.objects.filter(
            schedule__year=year,
            schedule__period=period,
            subject=subject
        )
        
        if grade_level:
            query = query.filter(grade_level=grade_level)
        
        test = query.first()
        
        if not test:
            return None
            
        question_groups = QuestionGroup.objects.filter(test=test).order_by('group_number')
        
        structure = {
            'test': test,
            'question_groups': []
        }
        
        for group in question_groups:
            structure['question_groups'].append({
                'id': group.id,
                'group_number': group.group_number,
                'title': group.title,
                'max_score': group.max_score,
                'questions_count': group.questions.count()
            })
        
        return structure
        
    except Exception as e:
        return None

def generate_score_template(year, period, subject, grade_level=None):
    """
    指定された年度・時期・科目・学年の得点入力用テンプレートを生成
    生徒登録と同様の形式（塾ID・塾名・教室ID・教室名・生徒ID・生徒名・学年・年度・時期）に統一
    """
    structure = get_test_template_structure(year, period, subject, grade_level)
    
    if not structure:
        period_display = {'spring': '春季', 'summer': '夏季', 'winter': '冬季'}.get(period, period)
        subject_display = {'japanese': '国語', 'math': '算数', 'english': '英語', 'mathematics': '数学'}.get(subject, subject)
        grade_display = {'elementary': '小学生', 'middle_school': '中学生'}.get(grade_level, grade_level) if grade_level else ''
        raise ValidationError(f"{year}年度{period_display}{grade_display}{subject_display}テストが見つかりません")
    
    # 基本情報列（生徒登録と同じ形式）
    columns = [
        '塾ID', '塾名', '教室ID', '教室名', 
        '生徒ID', '生徒名', '学年', '年度', '期間',
        '出席'  # 出席状況
    ]
    
    # 大問ごとの列を追加
    for group in structure['question_groups']:
        column_name = f"大問{group['group_number']}"
        columns.append(column_name)
    
    # 合計点列
    columns.append('合計点')
    
    # サンプルデータ
    sample_data = {col: [] for col in columns}
    
    # 期間表示を変換
    period_display_jp = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}.get(period, period)
    
    # サンプル行を3つ作成
    sample_names = ['田中太郎', '佐藤花子', '鈴木次郎']
    sample_grades = ['小6', '小5', '中1']
    
    for i in range(3):
        sample_data['塾ID'].append('100001')
        sample_data['塾名'].append('サンプル学習塾')
        sample_data['教室ID'].append('001001')
        sample_data['教室名'].append('メイン教室')
        sample_data['生徒ID'].append(f'{123456 + i}')
        sample_data['生徒名'].append(sample_names[i])
        sample_data['学年'].append(sample_grades[i])
        sample_data['年度'].append(str(year))
        sample_data['期間'].append(period_display_jp)
        sample_data['出席'].append('出席')
        
        total = 0
        for group in structure['question_groups']:
            # サンプル点数（満点から徐々に減らす）
            score = max(0, group['max_score'] - i * 2)
            column_name = f"大問{group['group_number']}"
            sample_data[column_name].append(score)
            total += score
        
        sample_data['合計点'].append(total)
    
    # 空行を追加（データ入力用）
    for _ in range(3):
        for col in columns:
            if col in ['年度', '期間']:
                sample_data[col].append(str(year) if col == '年度' else period_display_jp)
            else:
                sample_data[col].append('')
    
    df = pd.DataFrame(sample_data)
    return df, structure

def generate_individual_report_template(student_id, year, period, format_type='word'):
    """
    個別成績表帳票生成
    A3サイズの美しいデザイン（Word/HTMLテンプレート対応）
    """
    try:
        from students.models import StudentEnrollment
        from tests.models import TestDefinition, TestSchedule
        # CommentTemplateはscores.modelsに移動済み
        from django.db.models import Avg
        import tempfile
        import os
        from datetime import datetime
        from docx import Document
        from docx.shared import Inches, Cm, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml.shared import OxmlElement, qn
        from docx.shared import RGBColor
        
        # 生徒情報取得
        print(f"生徒情報検索: student_id={student_id}, year={year}, period={period}")
        try:
            student_enrollment = StudentEnrollment.objects.get(
                student__student_id=student_id,
                year=year,
                period=period,
                is_active=True
            )
            student = student_enrollment.student
            print(f"生徒情報取得成功: {student.name}")
        except StudentEnrollment.DoesNotExist:
            print(f"生徒受講情報が見つかりません: {student_id}")
            return {
                'success': False,
                'error': f'生徒ID {student_id} の{year}年度{period}期の受講情報が見つかりません'
            }
        
        # 学年に応じた教科を決定
        grade = student.grade
        
        # 数字だけの場合は小学生として扱う
        is_elementary = grade.startswith('小') or (isinstance(grade, str) and grade.isdigit())
        
        if is_elementary:
            subjects = ['japanese', 'math']  # 国語、算数
            subject_names = {'japanese': '国語', 'math': '算数'}
        else:
            subjects = ['english', 'mathematics']  # 英語、数学
            subject_names = {'english': '英語', 'mathematics': '数学'}
        
        # テストスケジュール取得
        try:
            schedule = TestSchedule.objects.get(year=year, period=period)
        except TestSchedule.DoesNotExist:
            return {
                'success': False,
                'error': f'{year}年度{period}期のテストスケジュールが見つかりません'
            }
        
        # 各教科のテスト結果と統計を取得
        report_data = {
            'student_info': {
                'name': student.name,
                'id': student.student_id,
                'grade': student.grade,
                'school_name': student.classroom.school.name if student.classroom and student.classroom.school else '不明',
                'classroom_name': student.classroom.name if student.classroom else '不明'
            },
            'test_info': {
                'year': year,
                'period': period,
                'date': schedule.actual_date or schedule.planned_date
            },
            'subjects': {},
            'subject_results': {},
            'combined_results': {
                'total_score': 0,
                'grade_rank': '-',
                'grade_total': '-',
                'school_rank': '-',
                'school_total': '-'
            }
        }
        
        for subject in subjects:
            # 実際にスコアが記録されているテストを取得（学年に関係なく）
            student_tests_with_scores = Score.objects.filter(
                student=student,
                test__schedule=schedule,
                test__subject=subject
            ).select_related('test').values_list('test', flat=True).distinct()
            
            if not student_tests_with_scores:
                # スコアが記録されていない場合は、学年に応じたテストを試す
                # 学年に応じてTestDefinitionを検索
                grade_level_filter = convert_student_grade_to_test_grade_level(student.grade)
                
                if grade_level_filter:
                    test_def = TestDefinition.objects.filter(
                        schedule=schedule,
                        subject=subject,
                        grade_level=grade_level_filter
                    ).first()
                else:
                    # フォールバック：小学生/中学生で大きく分ける
                    test_def = TestDefinition.objects.filter(
                        schedule=schedule,
                        subject=subject,
                        grade_level__startswith='elementary_' if is_elementary else 'middle_'
                    ).first()
                
                if not test_def:
                    continue
            else:
                # 最初に見つかったテストを使用（通常は1つのテストのみ）
                test_def = TestDefinition.objects.get(id=student_tests_with_scores[0])
            
            # 生徒の得点取得
            student_scores = Score.objects.filter(
                student=student,
                test=test_def
            ).select_related('question_group')
            
            # テスト定義から全ての大問を取得（0点の問題も含める）
            all_question_groups = test_def.question_groups.all().order_by('group_number')
            question_scores = []
            total_score = 0
            
            for question_group in all_question_groups:
                # 生徒の得点を検索
                student_score_obj = student_scores.filter(question_group=question_group).first()
                score = student_score_obj.score if student_score_obj else 0
                
                question_scores.append({
                    'question_number': question_group.group_number,
                    'title': question_group.title,
                    'score': score,
                    'max_score': question_group.max_score
                })
                total_score += score or 0
            
            # 全国統計計算
            all_students = Score.objects.filter(test=test_def).values('student').distinct()
            all_scores = []
            for student_data in all_students:
                student_total = Score.objects.filter(
                    test=test_def,
                    student_id=student_data['student']
                ).aggregate(total=Sum('score'))['total'] or 0
                all_scores.append(student_total)
            
            # 学年順位計算（全国を学年別に修正）
            grade_scores = []
            grade_students = Score.objects.filter(
                test=test_def,
                student__grade=student.grade
            ).values('student').distinct()
            
            for grade_student_data in grade_students:
                grade_student_total = Score.objects.filter(
                    test=test_def,
                    student_id=grade_student_data['student']
                ).aggregate(total=Sum('score'))['total'] or 0
                grade_scores.append(grade_student_total)
            
            grade_scores.sort(reverse=True)
            grade_rank = grade_scores.index(total_score) + 1 if total_score in grade_scores else len(grade_scores)
            grade_total = len(grade_scores)
            
            # 全国順位計算（参考用）
            all_scores.sort(reverse=True)
            national_rank = all_scores.index(total_score) + 1 if total_score in all_scores else len(all_scores)
            
            # 塾内順位計算
            school_scores = []
            school_students = Score.objects.filter(
                test=test_def,
                student__classroom__school=student.classroom.school
            ).values('student').distinct()
            
            for school_student_data in school_students:
                school_student_total = Score.objects.filter(
                    test=test_def,
                    student_id=school_student_data['student']
                ).aggregate(total=Sum('score'))['total'] or 0
                school_scores.append(school_student_total)
            
            school_scores.sort(reverse=True)
            school_rank = school_scores.index(total_score) + 1 if total_score in school_scores else len(school_scores)
            school_total = len(school_scores)
            
            # 平均点計算
            grade_average = sum(grade_scores) / len(grade_scores) if grade_scores else 0
            school_average = sum(school_scores) / len(school_scores) if school_scores else 0
            
            # 偏差値計算
            import statistics
            grade_deviation = 50.0     # デフォルト偏差値（学年）
            school_deviation = 50.0    # デフォルト偏差値（塾内）
            
            if len(grade_scores) > 1:
                try:
                    std_dev = statistics.stdev(grade_scores)
                    if std_dev > 0:
                        grade_deviation = 50 + (total_score - grade_average) / std_dev * 10
                        grade_deviation = max(25, min(75, grade_deviation))  # 25-75の範囲に制限
                except:
                    grade_deviation = 50.0
            
            if len(school_scores) > 1:
                try:
                    school_std_dev = statistics.stdev(school_scores)
                    if school_std_dev > 0:
                        school_deviation = 50 + (total_score - school_average) / school_std_dev * 10
                        school_deviation = max(25, min(75, school_deviation))  # 25-75の範囲に制限
                except:
                    school_deviation = 50.0
            
            # 大問別平均点
            question_averages = []
            for q_score in question_scores:
                q_avg = Score.objects.filter(
                    test=test_def,
                    question_group__group_number=q_score['question_number']
                ).aggregate(avg=Avg('score'))['avg'] or 0
                question_averages.append({
                    'question_number': q_score['question_number'],
                    'average': round(q_avg, 1)
                })
            
            # コメント取得・生成
            try:
                # TestResultからコメントを取得
                test_result = TestResult.objects.filter(student=student, test=test_def).first()
                if test_result and test_result.comment:
                    comment = test_result.comment
                else:
                    # スコアに基づいたコメント生成
                    score_percentage = (total_score / test_def.max_score * 100) if test_def.max_score > 0 else 0
                    if score_percentage >= 90:
                        comment = f"素晴らしい成績です。{subject_names[subject]}での理解度が非常に高く、継続した努力の成果が現れています。"
                    elif score_percentage >= 80:
                        comment = f"よく頑張りました。{subject_names[subject]}の基礎は身についています。さらなる向上を目指しましょう。"
                    elif score_percentage >= 70:
                        comment = f"{subject_names[subject]}の基本的な内容は理解できています。苦手分野の復習に重点を置きましょう。"
                    elif score_percentage >= 60:
                        comment = f"{subject_names[subject]}の基礎固めが重要です。復習を重ね、理解を深めていきましょう。"
                    else:
                        comment = f"{subject_names[subject]}の基本から丁寧に復習し、一歩ずつ理解を深めていきましょう。"
            except:
                comment = "よく頑張りました。継続して学習を続けましょう。"
            
            report_data['subjects'][subject] = {
                'name': subject_names[subject],
                'total_score': total_score,
                'max_score': test_def.max_score,
                'average_score': round(grade_average, 1),
                'school_average': round(school_average, 1),
                'grade_rank': grade_rank,
                'grade_total': grade_total,
                'school_rank': school_rank,
                'school_total': school_total,
                'grade_deviation': round(grade_deviation, 1),
                'school_deviation': round(school_deviation, 1),
                'question_scores': question_scores,
                'question_averages': question_averages,
                'comment': comment
            }
            
            # PDF用のsubject_resultsにも追加
            report_data['subject_results'][subject_names[subject]] = {
                'total_score': total_score,
                'rankings': {
                    'grade_rank': grade_rank,
                    'school_rank': school_rank
                },
                'comment': comment
            }
            
            # 合計点を累積
            report_data['combined_results']['total_score'] += total_score
        
        # 合計成績の順位計算
        if report_data['combined_results']['total_score'] > 0:
            # 国語と算数の合計で全体順位を計算
            combined_total = report_data['combined_results']['total_score']
            
            # 全体の順位情報をsubjectsから取得
            total_national_rank = 1
            total_school_rank = 1
            total_students = 1
            total_school_students = 1
            
            if 'japanese' in report_data['subjects'] and 'math' in report_data['subjects']:
                # 簡易的に国語と算数の平均順位を使用（学年順位）
                jp_rank = report_data['subjects']['japanese']['grade_rank']
                math_rank = report_data['subjects']['math']['grade_rank']
                total_national_rank = int((jp_rank + math_rank) / 2)
                
                jp_school_rank = report_data['subjects']['japanese']['school_rank']
                math_school_rank = report_data['subjects']['math']['school_rank']
                total_school_rank = int((jp_school_rank + math_school_rank) / 2)
                
                total_students = max(
                    report_data['subjects']['japanese']['grade_total'],
                    report_data['subjects']['math']['grade_total']
                )
                total_school_students = max(
                    report_data['subjects']['japanese']['school_total'],
                    report_data['subjects']['math']['school_total']
                )
            
            report_data['combined_results'].update({
                'grade_rank': total_national_rank,
                'grade_total': total_students,
                'school_rank': total_school_rank,
                'school_total': total_school_students
            })
        
        # レポート生成処理を実行
        
        # 帳票ファイル生成
        if format_type == 'pdf':
            result = create_beautiful_pdf_report(report_data)
            return result
        elif format_type in ['word', 'a4_portrait']:
            file_path = create_a4_portrait_report(report_data)
            file_extension = '.docx'
        else:
            file_path = generate_excel_report(report_data)
            file_extension = '.xlsx'
        
        # ファイル名生成
        from datetime import datetime
        filename = f"{student.name}_成績表_{year}年度{period}期{file_extension}"
        
        return {
            'success': True,
            'download_url': f'/media/reports/{os.path.basename(file_path)}',
            'filename': filename,
            'student_name': student.name,
            'file_path': file_path  # デバッグ用
        }
        
    except Exception as e:
        print(f"個別帳票生成エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def create_a4_portrait_report(report_data):
    """
    A4縦向きの成績表レポートを生成（グラフ付き）
    """
    try:
        import tempfile
        import os
        from datetime import datetime
        try:
            from docx import Document
            from docx.shared import Inches, Cm, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.enum.table import WD_TABLE_ALIGNMENT
            from docx.oxml.shared import OxmlElement, qn
            from docx.enum.section import WD_SECTION
            from docx.enum.section import WD_ORIENT
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # GUI不要のバックエンドを使用
        except ImportError as import_error:
            print(f"ライブラリのインポートエラー: {import_error}")
            return create_fallback_text_report(report_data)
        
        # 新しいドキュメントを作成
        doc = Document()
        
        # A4縦向きに設定（2枚に収めるため余白を小さく）
        section = doc.sections[0]
        section.orientation = WD_ORIENT.PORTRAIT
        section.page_width = Cm(21)   # A4縦向き幅
        section.page_height = Cm(29.7) # A4縦向き高さ
        section.left_margin = Cm(1.0)  # 左余白縮小
        section.right_margin = Cm(1.0) # 右余白縮小
        section.top_margin = Cm(1.0)   # 上余白縮小
        section.bottom_margin = Cm(1.0) # 下余白縮小
        
        # ヘッダー部分（コンパクト化）
        header = doc.add_heading('', level=0)
        header_run = header.runs[0] if header.runs else header.add_run()
        header_run.text = '個別成績表'
        header_run.font.size = Pt(18)  # サイズ縮小
        header_run.font.color.rgb = RGBColor(31, 73, 125)
        header_run.bold = True
        header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 生徒情報テーブル
        student_info = report_data['student_info']
        test_info = report_data['test_info']
        
        info_table = doc.add_table(rows=2, cols=4)
        info_table.style = 'Light Grid Accent 1'
        
        # ヘッダー行
        info_cells = info_table.rows[0].cells
        info_cells[0].text = '生徒氏名'
        info_cells[1].text = '生徒ID'
        info_cells[2].text = '学年・教室'
        info_cells[3].text = 'テスト実施日'
        
        # データ行
        data_cells = info_table.rows[1].cells
        data_cells[0].text = student_info['name']
        data_cells[1].text = student_info['id']
        data_cells[2].text = f"{student_info['grade']}年生 {student_info['classroom_name']}"
        data_cells[3].text = f"2025-07-15"  # テスト実施日
        
        # テーブルのスタイル設定
        for row in info_table.rows:
            for cell in row.cells:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(11)
        
        doc.add_paragraph()  # 空行
        
        # 科目別結果
        subjects = report_data.get('subjects', {})
        
        for subject_code, subject_data in subjects.items():
            if 'math' in subject_code.lower() or '算数' in subject_data.get('name', ''):
                # 算数のみ表示（小学生）
                create_a4_subject_section(doc, subject_data)
            elif subject_data.get('name') == '国語':
                # 国語も表示
                create_a4_subject_section(doc, subject_data)
        
        # 総合コメント欄
        doc.add_paragraph()
        comment_header = doc.add_heading('総合所見', level=2)
        comment_header.runs[0].font.color.rgb = RGBColor(31, 73, 125)
        comment_header.runs[0].font.size = Pt(14)
        
        # コメントテーブル
        comment_table = doc.add_table(rows=1, cols=1)
        comment_table.style = 'Light Grid Accent 1'
        comment_cell = comment_table.cell(0, 0)
        
        # 各科目のコメントを統合
        all_comments = []
        for subject_data in subjects.values():
            if subject_data.get('comment'):
                all_comments.append(f"【{subject_data['name']}】{subject_data['comment']}")
        
        comment_text = '\n\n'.join(all_comments) if all_comments else "よく頑張りました。引き続き学習を継続してください。"
        
        # コメントを段落として追加
        comment_paragraph = comment_cell.paragraphs[0]
        comment_run = comment_paragraph.add_run(comment_text)
        comment_run.font.size = Pt(10)
        comment_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        
        # フッター
        doc.add_paragraph()
        footer = doc.add_paragraph()
        footer_run = footer.add_run(f"作成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
        footer_run.font.size = Pt(9)
        footer_run.font.color.rgb = RGBColor(128, 128, 128)
        footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # ファイル保存
        from django.conf import settings
        media_reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(media_reports_dir, exist_ok=True)
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        file_path = os.path.join(media_reports_dir, filename)
        doc.save(file_path)
        
        import stat
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        
        print(f"A4縦向き帳票生成完了: {file_path}")
        return file_path
        
    except Exception as e:
        print(f"A4縦向き帳票生成エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        # フォールバック: 古い横向き形式を使用
        return create_beautiful_word_report(report_data)

def create_beautiful_word_report(report_data):
    """
    美しいデザインのWordレポートを生成
    A3横向きサイズで見やすいレイアウト
    """
    try:
        import tempfile
        import os
        from datetime import datetime
        try:
            from docx import Document
            from docx.shared import Inches, Cm, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.enum.table import WD_TABLE_ALIGNMENT
            from docx.oxml.shared import OxmlElement, qn
            from docx.enum.section import WD_SECTION
            from docx.enum.section import WD_ORIENT
        except ImportError as import_error:
            print(f"python-docxのインポートエラー: {import_error}")
            # フォールバック: 簡易的なテキストファイルを生成
            return create_fallback_text_report(report_data)
        
        # 新しいドキュメントを作成
        doc = Document()
        
        # A3横向きに設定
        section = doc.sections[0]
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = Cm(42)  # A3横向き幅
        section.page_height = Cm(29.7)  # A3横向き高さ
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        
        # ヘッダー部分
        header = doc.add_heading('', level=0)
        header_run = header.runs[0] if header.runs else header.add_run()
        header_run.text = '個別成績表'
        header_run.font.size = Pt(24)
        header_run.font.color.rgb = RGBColor(31, 73, 125)  # 濃い青色
        header_run.bold = True
        header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 生徒情報テーブル
        student_info = report_data['student_info']
        test_info = report_data['test_info']
        
        info_table = doc.add_table(rows=2, cols=4)
        info_table.style = 'Table Grid'
        info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # ヘッダー行
        info_cells = info_table.rows[0].cells
        info_cells[0].text = '生徒氏名'
        info_cells[1].text = '生徒ID'
        info_cells[2].text = '学年・教室'
        info_cells[3].text = 'テスト実施日'
        
        # データ行
        data_cells = info_table.rows[1].cells
        data_cells[0].text = student_info['name']
        data_cells[1].text = student_info['id']
        data_cells[2].text = f"{student_info['grade']} {student_info['classroom_name']}"
        data_cells[3].text = str(test_info.get('date', ''))
        
        # テーブルのスタイル設定
        for row in info_table.rows:
            for cell in row.cells:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(12)
        
        # ヘッダー行の背景色設定
        for cell in info_table.rows[0].cells:
            set_cell_background(cell, RGBColor(189, 215, 238))  # 薄い青色
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
        
        doc.add_paragraph()  # 空行
        
        # 科目別結果
        subjects = report_data.get('subjects', {})
        
        if subjects:
            # 科目を分類（左：算数/数学、右：国語/英語）
            math_subjects = []
            language_subjects = []
            
            for subject_code, subject_data in subjects.items():
                if 'math' in subject_code.lower() or '算数' in subject_data.get('name', '') or '数学' in subject_data.get('name', ''):
                    math_subjects.append((subject_code, subject_data))
                else:  # 国語、英語など
                    language_subjects.append((subject_code, subject_data))
            
            # メインテーブル（2列）
            main_table = doc.add_table(rows=1, cols=2)
            main_table.style = 'Table Grid'
            
            # テーブル幅を調整
            for column in main_table.columns:
                for cell in column.cells:
                    cell.width = Cm(18)  # 各列の幅を18cmに設定
            
            # 左側セル：算数/数学
            left_cell = main_table.cell(0, 0)
            left_paragraph = left_cell.paragraphs[0]
            left_run = left_paragraph.add_run('算数・数学')
            left_run.font.size = Pt(16)
            left_run.font.color.rgb = RGBColor(31, 73, 125)
            left_run.bold = True
            left_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            if math_subjects:
                for subject_code, subject_data in math_subjects:
                    create_subject_section(left_cell, subject_data)
            else:
                # 学年に応じたサンプルデータを表示
                student_info = report_data.get('student_info', {})
                grade = student_info.get('grade', '不明')
                is_elementary = grade.startswith('小') or grade.isdigit()
                
                sample_math_data = {
                    'name': f"{'算数' if is_elementary else '数学'}（{grade}）",
                    'total_score': '-',
                    'max_score': 100,
                    'average_score': '-',
                    'national_rank': '-',
                    'total_students': '-',
                    'comment': 'テスト結果データがありません。'
                }
                create_subject_section(left_cell, sample_math_data)
            
            # 右側セル：国語/英語
            right_cell = main_table.cell(0, 1)
            right_paragraph = right_cell.paragraphs[0]
            right_run = right_paragraph.add_run('国語・英語')
            right_run.font.size = Pt(16)
            right_run.font.color.rgb = RGBColor(31, 73, 125)
            right_run.bold = True
            right_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            if language_subjects:
                for subject_code, subject_data in language_subjects:
                    create_subject_section(right_cell, subject_data)
            else:
                # 学年に応じたサンプルデータを表示
                student_info = report_data.get('student_info', {})
                grade = student_info.get('grade', '不明')
                is_elementary = grade.startswith('小') or grade.isdigit()
                
                sample_language_data = {
                    'name': f"{'国語' if is_elementary else '英語'}（{grade}）",
                    'total_score': '-',
                    'max_score': 100,
                    'average_score': '-',
                    'national_rank': '-',
                    'total_students': '-',
                    'comment': 'テスト結果データがありません。'
                }
                create_subject_section(right_cell, sample_language_data)
            
            # セルの背景色を設定（薄いグレー）
            set_cell_background(left_cell, RGBColor(248, 248, 248))
            set_cell_background(right_cell, RGBColor(252, 252, 252))
        
        # 総合コメント欄
        doc.add_paragraph()
        comment_header = doc.add_heading('総合所見', level=2)
        comment_header.runs[0].font.color.rgb = RGBColor(31, 73, 125)
        
        # コメントボックス
        comment_table = doc.add_table(rows=1, cols=1)
        comment_table.style = 'Table Grid'
        comment_cell = comment_table.cell(0, 0)
        
        # セルに余白を設定
        comment_cell._tc.get_or_add_tcPr().append(
            OxmlElement('w:tcMar')
        )
        
        # 各科目のコメントを統合
        all_comments = []
        for subject_data in subjects.values():
            if subject_data.get('comment'):
                all_comments.append(f"【{subject_data['name']}】{subject_data['comment']}")
        
        comment_text = '\n\n'.join(all_comments) if all_comments else "よく頑張りました。引き続き学習を継続してください。"
        
        # コメントを段落として追加
        comment_paragraph = comment_cell.paragraphs[0]
        comment_run = comment_paragraph.add_run(comment_text)
        comment_run.font.size = Pt(11)
        comment_run.font.name = 'ＭＳ Ｐゴシック'  # 日本語フォント
        comment_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        
        # コメント欄の背景色を設定
        set_cell_background(comment_cell, RGBColor(252, 252, 252))  # 非常に薄いグレー
        
        # フッター
        doc.add_paragraph()
        footer = doc.add_paragraph()
        footer_run = footer.add_run(f"作成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
        footer_run.font.size = Pt(9)
        footer_run.font.color.rgb = RGBColor(128, 128, 128)
        footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # メディアディレクトリに保存
        from django.conf import settings
        
        media_reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(media_reports_dir, exist_ok=True)
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        file_path = os.path.join(media_reports_dir, filename)
        doc.save(file_path)
        
        # ファイル権限を設定（読み取り可能にする）
        import stat
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644
        
        print(f"Word帳票生成完了: {file_path}")
        
        return file_path
        
    except Exception as e:
        print(f"Word帳票生成エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e

# 既存のコードとの互換性のためのエイリアス
def generate_word_report(report_data):
    """既存コードとの互換性のため、新しい美しい帳票生成関数を呼び出す"""
    return create_beautiful_word_report(report_data)

def create_subject_section(cell, subject_data):
    """
    科目別セクションを作成
    """
    try:
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        # 科目名ヘッダー
        subject_header = cell.add_paragraph()
        subject_run = subject_header.add_run(subject_data['name'])
        subject_run.font.size = Pt(16)
        subject_run.font.bold = True
        subject_run.font.color.rgb = RGBColor(31, 73, 125)
        subject_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 得点サマリー
        summary_p = cell.add_paragraph()
        summary_run = summary_p.add_run(
            f"得点: {subject_data['total_score']}/{subject_data['max_score']}点 "
            f"(平均: {subject_data['average_score']}点)"
        )
        summary_run.font.size = Pt(14)
        summary_run.font.bold = True
        summary_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 順位情報
        rank_p = cell.add_paragraph()
        rank_run = rank_p.add_run(
            f"全国順位: {subject_data['national_rank']}/{subject_data['total_students']}位"
        )
        rank_run.font.size = Pt(12)
        rank_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 大問別詳細
        if subject_data.get('question_scores'):
            cell.add_paragraph()
            detail_header = cell.add_paragraph()
            detail_run = detail_header.add_run('大問別得点')
            detail_run.font.size = Pt(12)
            detail_run.font.bold = True
            detail_run.font.color.rgb = RGBColor(68, 114, 196)  # 青色
            
            # 大問別得点を表形式で表示
            question_table = cell.add_table(rows=len(subject_data['question_scores']) + 1, cols=3)
            question_table.style = 'Light Grid Accent 1'
            
            # ヘッダー行
            header_cells = question_table.rows[0].cells
            header_cells[0].text = '大問'
            header_cells[1].text = '得点'
            header_cells[2].text = '平均'
            
            for header_cell in header_cells:
                for paragraph in header_cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True
                        run.font.size = Pt(9)
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # データ行
            for i, q in enumerate(subject_data['question_scores']):
                # question_averagesはリスト形式なので、question_numberで検索
                q_avg = 0
                question_averages = subject_data.get('question_averages', [])
                for avg_data in question_averages:
                    if avg_data.get('question_number') == q['question_number']:
                        q_avg = avg_data.get('average', 0)
                        break
                
                data_cells = question_table.rows[i + 1].cells
                data_cells[0].text = f"{q.get('title', f'第{q['question_number']}問')}"
                data_cells[1].text = f"{q['score']}/{q['max_score']}"
                data_cells[2].text = f"{q_avg:.1f}"
                
                for data_cell in data_cells:
                    for paragraph in data_cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(9)
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
    except Exception as e:
        print(f"科目セクション作成エラー: {str(e)}")

def create_a4_subject_section(doc, subject_data):
    """
    A4縦向き用の科目別セクションを作成（グラフ付き）
    """
    try:
        from docx.shared import Pt, RGBColor, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        import numpy as np
        import os
        from django.conf import settings
        
        # 科目名ヘッダー（コンパクト化）
        subject_header = doc.add_heading(subject_data['name'], level=2)
        subject_header.runs[0].font.color.rgb = RGBColor(31, 73, 125)
        subject_header.runs[0].font.size = Pt(14)  # サイズ縮小
        
        # メイン統計テーブル
        stats_table = doc.add_table(rows=3, cols=4)
        stats_table.style = 'Light Grid Accent 1'
        
        # ヘッダー行
        headers = ['項目', '得点', '順位', '偏差値']
        for i, header in enumerate(headers):
            cell = stats_table.cell(0, i)
            cell.text = header
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in cell.paragraphs[0].runs:
                run.font.bold = True
                run.font.size = Pt(11)
        
        # 全国データ行
        row1_cells = stats_table.rows[1].cells
        row1_cells[0].text = '全国'
        row1_cells[1].text = f"{subject_data['total_score']}/{subject_data['max_score']}点 (平均{subject_data['average_score']}点)"
        row1_cells[2].text = f"{subject_data['national_rank']}/{subject_data['total_students']}位"
        row1_cells[3].text = f"{subject_data['national_deviation']}"
        
        # 塾内データ行
        row2_cells = stats_table.rows[2].cells
        row2_cells[0].text = '塾内'
        row2_cells[1].text = f"{subject_data['total_score']}/{subject_data['max_score']}点 (平均{subject_data['school_average']}点)"
        row2_cells[2].text = f"{subject_data['school_rank']}/{subject_data['school_total']}位"
        row2_cells[3].text = f"{subject_data['school_deviation']}"
        
        # テーブルの中央揃え
        for row in stats_table.rows[1:]:
            for cell in row.cells:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in cell.paragraphs[0].runs:
                    run.font.size = Pt(10)
        
        # 大問別詳細テーブル
        if subject_data.get('question_scores'):
            doc.add_paragraph()
            detail_header = doc.add_paragraph()
            detail_run = detail_header.add_run('大問別得点詳細')
            detail_run.font.size = Pt(11)  # サイズ縮小
            detail_run.font.bold = True
            detail_run.font.color.rgb = RGBColor(68, 114, 196)
            
            question_table = doc.add_table(rows=len(subject_data['question_scores']) + 1, cols=4)
            question_table.style = 'Light List Accent 1'
            
            # ヘッダー行
            q_headers = ['大問', 'タイトル', '得点', '平均点']
            for i, header in enumerate(q_headers):
                cell = question_table.cell(0, i)
                cell.text = header
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in cell.paragraphs[0].runs:
                    run.font.bold = True
                    run.font.size = Pt(10)
            
            # データ行
            for i, q in enumerate(subject_data['question_scores']):
                q_avg = 0
                question_averages = subject_data.get('question_averages', [])
                for avg_data in question_averages:
                    if avg_data.get('question_number') == q['question_number']:
                        q_avg = avg_data.get('average', 0)
                        break
                
                data_cells = question_table.rows[i + 1].cells
                data_cells[0].text = f"第{q['question_number']}問"
                data_cells[1].text = f"{q.get('title', '')}"
                data_cells[2].text = f"{q['score']}/{q['max_score']}"
                data_cells[3].text = f"{q_avg:.1f}"
                
                for cell in data_cells:
                    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in cell.paragraphs[0].runs:
                        run.font.size = Pt(9)
            
            # レーダーチャート生成（大問数に応じて）
            if len(subject_data['question_scores']) >= 3:
                create_radar_chart(doc, subject_data)
            
            # 棒グラフ生成
            create_bar_chart(doc, subject_data)
        
        doc.add_paragraph()  # 空行
        
    except Exception as e:
        print(f"A4科目セクション作成エラー: {str(e)}")
        import traceback
        traceback.print_exc()

def create_radar_chart(doc, subject_data):
    """
    大問別成績のレーダーチャートを生成してWordに挿入
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        import numpy as np
        import os
        from django.conf import settings
        from docx.shared import Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        # 日本語フォント設定
        matplotlib.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
        
        # データ準備
        questions = subject_data['question_scores']
        if len(questions) < 3:
            return
        
        categories = [f"大問{q['question_number']}" for q in questions]
        scores = [(q['score'] / q['max_score']) * 100 for q in questions]  # パーセンテージ化
        
        # 円形にするため最初の値を最後に追加
        scores += scores[:1]
        categories += categories[:1]
        
        # 角度計算
        N = len(categories) - 1
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        
        # グラフ作成
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
        ax.plot(angles, scores, 'o-', linewidth=2, label='得点率', color='#1f73b5')
        ax.fill(angles, scores, alpha=0.25, color='#1f73b5')
        
        # 軸設定
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories[:-1])
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'])
        ax.grid(True)
        
        # タイトル
        plt.title(f'{subject_data["name"]} 大問別成績レーダーチャート', size=12, color='#1f73b5', y=1.1)
        
        # 保存
        media_reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(media_reports_dir, exist_ok=True)
        chart_path = os.path.join(media_reports_dir, f'radar_{subject_data["name"]}_{np.random.randint(1000, 9999)}.png')
        
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        # Wordに挿入
        paragraph = doc.add_paragraph()
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
        run.add_picture(chart_path, width=Cm(10))  # チャートサイズ縮小
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 一時ファイル削除
        try:
            os.remove(chart_path)
        except:
            pass
            
    except Exception as e:
        print(f"レーダーチャート生成エラー: {str(e)}")

def create_bar_chart(doc, subject_data):
    """
    得点と平均点の比較棒グラフを生成してWordに挿入
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        import numpy as np
        import os
        from django.conf import settings
        from docx.shared import Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        # 日本語フォント設定
        matplotlib.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
        
        # データ準備
        categories = ['全国', '塾内']
        my_scores = [subject_data['total_score'], subject_data['total_score']]
        averages = [subject_data['average_score'], subject_data['school_average']]
        
        x = np.arange(len(categories))
        width = 0.35
        
        # グラフ作成
        fig, ax = plt.subplots(figsize=(8, 5))
        bars1 = ax.bar(x - width/2, my_scores, width, label='あなたの得点', color='#1f73b5')
        bars2 = ax.bar(x + width/2, averages, width, label='平均点', color='#ff7f0e')
        
        # 軸とラベル設定
        ax.set_xlabel('比較対象')
        ax.set_ylabel('得点')
        ax.set_title(f'{subject_data["name"]} 得点比較')
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 棒の上に数値表示
        for bar in bars1:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{height:.0f}', ha='center', va='bottom')
        
        for bar in bars2:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{height:.1f}', ha='center', va='bottom')
        
        # 保存
        media_reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(media_reports_dir, exist_ok=True)
        chart_path = os.path.join(media_reports_dir, f'bar_{subject_data["name"]}_{np.random.randint(1000, 9999)}.png')
        
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        # Wordに挿入
        paragraph = doc.add_paragraph()
        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
        run.add_picture(chart_path, width=Cm(12))  # チャートサイズ縮小
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 一時ファイル削除
        try:
            os.remove(chart_path)
        except:
            pass
            
    except Exception as e:
        print(f"棒グラフ生成エラー: {str(e)}")

def set_cell_background(cell, color):
    """
    セルの背景色を設定
    """
    # 背景色設定は複雑なため、現在はスキップ
    # 報告書の機能性に影響しないため、このままでOK
    pass

def create_beautiful_pdf_report(report_data):
    """
    美しいデザインのPDFレポートを生成 A3横向きサイズで見やすいレイアウト
    """
    try:
        import os
        from datetime import datetime
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A3, landscape
        from reportlab.lib.units import mm
        from reportlab.lib.colors import HexColor, Color
        from reportlab.pdfbase import pdfutils
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase import pdfmetrics
        from django.conf import settings
        
        # レポートディレクトリの作成
        media_root = getattr(settings, 'MEDIA_ROOT', '/tmp')
        reports_dir = os.path.join(media_root, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # ファイル名生成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'report_{timestamp}.pdf'
        file_path = os.path.join(reports_dir, filename)
        
        # A3横向きキャンバス作成
        page_width, page_height = landscape(A3)
        c = canvas.Canvas(file_path, pagesize=landscape(A3))
        
        # 日本語フォント設定（CIDフォントを使用）  
        japanese_font = 'Helvetica'  # デフォルトはHelvetica
        try:
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            # HeiseiKakuGo-W5フォント（日本語対応）
            pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
            japanese_font = 'HeiseiKakuGo-W5'
            print('HeiseiKakuGo-W5フォント登録成功')
        except Exception as e:
            print(f'日本語フォント登録失敗: {e}')
            try:
                from reportlab.pdfbase.cidfonts import UnicodeCIDFont
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
                japanese_font = 'HeiseiMin-W3'
                print('HeiseiMin-W3フォント登録成功')
            except Exception as e2:
                print(f'HeiseiMin-W3フォント登録失敗: {e2}')
                print('Helveticaフォントを使用')
        
        # カラーパレット
        primary_blue = HexColor('#1f497d')
        light_blue = HexColor('#bdd7ee')
        gray = HexColor('#808080')
        light_gray = HexColor('#f8f8f8')
        
        # データ抽出
        student_info = report_data.get('student_info', {})
        test_info = report_data.get('test_info', {})
        subject_results = report_data.get('subject_results', {})
        
        # デバッグ情報
        print(f'PDF生成データ確認:')
        print(f'  student_info: {student_info}')
        print(f'  test_info: {test_info}')
        print(f'  subject_results: {subject_results}')
        
        # ヘッダー
        c.setFont(japanese_font, 24)
        c.setFillColor(primary_blue)
        c.drawString(50*mm, page_height - 30*mm, '個別成績表')
        
        # 生徒情報
        y_pos = page_height - 50*mm
        c.setFont(japanese_font, 14)
        c.setFillColor(Color(0, 0, 0))
        
        student_info_list = [
            f"生徒名: {student_info.get('name', 'N/A')}",
            f"生徒ID: {student_info.get('id', 'N/A')}",
            f"学年: {student_info.get('grade', 'N/A')}",
            f"クラス: {student_info.get('classroom_name', 'N/A')}",
            f"テスト期間: {test_info.get('year', 'N/A')}年度 {test_info.get('period', 'N/A')}"
        ]
        
        for info in student_info_list:
            c.drawString(50*mm, y_pos, info)
            y_pos -= 8*mm
        
        # 科目別成績表（2列レイアウト）
        y_pos -= 10*mm
        c.setFont(japanese_font, 16)
        c.setFillColor(primary_blue)
        c.drawString(50*mm, y_pos, '科目別成績')
        
        y_pos -= 20*mm
        
        # 左右に分けて科目を表示
        left_x = 50*mm  # 左側（算数/数学）
        right_x = 220*mm  # 右側（国語/英語）
        column_width = 150*mm
        
        # 科目を分類
        math_subjects = []
        language_subjects = []
        
        if subject_results:
            for subject, data in subject_results.items():
                if '算数' in subject or '数学' in subject or 'math' in subject.lower():
                    math_subjects.append((subject, data))
                else:  # 国語、英語など
                    language_subjects.append((subject, data))
        
        # 左側：算数/数学
        c.setFont(japanese_font, 14)
        c.setFillColor(primary_blue)
        c.drawString(left_x, y_pos, '算数・数学')
        
        y_left = y_pos - 15*mm
        y_left = draw_subject_section(c, japanese_font, math_subjects, left_x, y_left, column_width, light_blue, light_gray, primary_blue)
        
        # 右側：国語/英語
        c.setFillColor(primary_blue)
        c.drawString(right_x, y_pos, '国語・英語')
        
        y_right = y_pos - 15*mm
        y_right = draw_subject_section(c, japanese_font, language_subjects, right_x, y_right, column_width, light_blue, light_gray, primary_blue)
        
        # Y座標を調整（両方のセクションが終わったところまで）
        y_pos = min(y_left, y_right) - 20*mm
        
        # 総合成績
        y_pos -= 10*mm
        c.setFont(japanese_font, 16)
        c.setFillColor(primary_blue)
        c.drawString(50*mm, y_pos, '総合成績')
        
        y_pos -= 15*mm
        c.setFont(japanese_font, 14)
        c.setFillColor(Color(0, 0, 0))
        
        combined_results = report_data.get('combined_results', {})
        total_info = [
            f"合計点: {combined_results.get('total_score', 'N/A')}点",
            f"学年順位: {combined_results.get('grade_rank', 'N/A')}位 / {combined_results.get('grade_total', 'N/A')}名",
            f"塾内順位: {combined_results.get('school_rank', 'N/A')}位 / {combined_results.get('school_total', 'N/A')}名"
        ]
        
        for info in total_info:
            c.drawString(50*mm, y_pos, info)
            y_pos -= 10*mm
        
        # フッター
        c.setFont(japanese_font, 10)
        c.setFillColor(gray)
        c.drawString(50*mm, 20*mm, f"作成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
        
        # PDF保存
        c.save()
        
        # ファイル権限設定
        os.chmod(file_path, 0o644)
        
        print(f"PDF帳票生成完了: {file_path}")
        
        return {
            'success': True,
            'download_url': f'/media/reports/{filename}',
            'filename': f"{student_info.get('name', 'report')}_{test_info.get('year', '')}年度{test_info.get('period', '')}.pdf",
            'student_name': student_info.get('name', 'N/A'),
            'file_path': file_path
        }
        
    except Exception as e:
        print(f"PDF帳票生成エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_fallback_text_report(report_data)

def create_fallback_text_report(report_data):
    """
    python-docxが利用できない場合のフォールバック
    シンプルなテキストファイルを生成
    """
    try:
        import tempfile
        import os
        from datetime import datetime
        from django.conf import settings
        
        # メディアディレクトリに保存
        media_reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(media_reports_dir, exist_ok=True)
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = os.path.join(media_reports_dir, filename)
        
        student_info = report_data['student_info']
        test_info = report_data['test_info']
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write("個別成績表\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"生徒氏名: {student_info['name']}\n")
            f.write(f"生徒ID: {student_info['id']}\n")
            f.write(f"学年・教室: {student_info['grade']} {student_info['classroom_name']}\n")
            f.write(f"テスト実施日: {test_info.get('date', '')}\n\n")
            
            subjects = report_data.get('subjects', {})
            for subject_code, subject_data in subjects.items():
                f.write("-" * 30 + "\n")
                f.write(f"{subject_data['name']}\n")
                f.write("-" * 30 + "\n")
                f.write(f"得点: {subject_data['total_score']}/{subject_data['max_score']}点\n")
                f.write(f"平均: {subject_data['average_score']}点\n")
                f.write(f"全国順位: {subject_data['national_rank']}/{subject_data['total_students']}位\n\n")
                
                if subject_data.get('question_scores'):
                    f.write("大問別得点:\n")
                    for q in subject_data['question_scores']:
                        q_avg = subject_data.get('question_averages', {}).get(q['question_number'], 0)
                        f.write(f"  大問{q['question_number']}: {q['score']}/{q['max_score']}点 (平均: {q_avg:.1f}点)\n")
                    f.write("\n")
                
                if subject_data.get('comment'):
                    f.write(f"コメント: {subject_data['comment']}\n\n")
            
            f.write(f"作成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}\n")
        
        return file_path
        
    except Exception as e:
        print(f"フォールバックレポート生成エラー: {str(e)}")
        raise e

def generate_bulk_reports_template(student_ids, year, period, format_type='word'):
    """
    一括成績表帳票生成
    複数の生徒の成績表をZIPファイルにまとめて生成
    """
    try:
        import zipfile
        import tempfile
        import os
        from datetime import datetime
        
        # 一時ディレクトリ作成
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f'成績表一括_{year}年度{period}期_{len(student_ids)}名.zip')
        
        generated_files = []
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for student_id in student_ids:
                # 各生徒の個別帳票を生成
                result = generate_individual_report_template(
                    student_id=student_id,
                    year=year,
                    period=period,
                    format_type=format_type
                )
                
                if result.get('success'):
                    # ZIPファイルに追加
                    from django.conf import settings
                    file_path = result['download_url'].replace('/media/reports/', '')
                    zipf.write(
                        os.path.join(settings.MEDIA_ROOT, 'reports', file_path),
                        result['filename']
                    )
                    generated_files.append(result['filename'])
        
        if not generated_files:
            return {
                'success': False,
                'error': '生成できた帳票がありませんでした'
            }
        
        return {
            'success': True,
            'download_url': f'/media/reports/{os.path.basename(zip_path)}',
            'filename': os.path.basename(zip_path),
            'generated_count': len(generated_files),
            'total_requested': len(student_ids)
        }
        
    except Exception as e:
        print(f"一括帳票生成エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def generate_word_report_old(report_data):
    """Word形式の成績表を生成（A3横向き二つ折り）"""
    try:
        from docx import Document
        from docx.shared import Inches, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        import tempfile
        import os
        
        # 新しいドキュメント作成
        doc = Document()
        
        # ページ設定（A3横向き）
        section = doc.sections[0]
        section.page_width = Inches(16.54)  # A3横
        section.page_height = Inches(11.69)  # A3縦
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        
        # タイトル
        title = doc.add_heading('全国学力診断テスト 成績表', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 生徒情報ヘッダー
        info_table = doc.add_table(rows=2, cols=4)
        info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # 生徒情報入力
        cells = info_table.rows[0].cells
        cells[0].text = f"氏名: {report_data['student_info']['name']}"
        cells[1].text = f"学年: {report_data['student_info']['grade']}"
        cells[2].text = f"学校: {report_data['student_info']['school_name']}"
        cells[3].text = f"クラス: {report_data['student_info']['classroom_name']}"
        
        cells = info_table.rows[1].cells
        cells[0].text = f"生徒ID: {report_data['student_info']['id']}"
        cells[1].text = f"実施年度: {report_data['test_info']['year']}年度"
        cells[2].text = f"実施期間: {report_data['test_info']['period']}"
        cells[3].text = f"実施日: {report_data['test_info']['date']}"
        
        doc.add_paragraph()  # 空行
        
        # 2列レイアウト用のテーブル（左右分割）
        main_table = doc.add_table(rows=1, cols=2)
        main_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # 左側と右側のセル
        left_cell = main_table.rows[0].cells[0]
        right_cell = main_table.rows[0].cells[1]
        
        # 教科データを左右に分割
        subjects_list = list(report_data['subjects'].items())
        
        # 左側（1つ目の教科）
        if len(subjects_list) > 0:
            subject_key, subject_data = subjects_list[0]
            add_subject_content(left_cell, subject_data)
        
        # 右側（2つ目の教科）
        if len(subjects_list) > 1:
            subject_key, subject_data = subjects_list[1]
            add_subject_content(right_cell, subject_data)
        
        # ファイル保存
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc.save(temp_file.name)
        temp_file.close()
        
        # メディアディレクトリに移動
        from django.conf import settings
        from datetime import datetime
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        final_path = os.path.join(reports_dir, f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx')
        os.rename(temp_file.name, final_path)
        
        return final_path
        
    except Exception as e:
        print(f"Word帳票生成エラー: {str(e)}")
        raise e

def add_subject_content(cell, subject_data):
    """教科別コンテンツをセルに追加"""
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    # セル内の段落をクリア
    cell.text = ""
    
    # 教科名
    p = cell.add_paragraph()
    run = p.add_run(f"{subject_data['name']} ({subject_data['total_score']}/{subject_data['max_score']}点)")
    run.bold = True
    run.font.size = Pt(16)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 順位・平均点
    cell.add_paragraph(f"全国順位: {subject_data['national_rank']}位 / {subject_data['total_students']}名")
    cell.add_paragraph(f"全国平均: {subject_data['average_score']}点")
    
    # 大問別成績
    cell.add_paragraph("【大問別成績】")
    
    for q_score in subject_data['question_scores']:
        q_avg = next((qa['average'] for qa in subject_data['question_averages'] 
                     if qa['question_number'] == q_score['question_number']), 0)
        cell.add_paragraph(
            f"大問{q_score['question_number']}: {q_score['score']}/{q_score['max_score']}点 "
            f"(平均: {q_avg}点)"
        )
    
    # コメント
    cell.add_paragraph()
    cell.add_paragraph("【コメント】")
    cell.add_paragraph(subject_data['comment'])

def generate_excel_report(report_data):
    """Excel形式の成績表を生成"""
    # 簡単な実装（Word版を優先）
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    # TODO: Excel生成の詳細実装
    return temp_file.name

def get_grade_level_from_student_grade(student_grade):
    """生徒の学年から対応するテスト学年レベルを取得"""
    # 数値・文字列の両方に対応
    grade_mapping = {
        # 数値形式
        1: 'elementary_1', '1': 'elementary_1',
        2: 'elementary_2', '2': 'elementary_2',
        3: 'elementary_3', '3': 'elementary_3',
        4: 'elementary_4', '4': 'elementary_4',
        5: 'elementary_5', '5': 'elementary_5',
        6: 'elementary_6', '6': 'elementary_6',
        7: 'middle_1', '7': 'middle_1',
        8: 'middle_2', '8': 'middle_2',
        9: 'middle_3', '9': 'middle_3',
        # 文字列形式
        '小1': 'elementary_1',
        '小2': 'elementary_2',
        '小3': 'elementary_3',
        '小4': 'elementary_4',
        '小5': 'elementary_5',
        '小6': 'elementary_6',
        '中1': 'middle_1',
        '中2': 'middle_2',
        '中3': 'middle_3'
    }
    return grade_mapping.get(student_grade)

def is_student_test_grade_match(student, test):
    """生徒の学年とテストの対象学年が一致するかチェック"""
    expected_grade_level = get_grade_level_from_student_grade(student.grade)
    return expected_grade_level == test.grade_level

def import_scores_from_excel(file_path, year, period, subject=None, grade_level=None, school_id=None):
    """
    Excelファイルから得点データを一括インポート（新形式対応）
    塾ID・塾名・教室ID・教室名・生徒ID・生徒名・学年・年度・期間・出席・大問・合計点
    """
    try:
        # CSVファイルを読み込み（BOM対応）
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')  # BOM付きUTF-8
        except:
            try:
                df = pd.read_csv(file_path, encoding='utf-8')  # 通常のUTF-8
            except:
                try:
                    df = pd.read_csv(file_path, encoding='shift_jis')  # Shift_JIS
                except:
                    df = pd.read_excel(file_path)  # Excel形式
        
        # 列名を正規化（空白文字除去）
        df.columns = df.columns.str.strip()
        
        # 統合テンプレート形式か単一教科形式かを判定
        is_unified_template = subject is None or any(col for col in df.columns if '_大問' in col)
        
        if not is_unified_template:
            # 単一教科の場合のテスト構造を取得
            structure = get_test_template_structure(year, period, subject, grade_level)
            if not structure:
                period_display = {'spring': '春季', 'summer': '夏季', 'winter': '冬季'}.get(period, period)
                subject_display = {'japanese': '国語', 'math': '算数', 'english': '英語', 'mathematics': '数学'}.get(subject, subject)
                grade_display = {'elementary': '小学生', 'middle_school': '中学生'}.get(grade_level, grade_level) if grade_level else ''
                raise ValidationError(f"{year}年度{period_display}{grade_display}{subject_display}テストが見つかりません")
            
            test = structure['test']
        else:
            # 統合テンプレートの場合はtestをNoneに設定（後で各教科別に処理）
            test = None
            structure = None
        
        # 基本列をチェック
        expected_columns = ['塾ID', '塾名', '教室ID', '教室名', '生徒ID', '生徒名', '学年', '年度', '期間', '出席']
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(f"必要な列が不足しています: {', '.join(missing_columns)}\\n実際の列: {list(df.columns)}")
        
        # 統合テンプレート形式の検出（デバッグ用）
        unified_columns = [col for col in df.columns if '_大問' in col]
        single_columns = [col for col in df.columns if col.startswith('大問')]
        print(f"列の検出: 統合形式列={unified_columns}, 単一形式列={single_columns}")
        
        # 空行を除去
        df = df.dropna(how='all')
        
        # データ型を文字列に統一し、数値フィールドの小数点を除去
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            # 数値IDフィールドの小数点を除去
            if col in ['塾ID', '教室ID', '生徒ID']:
                df[col] = df[col].str.replace('.0', '', regex=False)
                # ExcelエラーやNaN値をクリーンアップ
                df[col] = df[col].replace(['nan', '#N/A', '#REF!', '#VALUE!', '#DIV/0!', '#NAME?', '#NULL!', '#NUM!'], '')
        
        created_scores = []
        updated_scores = []
        errors = []
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # 空行をスキップ
                    if pd.isna(row['生徒ID']) or str(row['生徒ID']).strip() == '' or str(row['生徒ID']).strip() == 'nan':
                        continue
                    
                    student_id = str(row['生徒ID']).strip()
                    
                    # 必須フィールドの検証
                    if str(row['塾ID']).strip() == '' or str(row['塾ID']).strip() == 'nan':
                        errors.append(f'行 {index + 2}: 塾IDが空です')
                        continue
                    
                    if str(row['教室ID']).strip() == '' or str(row['教室ID']).strip() == 'nan':
                        errors.append(f'行 {index + 2}: 教室IDが空です (塾ID: {row["塾ID"]})')
                        continue
                    
                    # 教室を取得
                    from classrooms.models import Classroom
                    classroom = Classroom.objects.filter(
                        classroom_id=row['教室ID'],
                        school__school_id=row['塾ID']
                    ).first()
                    
                    if not classroom:
                        errors.append(f'行 {index + 2}: 教室が見つかりません (塾ID: {row["塾ID"]}, 教室ID: {row["教室ID"]})')
                        continue
                    
                    # 生徒の存在確認・作成（StudentEnrollment経由）
                    from students.models import StudentEnrollment
                    
                    # まず該当期間の受講生徒を探す
                    enrollment = StudentEnrollment.objects.filter(
                        student__student_id=student_id,
                        student__classroom=classroom,
                        year=year,
                        period=period,
                        is_active=True
                    ).first()
                    
                    if enrollment:
                        student = enrollment.student
                    else:
                        # 生徒が存在するかチェック（他の期間含む）
                        existing_student = Student.objects.filter(
                            student_id=student_id,
                            classroom=classroom
                        ).first()
                        
                        if existing_student:
                            # 既存生徒の新期間登録を作成
                            student = existing_student
                            enrollment = StudentEnrollment.objects.create(
                                student=student,
                                year=year,
                                period=period,
                                is_active=True
                            )
                            print(f"新期間受講登録作成: 生徒ID {student_id} ({student.name}) - {year}年度{period}期")
                        else:
                            # 完全に新しい生徒を作成
                            student_name = row.get('生徒名', f'生徒{student_id}')
                            student_grade = row.get('学年', '1')
                            
                            # 学年形式を数値に変換
                            if isinstance(student_grade, str):
                                if student_grade.startswith('小'):
                                    student_grade = student_grade.replace('小', '')
                                elif student_grade.startswith('中'):
                                    middle_grade = int(student_grade.replace('中', ''))
                                    student_grade = str(middle_grade + 6)
                            
                            student = Student.objects.create(
                                student_id=student_id,
                                name=student_name,
                                grade=student_grade,
                                classroom=classroom,
                                is_active=True
                            )
                            
                            # 新生徒の受講登録も作成
                            enrollment = StudentEnrollment.objects.create(
                                student=student,
                                year=year,
                                period=period,
                                is_active=True
                            )
                            print(f"新生徒・受講登録作成: 生徒ID {student_id} ({student_name}) - {year}年度{period}期")
                    
                    # 出席状況を処理
                    attendance_value = str(row.get('出席', '出席')).strip()
                    is_attendance = attendance_value in ['出席', '○', '1', 'True', 'true']
                    
                    # 各大問の得点を処理（単一教科・統合テンプレート両方対応）
                    
                    # 統合テンプレートかどうかを判定（教科名_大問の形式の列があるかチェック）
                    is_unified_template = any(col for col in df.columns if '_大問' in col)
                    print(f"行{index + 2}: 統合テンプレート判定: {is_unified_template}, 生徒: {student.name}, 学年: {student.grade}")
                    
                    if is_unified_template:
                        # 統合テンプレートの場合：複数教科を処理
                        
                        # 利用可能な教科とテスト構造を取得
                        from tests.models import TestDefinition
                        available_tests = TestDefinition.objects.filter(
                            schedule__year=year,
                            schedule__period=period,
                            is_active=True
                        )
                        print(f"利用可能なテスト: {[(str(t), t.subject, t.grade_level) for t in available_tests]}")
                        
                        # 教科マッピング
                        subject_mapping = {
                            '国語': 'japanese',
                            '算数': 'math',
                            '英語': 'english',
                            '数学': 'mathematics'
                        }
                        
                        for subject_display, subject_code in subject_mapping.items():
                            # この生徒の学年に対応する教科かチェック
                            is_elementary = student.grade and student.grade.startswith('小')
                            
                            # 小学生は国語・算数、中学生は英語・数学
                            if is_elementary and subject_code in ['japanese', 'math']:
                                should_process = True
                            elif not is_elementary and subject_code in ['english', 'mathematics']:
                                should_process = True
                            else:
                                should_process = False
                            
                            if not should_process:
                                continue
                            
                            # 対応するテストを探す
                            test_for_subject = available_tests.filter(
                                subject=subject_code,
                                grade_level__startswith='elementary_' if is_elementary else 'middle_'
                            ).first()
                            
                            if not test_for_subject:
                                print(f"警告: {subject_display}のテストが見つかりません (生徒: {student.name}, 学年: {student.grade})")
                                continue
                            
                            # この教科の大問を処理
                            subject_structure = get_test_template_structure(year, period, subject_code, test_for_subject.grade_level)
                            if not subject_structure:
                                print(f"警告: {subject_display}のテスト構造が見つかりません")
                                continue
                            
                            print(f"処理中: {subject_display} (テスト: {str(test_for_subject)})")
                            
                            for group_info in subject_structure['question_groups']:
                                column_name = f"{subject_display}_大問{group_info['group_number']}"
                                
                                # 得点値を取得
                                score_value = None
                                if column_name in df.columns:
                                    score_value = row[column_name]
                                
                                if pd.isna(score_value) or str(score_value).strip() in ['', 'nan']:
                                    continue  # 空の場合はスキップ
                                
                                try:
                                    score_value = float(score_value)
                                    if score_value < 0 or score_value > group_info['max_score']:
                                        errors.append(f"行{index + 2}: {column_name}の得点が範囲外です (0-{group_info['max_score']})")
                                        continue
                                except (ValueError, TypeError):
                                    errors.append(f"行{index + 2}: {column_name}の得点が無効です")
                                    continue
                                
                                # 生徒の学年とテストの対象学年をチェック
                                if not is_student_test_grade_match(student, test_for_subject):
                                    expected_grade_level = get_grade_level_from_student_grade(student.grade)
                                    errors.append(f"行{index + 2}: {student.name}の学年({student.grade})とテスト対象学年({test_for_subject.grade_level})が一致しません。期待される学年レベル: {expected_grade_level}")
                                    continue
                                
                                # 得点レコードを作成または更新
                                try:
                                    group = QuestionGroup.objects.get(
                                        test=test_for_subject,
                                        group_number=group_info['group_number']
                                    )
                                    score_obj, created = Score.objects.update_or_create(
                                        student=student,
                                        test=test_for_subject,
                                        question_group=group,
                                        defaults={
                                            'score': score_value,
                                            'attendance': is_attendance
                                        }
                                    )
                                    
                                    if created:
                                        created_scores.append(score_obj)
                                    else:
                                        updated_scores.append(score_obj)
                                    
                                    print(f"成功: {student.name} - {subject_display} 大問{group_info['group_number']}: {score_value}点")
                                except QuestionGroup.DoesNotExist:
                                    errors.append(f"行{index + 2}: {column_name}の大問が見つかりません (テスト: {str(test_for_subject)})")
                                    continue
                    else:
                        # 単一教科テンプレートの場合：従来の処理
                        for group_info in structure['question_groups']:
                            group = QuestionGroup.objects.get(id=group_info['id'])
                            column_name = f"大問{group_info['group_number']}"
                            
                            # 得点値を取得
                            score_value = None
                            if column_name in df.columns:
                                score_value = row[column_name]
                            
                            if pd.isna(score_value) or str(score_value).strip() in ['', 'nan']:
                                continue  # 空の場合はスキップ
                            
                            try:
                                score_value = float(score_value)
                                if score_value < 0 or score_value > group_info['max_score']:
                                    errors.append(f"行{index + 2}: {column_name}の得点が範囲外です (0-{group_info['max_score']})")
                                    continue
                            except (ValueError, TypeError):
                                errors.append(f"行{index + 2}: {column_name}の得点が無効です")
                                continue
                            
                            # 生徒の学年とテストの対象学年をチェック
                            if not is_student_test_grade_match(student, test):
                                expected_grade_level = get_grade_level_from_student_grade(student.grade)
                                errors.append(f"行{index + 2}: {student.name}の学年({student.grade})とテスト対象学年({test.grade_level})が一致しません。期待される学年レベル: {expected_grade_level}")
                                continue
                            
                            # 得点レコードを作成または更新
                            score_obj, created = Score.objects.update_or_create(
                                student=student,
                                test=test,
                                question_group=group,
                                defaults={
                                    'score': score_value,
                                    'attendance': is_attendance
                                }
                            )
                            
                            if created:
                                created_scores.append(score_obj)
                            else:
                                updated_scores.append(score_obj)
                    
                except Exception as e:
                    student_info = f"生徒ID: {student_id}" if 'student_id' in locals() else "不明な生徒"
                    errors.append(f"行{index + 2} ({student_info}): {str(e)}")
                    print(f"インポートエラー - 行{index + 2}: {student_info} - {str(e)}")
        
        period_display = {'spring': '春季', 'summer': '夏季', 'winter': '冬季'}.get(period, period)
        
        # インポート詳細情報を追加
        import_details = []
        for score in created_scores + updated_scores:
            import_details.append({
                'student_name': score.student.name,
                'student_id': score.student.student_id,
                'subject': score.test.get_subject_display(),
                'question_group': f"大問{score.question_group.group_number}",
                'score': score.score,
                'attendance': score.attendance
            })
        
        return {
            'success': True,
            'created_scores': len(created_scores),
            'updated_scores': len(updated_scores),
            'test_info': f"{year}年度{period_display} 統合テンプレート",
            'import_details': import_details[:20],  # 最初の20件のみ表示
            'total_processed': len(import_details),
            'errors': errors
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def export_scores_template_by_test(year, period, subject, school_id=None):
    """
    指定されたテストの得点エクスポート用テンプレートを生成
    """
    try:
        structure = get_test_template_structure(year, period, subject)
        if not structure:
            period_display = {'spring': '春季', 'summer': '夏季', 'winter': '冬季'}.get(period, period)
            subject_display = {'japanese': '国語', 'math': '算数', 'english': '英語', 'mathematics': '数学'}.get(subject, subject)
            raise ValidationError(f"{year}年度{period_display}{subject_display}テストが見つかりません")
        
        test = structure['test']
        
        # 生徒データを取得
        students_query = Student.objects.all()
        if school_id:
            students_query = students_query.filter(classroom__school__school_id=school_id)
        
        students = students_query.select_related('classroom').order_by('classroom', 'student_id')
        
        if not students.exists():
            raise ValidationError("対象の生徒が見つかりません")
        
        # データを構築
        data = []
        for student in students:
            row = {
                '生徒ID': student.student_id,
                '生徒名': student.name,
                '教室ID': student.classroom.classroom_id,
                '教室名': student.classroom.name,
            }
            
            total_score = 0
            for group_info in structure['question_groups']:
                column_name = f"大問{group_info['group_number']}({group_info['title']})"
                
                # 既存の得点があるかチェック
                try:
                    score_obj = Score.objects.get(
                        student=student,
                        test=test,
                        question_group_id=group_info['id']
                    )
                    score_value = score_obj.score
                    total_score += score_value
                except Score.DoesNotExist:
                    score_value = ''  # 未入力
                
                row[column_name] = score_value
            
            row['合計点'] = total_score if total_score > 0 else ''
            data.append(row)
        
        df = pd.DataFrame(data)
        return df
        
    except Exception as e:
        raise ValidationError(str(e))

def generate_unified_score_template(year, period, grade_level):
    """
    指定された学年のすべての教科を含む統合テンプレートを生成
    小学生: 国語・算数, 中学生: 英語・数学
    """
    # 学年レベルに応じて教科を決定
    if grade_level == 'elementary':
        subjects = ['japanese', 'math']  # 国語、算数
    elif grade_level == 'middle_school':
        subjects = ['english', 'mathematics']  # 英語、数学
    else:
        raise ValidationError(f"無効な学年レベルです: {grade_level}")
    
    # 各教科のテスト構造を取得
    all_structures = {}
    for subject in subjects:
        structure = get_test_template_structure(year, period, subject, grade_level)
        if structure:
            all_structures[subject] = structure
    
    if not all_structures:
        period_display = {'spring': '春季', 'summer': '夏季', 'winter': '冬季'}.get(period, period)
        grade_display = {'elementary': '小学生', 'middle_school': '中学生'}.get(grade_level, grade_level)
        raise ValidationError(f"{year}年度{period_display}{grade_display}のテストが見つかりません")
    
    # 基本情報列（生徒登録と同じ形式）
    columns = [
        '塾ID', '塾名', '教室ID', '教室名', 
        '生徒ID', '生徒名', '学年', '年度', '期間',
        '出席'  # 出席状況
    ]
    
    # 各教科の大問ごとの列を追加
    subject_columns = {}
    for subject, structure in all_structures.items():
        subject_display = {'japanese': '国語', 'math': '算数', 'english': '英語', 'mathematics': '数学'}.get(subject, subject)
        subject_columns[subject] = []
        
        for group in structure['question_groups']:
            column_name = f"{subject_display}_大問{group['group_number']}"
            columns.append(column_name)
            subject_columns[subject].append(column_name)
        
        # 教科別合計点列
        total_column = f"{subject_display}_合計点"
        columns.append(total_column)
        subject_columns[subject].append(total_column)
    
    # 全体合計点列
    columns.append('全体合計点')
    
    # サンプルデータ
    sample_data = {col: [] for col in columns}
    
    # 期間表示を変換
    period_display_jp = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}.get(period, period)
    
    # サンプル行を3つ作成
    sample_names = ['田中太郎', '佐藤花子', '鈴木次郎']
    if grade_level == 'elementary':
        sample_grades = ['小6', '小5', '小4']
    else:
        sample_grades = ['中1', '中2', '中3']
    
    for i in range(3):
        sample_data['塾ID'].append('100001')
        sample_data['塾名'].append('サンプル学習塾')
        sample_data['教室ID'].append('001001')
        sample_data['教室名'].append('メイン教室')
        sample_data['生徒ID'].append(f'{123456 + i}')
        sample_data['生徒名'].append(sample_names[i])
        sample_data['学年'].append(sample_grades[i])
        sample_data['年度'].append(str(year))
        sample_data['期間'].append(period_display_jp)
        sample_data['出席'].append('出席')
        
        overall_total = 0
        
        # 各教科のサンプル点数を設定
        for subject, structure in all_structures.items():
            subject_total = 0
            
            for group in structure['question_groups']:
                subject_display = {'japanese': '国語', 'math': '算数', 'english': '英語', 'mathematics': '数学'}.get(subject, subject)
                column_name = f"{subject_display}_大問{group['group_number']}"
                
                # サンプル点数（満点から徐々に減らす）
                score = max(0, group['max_score'] - i * 2)
                sample_data[column_name].append(score)
                subject_total += score
            
            # 教科別合計点
            subject_display = {'japanese': '国語', 'math': '算数', 'english': '英語', 'mathematics': '数学'}.get(subject, subject)
            total_column = f"{subject_display}_合計点"
            sample_data[total_column].append(subject_total)
            overall_total += subject_total
        
        # 全体合計点
        sample_data['全体合計点'].append(overall_total)
    
    # 空行を追加（データ入力用）
    for _ in range(3):
        for col in columns:
            if col in ['年度', '期間']:
                sample_data[col].append(str(year) if col == '年度' else period_display_jp)
            else:
                sample_data[col].append('')
    
    df = pd.DataFrame(sample_data)
    return df, all_structures

def _format_grade_display(grade):
    """学年を「小6」「中1」形式で表示する"""
    if not grade:
        return '未設定'
    
    try:
        grade_num = int(grade)
        if 1 <= grade_num <= 6:
            return f'小{grade_num}'
        elif 7 <= grade_num <= 9:
            return f'中{grade_num - 6}'
        else:
            return str(grade)
    except (ValueError, TypeError):
        return str(grade)

def generate_all_grades_unified_template(year, period):
    """
    全学年対応の統合テンプレートを生成（小学生・中学生両方の全教科を含む）
    """
    # 利用可能なテストを直接データベースから取得
    from tests.models import TestDefinition
    
    # 2025年夏期のテストを取得
    tests = TestDefinition.objects.filter(
        schedule__year=year,
        schedule__period=period,
        is_active=True
    )
    
    if not tests.exists():
        period_display = {'spring': '春季', 'summer': '夏季', 'winter': '冬季'}.get(period, period)
        raise ValidationError(f"{year}年度{period_display}のテストが見つかりません")
    
    # 教科別にテスト構造を取得
    all_structures = {}
    
    # 小学生の国語・算数を探す
    elementary_japanese = tests.filter(
        subject='japanese',
        grade_level__startswith='elementary_'
    ).first()
    if elementary_japanese:
        structure = get_test_template_structure(year, period, 'japanese', elementary_japanese.grade_level)
        if structure:
            all_structures['japanese_elementary'] = structure
    
    elementary_math = tests.filter(
        subject='math',
        grade_level__startswith='elementary_'
    ).first()
    if elementary_math:
        structure = get_test_template_structure(year, period, 'math', elementary_math.grade_level)
        if structure:
            all_structures['math_elementary'] = structure
    
    # 中学生の英語・数学を探す（存在する場合）
    middle_english = tests.filter(
        subject='english',
        grade_level__startswith='middle_'
    ).first()
    if middle_english:
        structure = get_test_template_structure(year, period, 'english', middle_english.grade_level)
        if structure:
            all_structures['english_middle'] = structure
    
    middle_mathematics = tests.filter(
        subject='mathematics',
        grade_level__startswith='middle_'
    ).first()
    if middle_mathematics:
        structure = get_test_template_structure(year, period, 'mathematics', middle_mathematics.grade_level)
        if structure:
            all_structures['mathematics_middle'] = structure
    
    if not all_structures:
        period_display = {'spring': '春季', 'summer': '夏季', 'winter': '冬季'}.get(period, period)
        raise ValidationError(f"{year}年度{period_display}のテストが見つかりません")
    
    # 基本情報列（生徒登録と同じ形式）
    columns = [
        '塾ID', '塾名', '教室ID', '教室名', 
        '生徒ID', '生徒名', '学年', '年度', '期間',
        '出席'  # 出席状況
    ]
    
    # 各教科の大問ごとの列を追加
    subject_mapping = {
        'japanese_elementary': '国語',
        'math_elementary': '算数', 
        'english_middle': '英語',
        'mathematics_middle': '数学'
    }
    
    for subject_key, structure in all_structures.items():
        subject_display = subject_mapping.get(subject_key, subject_key)
        
        for group in structure['question_groups']:
            column_name = f"{subject_display}_大問{group['group_number']}"
            columns.append(column_name)
        
        # 教科別合計点列
        total_column = f"{subject_display}_合計点"
        columns.append(total_column)
    
    # 全体合計点列
    columns.append('全体合計点')
    
    # サンプルデータ
    sample_data = {col: [] for col in columns}
    
    # 期間表示を変換
    period_display_jp = {'spring': '春期', 'summer': '夏期', 'winter': '冬期'}.get(period, period)
    
    # 実際の生徒データを取得
    from students.models import Student
    from scores.models import Score
    
    # 指定年度・期間の生徒を取得（StudentEnrollment経由）
    from students.models import StudentEnrollment
    
    # 該当期間の受講者を取得
    enrollments = StudentEnrollment.objects.filter(
        year=year,
        period=period,
        is_active=True
    ).select_related('student', 'student__classroom', 'student__classroom__school')
    
    # 生徒のリストを作成
    students = [enrollment.student for enrollment in enrollments if enrollment.student.is_active]
    
    if students:
        # 実際の生徒データを使用
        for student in students:
            # 学年表示を変換
            grade_display = _format_grade_display(student.grade)
            
            sample_data['塾ID'].append(student.classroom.school.school_id)
            sample_data['塾名'].append(student.classroom.school.name)
            sample_data['教室ID'].append(student.classroom.classroom_id)
            sample_data['教室名'].append(student.classroom.name)
            sample_data['生徒ID'].append(student.student_id)
            sample_data['生徒名'].append(student.name)
            sample_data['学年'].append(grade_display)
            sample_data['年度'].append(str(year))
            sample_data['期間'].append(period_display_jp)
            sample_data['出席'].append('')  # 初期値は空
            
            overall_total = 0
            
            # 各教科の既存スコアを取得
            for subject_key, structure in all_structures.items():
                subject_display = subject_mapping.get(subject_key, subject_key)
                subject_total = 0
                
                # この生徒がこの教科を受講するかどうか判定
                is_elementary = student.grade and student.grade.startswith('小')
                should_include = False
                if is_elementary and subject_key.endswith('_elementary'):
                    should_include = True
                elif not is_elementary and subject_key.endswith('_middle'):
                    should_include = True
                
                for group in structure['question_groups']:
                    column_name = f"{subject_display}_大問{group['group_number']}"
                    
                    if should_include:
                        # 既存スコアを探す
                        try:
                            from tests.models import QuestionGroup
                            question_group = QuestionGroup.objects.get(
                                test=structure['test'],
                                group_number=group['group_number']
                            )
                            score_obj = Score.objects.get(
                                student=student,
                                test=structure['test'],
                                question_group=question_group
                            )
                            score_value = score_obj.score
                            subject_total += score_value
                        except (Score.DoesNotExist, QuestionGroup.DoesNotExist):
                            score_value = ''  # スコア未入力
                        
                        sample_data[column_name].append(score_value)
                    else:
                        # 該当しない学年の場合は空欄
                        sample_data[column_name].append('')
                
                # 教科別合計点
                total_column = f"{subject_display}_合計点"
                if should_include and subject_total > 0:
                    sample_data[total_column].append(subject_total)
                    overall_total += subject_total
                else:
                    sample_data[total_column].append('')
            
            # 全体合計点
            sample_data['全体合計点'].append(overall_total if overall_total > 0 else '')
    else:
        # 生徒が存在しない場合はサンプル行を追加
        sample_names = ['田中太郎', '佐藤花子', '鈴木次郎']
        sample_grades = ['小6', '小5', '小4']
        
        for i in range(3):
            sample_data['塾ID'].append('100001')
            sample_data['塾名'].append('サンプル学習塾')
            sample_data['教室ID'].append('001001')
            sample_data['教室名'].append('メイン教室')
            sample_data['生徒ID'].append(f'{123456 + i}')
            sample_data['生徒名'].append(sample_names[i])
            sample_data['学年'].append(sample_grades[i])
            sample_data['年度'].append(str(year))
            sample_data['期間'].append(period_display_jp)
            sample_data['出席'].append('')
            
            # 各教科は空欄で初期化
            for subject_key, structure in all_structures.items():
                subject_display = subject_mapping.get(subject_key, subject_key)
                
                for group in structure['question_groups']:
                    column_name = f"{subject_display}_大問{group['group_number']}"
                    sample_data[column_name].append('')
                
                total_column = f"{subject_display}_合計点"
                sample_data[total_column].append('')
            
            sample_data['全体合計点'].append('')
    
    # 空行を追加（データ入力用）
    for _ in range(3):
        for col in columns:
            if col in ['年度', '期間']:
                sample_data[col].append(str(year) if col == '年度' else period_display_jp)
            else:
                sample_data[col].append('')
    
    df = pd.DataFrame(sample_data)
    return df, all_structures

def get_available_tests():
    """
    利用可能なテスト一覧を取得
    """
    tests = TestDefinition.objects.select_related('schedule').order_by('-schedule__year', '-schedule__period', 'subject')
    
    available_tests = []
    for test in tests:
        period_display = {'spring': '春季', 'summer': '夏季', 'winter': '冬季'}.get(test.schedule.period, test.schedule.period)
        available_tests.append({
            'year': test.schedule.year,
            'period': test.schedule.period,
            'period_display': period_display,
            'subject': test.subject,
            'subject_display': test.get_subject_display(),
            'name': str(test),
            'question_groups_count': test.question_groups.count()
        })
    
    return available_tests

def calculate_and_save_test_summary_by_school_type(year, period, school_type):
    """
    学校種別（小学生・中学生）でテスト結果を集計して保存
    """
    try:
        from tests.models import TestDefinition
        from students.models import Student
        from scores.models import TestResult
        from django.db.models import Avg, Count, Q
        
        # 学校種別に応じて対象科目を決定
        if school_type == 'elementary':
            target_subjects = ['japanese', 'math']  # 国語、算数
            grade_filter = Q(grade__startswith='elementary_')
        elif school_type == 'middle':
            target_subjects = ['english', 'mathematics']  # 英語、数学
            grade_filter = Q(grade__startswith='middle_')
        else:
            return {'success': False, 'error': '無効な学校種別です'}
        
        # 対象テストを取得
        tests = TestDefinition.objects.filter(
            schedule__year=year,
            schedule__period=period,
            subject__in=target_subjects
        )
        
        if not tests.exists():
            return {'success': False, 'error': f'{year}年度{period}期の{school_type}テストが見つかりません'}
        
        # 対象学年のテスト結果を取得
        total_students = TestResult.objects.filter(
            test__in=tests
        ).values('student').distinct().count()
        
        # 参加している塾数を取得
        schools_count = TestResult.objects.filter(
            test__in=tests
        ).values('student__classroom__school').distinct().count()
        
        return {
            'success': True,
            'total_students': total_students,
            'schools_count': schools_count,
            'school_type': school_type
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_test_summary_by_school_type(year, period, school_type):
    """
    学校種別での集計結果を取得
    """
    try:
        # 簡易実装 - 集計データの取得
        return {
            'success': True,
            'test_summary': {
                'year': year,
                'period': period,
                'school_type': school_type,
                'total_students': 0,
                'average_score': 0.0,
                'average_correct_rate': 0.0,
            },
            'school_summaries': []
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def recalculate_test_results_for_test(test, grade=None):
    """
    指定されたテストの結果を再計算（学年指定可能）
    """
    from students.models import Student
    
    # 対象学生を取得
    students_query = Student.objects.filter(
        scores__test=test
    ).distinct()
    
    if grade:
        students_query = students_query.filter(grade=grade)
    
    results = []
    for student in students_query:
        result = calculate_test_results(student, test)
        results.append(result)
    
    return results

def calculate_and_save_test_summary(year, period, subject, grade_level=None):
    """
    テスト集計を実行してデータベースに保存
    """
    from .models import TestSummary, SchoolTestSummary, TestResult
    from tests.models import TestDefinition
    from students.models import Student
    from schools.models import School
    from django.db.models import Avg, Count
    from decimal import Decimal
    import json
    
    try:
        # 指定されたテストを取得
        query = TestDefinition.objects.filter(
            schedule__year=year,
            schedule__period=period,
            subject=subject
        )
        
        if grade_level:
            query = query.filter(grade_level=grade_level)
        
        test = query.first()
        if not test:
            return {'success': False, 'error': 'テストが見つかりません'}
        
        # テスト結果を取得
        results = TestResult.objects.filter(test=test).select_related('student', 'student__classroom__school')
        
        if not results.exists():
            return {'success': False, 'error': 'テスト結果が見つかりません'}
        
        # 全体統計を計算
        total_students = results.count()
        avg_score = results.aggregate(avg=Avg('total_score'))['avg'] or 0
        avg_correct_rate = results.aggregate(avg=Avg('correct_rate'))['avg'] or 0
        
        # 学年別統計を計算
        grade_stats = {}
        for grade in range(1, 7):  # 1年生〜6年生
            grade_results = results.filter(student__grade=grade)
            if grade_results.exists():
                grade_avg = grade_results.aggregate(avg=Avg('total_score'))['avg'] or 0
                grade_correct_rate = grade_results.aggregate(avg=Avg('correct_rate'))['avg'] or 0
                grade_stats[str(grade)] = {
                    'count': grade_results.count(),
                    'average_score': float(grade_avg),
                    'average_correct_rate': float(grade_correct_rate)
                }
        
        # 塾別統計を計算
        school_stats = {}
        schools = School.objects.filter(
            classrooms__students__test_results__test=test
        ).distinct()
        
        school_rankings = []
        for school in schools:
            school_results = results.filter(student__classroom__school=school)
            if school_results.exists():
                school_avg = school_results.aggregate(avg=Avg('total_score'))['avg'] or 0
                school_correct_rate = school_results.aggregate(avg=Avg('correct_rate'))['avg'] or 0
                
                # 学年別詳細
                grade_details = {}
                for grade in range(1, 7):
                    grade_school_results = school_results.filter(student__grade=grade)
                    if grade_school_results.exists():
                        grade_details[str(grade)] = {
                            'count': grade_school_results.count(),
                            'average_score': float(grade_school_results.aggregate(avg=Avg('total_score'))['avg'] or 0),
                            'students': [
                                {
                                    'name': r.student.name,
                                    'student_id': r.student.student_id,
                                    'classroom_name': r.student.classroom.name,
                                    'total_score': r.total_score,
                                    'correct_rate': float(r.correct_rate),
                                    'school_rank': r.school_rank,
                                    'national_rank': r.national_rank
                                }
                                for r in grade_school_results.order_by('-total_score')
                            ]
                        }
                
                school_data = {
                    'school_id': school.school_id,
                    'school_name': school.name,
                    'count': school_results.count(),
                    'average_score': float(school_avg),
                    'average_correct_rate': float(school_correct_rate),
                    'grade_details': grade_details
                }
                
                school_stats[school.school_id] = school_data
                school_rankings.append((school, float(school_avg), school_data))
        
        # 塾を平均点でソート
        school_rankings.sort(key=lambda x: x[1], reverse=True)
        
        # TestSummaryを作成または更新
        test_summary, created = TestSummary.objects.update_or_create(
            test=test,
            defaults={
                'year': year,
                'period': period,
                'subject': subject,
                'total_students': total_students,
                'average_score': Decimal(str(avg_score)),
                'average_correct_rate': Decimal(str(avg_correct_rate)),
                'max_score': test.max_score,
                'grade_statistics': grade_stats,
                'school_statistics': school_stats
            }
        )
        
        # 既存のSchoolTestSummaryを削除
        SchoolTestSummary.objects.filter(test_summary=test_summary).delete()
        
        # SchoolTestSummaryを作成
        for rank, (school, avg_score, school_data) in enumerate(school_rankings, 1):
            SchoolTestSummary.objects.create(
                test_summary=test_summary,
                school=school,
                student_count=school_data['count'],
                average_score=Decimal(str(school_data['average_score'])),
                average_correct_rate=Decimal(str(school_data['average_correct_rate'])),
                rank_among_schools=rank,
                grade_details=school_data['grade_details']
            )
        
        return {
            'success': True,
            'test_summary': test_summary,
            'created': created,
            'total_students': total_students,
            'schools_count': len(school_rankings)
        }
        
    except TestDefinition.DoesNotExist:
        period_display = {'spring': '春季', 'summer': '夏季', 'winter': '冬季'}.get(period, period)
        subject_display = {'japanese': '国語', 'math': '算数', 'english': '英語', 'mathematics': '数学'}.get(subject, subject)
        return {'success': False, 'error': f"{year}年度{period_display}{subject_display}のテストが見つかりません"}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_test_summary(year, period, subject, grade_level=None):
    """
    保存されたテスト集計結果を取得
    """
    from .models import TestSummary, SchoolTestSummary
    from tests.models import TestDefinition
    
    try:
        query = TestDefinition.objects.filter(
            schedule__year=year,
            schedule__period=period,
            subject=subject
        )
        
        if grade_level:
            query = query.filter(grade_level=grade_level)
        
        test = query.first()
        if not test:
            return {'success': False, 'error': 'テストが見つかりません'}
        
        test_summary = TestSummary.objects.get(test=test)
        school_summaries = SchoolTestSummary.objects.filter(
            test_summary=test_summary
        ).select_related('school').order_by('rank_among_schools')
        
        return {
            'test_summary': test_summary,
            'school_summaries': school_summaries,
            'success': True
        }
        
    except (TestDefinition.DoesNotExist, TestSummary.DoesNotExist):
        return {'success': False, 'error': '集計結果が見つかりません'}
    except Exception as e:
        return {'success': False, 'error': str(e)}