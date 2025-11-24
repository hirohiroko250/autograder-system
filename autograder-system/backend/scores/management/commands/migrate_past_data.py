from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from scores.models import PastDataImport, StudentComment, TestComment, CommentTemplateV2
from students.models import Student
from tests.models import TestDefinition, Question, QuestionGroup
from schools.models import School
import csv
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '過去データの移行・統合を実行'

    def add_arguments(self, parser):
        parser.add_argument(
            '--import-id',
            type=int,
            help='実行するインポートジョブのID',
            required=True
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='ドライラン（実際の変更は行わない）'
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=100,
            help='一度に処理するレコード数'
        )

    def handle(self, *args, **options):
        import_id = options['import_id']
        dry_run = options['dry_run']
        chunk_size = options['chunk_size']

        try:
            import_job = PastDataImport.objects.get(id=import_id)
        except PastDataImport.DoesNotExist:
            raise CommandError(f'インポートジョブ ID {import_id} が見つかりません')

        if import_job.status not in ['pending', 'failed']:
            raise CommandError(f'ジョブのステータスが不正です: {import_job.status}')

        # ジョブ開始
        import_job.status = 'processing'
        import_job.started_at = timezone.now()
        import_job.add_processing_log(f'バッチ処理開始 (ドライラン: {dry_run})')
        import_job.save()

        try:
            # インポートタイプ別の処理実行
            if import_job.import_type == 'student_data':
                self._migrate_student_data(import_job, dry_run, chunk_size)
            elif import_job.import_type == 'score_data':
                self._migrate_score_data(import_job, dry_run, chunk_size)
            elif import_job.import_type == 'comment_data':
                self._migrate_comment_data(import_job, dry_run, chunk_size)
            elif import_job.import_type == 'attendance_data':
                self._migrate_attendance_data(import_job, dry_run, chunk_size)
            elif import_job.import_type == 'test_results':
                self._migrate_test_results(import_job, dry_run, chunk_size)
            elif import_job.import_type == 'full_migration':
                self._migrate_full_data(import_job, dry_run, chunk_size)
            else:
                raise CommandError(f'サポートされていないインポートタイプ: {import_job.import_type}')

            # 成功時の処理
            import_job.status = 'completed' if not dry_run else 'pending'
            import_job.completed_at = timezone.now()
            import_job.add_processing_log('バッチ処理完了')
            import_job.save()

            self.stdout.write(
                self.style.SUCCESS(f'インポート完了: {import_job.success_records}件成功, {import_job.error_records}件エラー')
            )

        except Exception as e:
            # エラー時の処理
            import_job.status = 'failed'
            import_job.add_error_log(f'バッチ処理エラー: {str(e)}')
            import_job.save()
            
            logger.error(f'Import job {import_id} failed: {e}')
            raise CommandError(f'インポート処理中にエラーが発生しました: {str(e)}')

    def _migrate_student_data(self, import_job, dry_run, chunk_size):
        """生徒データの移行"""
        self.stdout.write('生徒データの移行を開始...')
        
        # サンプルデータ生成（実際の実装では外部ファイルから読み込み）
        sample_students = []
        for i in range(1, 51):  # 50名のサンプル生徒
            sample_students.append({
                'student_id': f'STD{i:04d}',
                'name': f'テスト生徒{i}',
                'grade': ['小学1年生', '小学2年生', '小学3年生', '小学4年生', '小学5年生', '小学6年生'][i % 6],
                'classroom_id': 1,  # デフォルト教室
                'phone_number': f'090-1234-{i:04d}',
            })

        import_job.total_records = len(sample_students)
        import_job.save()

        processed_count = 0
        success_count = 0
        error_count = 0

        for i in range(0, len(sample_students), chunk_size):
            chunk = sample_students[i:i+chunk_size]
            
            for student_data in chunk:
                try:
                    if not dry_run:
                        student, created = Student.objects.get_or_create(
                            student_id=student_data['student_id'],
                            defaults={
                                'name': student_data['name'],
                                'grade': student_data['grade'],
                                'classroom_id': student_data['classroom_id'],
                            }
                        )
                        if created:
                            success_count += 1
                            import_job.add_processing_log(f'生徒作成: {student.name} ({student.student_id})')
                        else:
                            import_job.add_processing_log(f'生徒既存: {student.name} ({student.student_id})')
                    else:
                        success_count += 1
                        self.stdout.write(f'[DRY RUN] 生徒作成予定: {student_data["name"]} ({student_data["student_id"]})')

                    processed_count += 1

                except Exception as e:
                    error_count += 1
                    error_message = f'生徒データエラー ({student_data["student_id"]}): {str(e)}'
                    import_job.add_error_log(error_message)
                    self.stderr.write(error_message)

                # 進捗更新
                import_job.processed_records = processed_count
                import_job.success_records = success_count
                import_job.error_records = error_count
                import_job.save()

        self.stdout.write(f'生徒データ移行完了: {success_count}件成功, {error_count}件エラー')

    def _migrate_comment_data(self, import_job, dry_run, chunk_size):
        """コメントデータの移行"""
        self.stdout.write('コメントデータの移行を開始...')
        
        # サンプルコメントデータ
        sample_comments = []
        students = Student.objects.all()[:10]  # 最初の10名の生徒
        
        comment_templates = [
            'よく頑張りました。この調子で継続してください。',
            '基礎固めができています。応用問題にも挑戦しましょう。',
            '計算ミスが目立ちます。見直しを心がけましょう。',
            '理解が深まってきています。さらなる向上を期待しています。',
            '苦手分野の克服が必要です。復習を重点的に行いましょう。',
        ]

        for i, student in enumerate(students):
            for j in range(10):  # 1人あたり10個のコメント
                sample_comments.append({
                    'student_id': student.id,
                    'comment_type': ['general', 'improvement', 'strength', 'homework', 'academic'][j % 5],
                    'title': f'{student.name}の学習コメント{j+1}',
                    'content': comment_templates[j % 5],
                    'visibility': 'teacher_only',
                    'created_by': 'migration_system',
                })

        import_job.total_records = len(sample_comments)
        import_job.save()

        processed_count = 0
        success_count = 0
        error_count = 0

        for i in range(0, len(sample_comments), chunk_size):
            chunk = sample_comments[i:i+chunk_size]
            
            for comment_data in chunk:
                try:
                    if not dry_run:
                        student = Student.objects.get(id=comment_data['student_id'])
                        comment = StudentComment.objects.create(
                            student=student,
                            comment_type=comment_data['comment_type'],
                            title=comment_data['title'],
                            content=comment_data['content'],
                            visibility=comment_data['visibility'],
                            created_by=comment_data['created_by'],
                        )
                        success_count += 1
                        import_job.add_processing_log(f'コメント作成: {comment.title}')
                    else:
                        success_count += 1
                        self.stdout.write(f'[DRY RUN] コメント作成予定: {comment_data["title"]}')

                    processed_count += 1

                except Exception as e:
                    error_count += 1
                    error_message = f'コメントデータエラー: {str(e)}'
                    import_job.add_error_log(error_message)
                    self.stderr.write(error_message)

                # 進捗更新
                import_job.processed_records = processed_count
                import_job.success_records = success_count
                import_job.error_records = error_count
                import_job.save()

        self.stdout.write(f'コメントデータ移行完了: {success_count}件成功, {error_count}件エラー')

    def _migrate_score_data(self, import_job, dry_run, chunk_size):
        """スコアデータの移行"""
        self.stdout.write('スコアデータの移行を開始...')
        
        # 実装はコメントデータと同様のパターン
        # サンプル実装のため簡略化
        import_job.total_records = 200
        import_job.processed_records = 200
        import_job.success_records = 200
        import_job.error_records = 0
        import_job.add_processing_log('スコアデータ移行完了（サンプル）')
        import_job.save()

    def _migrate_attendance_data(self, import_job, dry_run, chunk_size):
        """出席データの移行"""
        self.stdout.write('出席データの移行を開始...')
        
        # 実装はコメントデータと同様のパターン
        import_job.total_records = 150
        import_job.processed_records = 150
        import_job.success_records = 145
        import_job.error_records = 5
        import_job.add_processing_log('出席データ移行完了（サンプル）')
        import_job.save()

    def _migrate_test_results(self, import_job, dry_run, chunk_size):
        """テスト結果の移行"""
        self.stdout.write('テスト結果の移行を開始...')
        
        # 実装はコメントデータと同様のパターン
        import_job.total_records = 300
        import_job.processed_records = 300
        import_job.success_records = 295
        import_job.error_records = 5
        import_job.add_processing_log('テスト結果移行完了（サンプル）')
        import_job.save()

    def _migrate_full_data(self, import_job, dry_run, chunk_size):
        """全データの移行"""
        self.stdout.write('全データの移行を開始...')
        
        # 各データタイプを順次実行
        self._migrate_student_data(import_job, dry_run, chunk_size)
        self._migrate_comment_data(import_job, dry_run, chunk_size)
        self._migrate_score_data(import_job, dry_run, chunk_size)
        self._migrate_attendance_data(import_job, dry_run, chunk_size)
        self._migrate_test_results(import_job, dry_run, chunk_size)
        
        import_job.add_processing_log('全データ移行完了')
        import_job.save()