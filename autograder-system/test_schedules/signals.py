from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TestScheduleInfo
from classrooms.models import Classroom, AttendanceRecord, SchoolBillingReport
from classrooms.utils import generate_classroom_billing_report, generate_school_billing_report
from schools.models import School
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=TestScheduleInfo)
def auto_generate_billing_report_on_test_completion(sender, instance, created, **kwargs):
    """
    テストスケジュールのステータスが'completed'に変更された時に
    自動的に課金レポートを生成する
    """
    # 新規作成時は何もしない
    if created:
        return

    # ステータスが'completed'に変更された場合のみ実行
    if instance.status == 'completed':
        logger.info(f"テスト完了検出: {instance.year}年度 {instance.get_period_display()}")

        try:
            # 全ての有効な塾に対して課金レポートを生成
            active_schools = School.objects.filter(is_active=True)

            successful_reports = 0
            failed_reports = 0

            for school in active_schools:
                try:
                    # 塾ベースの課金レポートを生成
                    result = generate_school_billing_report(
                        school=school,
                        year=int(instance.year),
                        period=instance.period,
                        force=False  # 既存レポートは上書きしない
                    )

                    if result.get('created') or result.get('updated'):
                        successful_reports += 1
                        logger.info(
                            f"塾課金レポート生成成功: {school.name} - "
                            f"{result.get('billed_students', 0)}名 "
                            f"{result.get('total_amount', 0)}円"
                        )
                    else:
                        logger.info(
                            f"塾課金レポートスキップ: {school.name} - "
                            f"{result.get('reason', '理由不明')}"
                        )

                except Exception as e:
                    failed_reports += 1
                    logger.error(
                        f"塾課金レポート生成エラー: {school.name} - {str(e)}"
                    )

            logger.info(
                f"自動塾課金レポート生成完了: "
                f"成功 {successful_reports}件, 失敗 {failed_reports}件"
            )

        except Exception as e:
            logger.error(f"自動課金レポート生成で予期しないエラー: {str(e)}")


@receiver(post_save, sender=TestScheduleInfo)
def update_test_status_based_on_deadline(sender, instance, created, **kwargs):
    """
    締切時刻を過ぎた場合、自動的にステータスを'completed'に更新する
    （このシグナルは定期実行タスクで補完することを推奨）
    """
    if instance.status == 'in_progress' and timezone.now() > instance.deadline:
        logger.info(f"締切時刻到達によりテストを完了状態に変更: {instance}")
        instance.status = 'completed'
        instance.save()