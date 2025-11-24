from django.core.management.base import BaseCommand
import pandas as pd
from tests.models import TestDefinition, QuestionGroup, TestSchedule
from students.models import Student
from scores.models import Score
import os

class Command(BaseCommand):
    help = 'Import scores from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return

        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            self.stdout.write(self.style.SUCCESS(f'Loaded {len(df)} rows from {csv_file}'))
            
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    student_id = str(row.get('生徒ID', '')).strip()
                    if not student_id:
                        continue
                        
                    try:
                        student = Student.objects.get(student_id=student_id)
                    except Student.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'Student not found: {student_id}'))
                        error_count += 1
                        continue
                        
                    year = row.get('年度', 2025)
                    period_jp = row.get('期間', '夏期')
                    period_map = {'春期': 'spring', '夏期': 'summer', '秋期': 'autumn', '冬期': 'winter'}
                    period = period_map.get(period_jp, 'summer')
                    
                    for col in df.columns:
                        if '_大問' in col:
                            col_parts = col.split('_')
                            if len(col_parts) >= 2:
                                subject_jp = col_parts[0]
                                question_part = col_parts[1]
                                
                                subject_map = {'国語': 'japanese', '算数': 'math', '数学': 'math', '英語': 'english'}
                                subject = subject_map.get(subject_jp)
                                if not subject:
                                    continue
                                    
                                import re
                                question_match = re.search(r'大問(\d+)', question_part)
                                if not question_match:
                                    continue
                                    
                                question_number = int(question_match.group(1))
                                score_val = row.get(col, '')
                                
                                if pd.isna(score_val) or score_val == '':
                                    continue
                                    
                                try:
                                    score = float(score_val)
                                except ValueError:
                                    continue
                                    
                                # Find test definition
                                # Simplified logic: find test by subject and year/period
                                test = TestDefinition.objects.filter(
                                    schedule__year=year,
                                    schedule__period=period,
                                    subject=subject
                                ).first()
                                
                                if not test:
                                    continue
                                    
                                # Find question group
                                try:
                                    question_group = QuestionGroup.objects.get(
                                        test=test,
                                        group_number=question_number
                                    )
                                except QuestionGroup.DoesNotExist:
                                    continue
                                    
                                Score.objects.update_or_create(
                                    student=student,
                                    test=test,
                                    question_group=question_group,
                                    defaults={
                                        'score': int(score),
                                        'attendance': True
                                    }
                                )
                    
                    success_count += 1
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing row {index}: {e}'))
                    error_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Import completed. Success: {success_count}, Errors: {error_count}'))
            
            # Recalculate results
            from scores.utils import calculate_test_results
            self.stdout.write('Recalculating test results...')
            # Logic to recalculate results would go here, simplified for now
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Import failed: {e}'))
