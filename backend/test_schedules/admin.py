from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from .models import TestScheduleInfo
from classrooms.utils import get_billing_summary

@admin.register(TestScheduleInfo)
class TestScheduleInfoAdmin(admin.ModelAdmin):
    list_display = ['year', 'period', 'planned_date', 'actual_date', 'deadline', 'status', 'billing_status']
    list_filter = ['year', 'period', 'status']
    search_fields = ['year']
    ordering = ['-year', 'period']
    actions = ['mark_as_completed', 'mark_as_in_progress', 'show_billing_summary']

    def billing_status(self, obj):
        """課金レポートの生成状況を表示"""
        if obj.status == 'completed':
            summary = get_billing_summary(int(obj.year), obj.period)
            if summary['total_classrooms'] > 0:
                return f"課金レポート生成済み ({summary['total_classrooms']}教室)"
            else:
                return "課金レポート未生成"
        return "-"
    billing_status.short_description = "課金レポート状況"

    def mark_as_completed(self, request, queryset):
        """選択したテストスケジュールを完了状態にする（課金レポート自動生成）"""
        updated_count = 0
        for schedule in queryset:
            if schedule.status != 'completed':
                schedule.status = 'completed'
                schedule.actual_date = timezone.now().date()
                schedule.save()  # シグナルが自動的に課金レポートを生成
                updated_count += 1

        if updated_count > 0:
            messages.success(
                request,
                f"{updated_count}件のテストスケジュールを完了状態にしました。"
                "課金レポートが自動生成されます。"
            )
        else:
            messages.info(request, "既に完了状態のため、変更はありませんでした。")

    mark_as_completed.short_description = "🏁 選択したテストを完了状態にする（課金レポート自動生成）"

    def mark_as_in_progress(self, request, queryset):
        """選択したテストスケジュールを実施中状態にする"""
        updated_count = 0
        for schedule in queryset:
            if schedule.status == 'scheduled':
                schedule.status = 'in_progress'
                schedule.save()
                updated_count += 1

        if updated_count > 0:
            messages.success(
                request,
                f"{updated_count}件のテストスケジュールを実施中状態にしました。"
            )
        else:
            messages.info(request, "既に実施中または完了状態のため、変更はありませんでした。")

    mark_as_in_progress.short_description = "▶️ 選択したテストを実施中状態にする"

    def show_billing_summary(self, request, queryset):
        """選択したテストスケジュールの課金サマリーを表示"""
        summaries = []
        for schedule in queryset:
            if schedule.status == 'completed':
                summary = get_billing_summary(int(schedule.year), schedule.period)
                period_display = schedule.get_period_display()
                summaries.append(
                    f"{schedule.year}年度{period_display}: "
                    f"{summary['total_classrooms']}教室, "
                    f"{summary['total_students']}名, "
                    f"{summary['total_amount']:,}円"
                )
            else:
                period_display = schedule.get_period_display()
                summaries.append(f"{schedule.year}年度{period_display}: 未完了")

        if summaries:
            messages.info(
                request,
                "課金サマリー: " + " | ".join(summaries)
            )
        else:
            messages.warning(request, "選択されたテストスケジュールがありません。")

    show_billing_summary.short_description = "💰 課金サマリーを表示"