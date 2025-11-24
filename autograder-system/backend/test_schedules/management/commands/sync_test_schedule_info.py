from django.core.management.base import BaseCommand
from tests.models import TestSchedule
from test_schedules.models import TestScheduleInfo


class Command(BaseCommand):
    help = 'TestScheduleからTestScheduleInfoを同期する'

    def handle(self, *args, **options):
        schedules = TestSchedule.objects.all()
        created_count = 0
        updated_count = 0

        for schedule in schedules:
            # ステータスを判定
            status = 'scheduled'
            period_status = schedule.get_period_status()
            if period_status == 'active':
                status = 'in_progress'
            elif period_status == 'ended':
                status = 'completed'

            # TestScheduleInfoを作成または更新
            info, created = TestScheduleInfo.objects.update_or_create(
                year=str(schedule.year),
                period=schedule.period,
                defaults={
                    'planned_date': schedule.planned_date,
                    'actual_date': schedule.actual_date,
                    'deadline': schedule.deadline_at,
                    'status': status
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'作成: {schedule.year}年度 {schedule.get_period_display()}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'更新: {schedule.year}年度 {schedule.get_period_display()}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n同期完了: 作成 {created_count}件, 更新 {updated_count}件'
            )
        )
