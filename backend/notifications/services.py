"""
通知作成サービス
"""
from typing import List, Optional
from django.contrib.auth import get_user_model
from .models import Notification, UserNotification

User = get_user_model()


def create_test_notification(
    test_definition,
    notification_type: str = 'test_created'
) -> Notification:
    """
    新規テスト作成時の通知を生成する
    
    Args:
        test_definition: TestDefinitionオブジェクト
        notification_type: 通知種別（'test_created' or 'test_updated'）
    
    Returns:
        Notification: 作成された通知オブジェクト
    """
    # 年度と期間の日本語表示を取得
    schedule = test_definition.schedule
    period_display = schedule.get_period_display() if schedule else '不明'
    
    # 教科の日本語表示を取得
    subject_display = test_definition.get_subject_display()
    
    # 学年の日本語表示を取得
    grade_display = test_definition.get_grade_level_display()
    
    # 通知タイトルとメッセージを生成
    if notification_type == 'test_created':
        title = f"{schedule.year if schedule else '----'}年度{period_display}のテストが追加されました"
        message = f"{grade_display} {subject_display}のテストが新しく登録されました。\n実施予定: {schedule.planned_date if schedule else '未定'}"
    else:  # test_updated
        title = f"{schedule.year if schedule else '----'}年度{period_display}のテストが更新されました"
        message = f"{grade_display} {subject_display}のテスト情報が更新されました。"
    
    # 通知を作成
    notification = Notification.objects.create(
        title=title,
        message=message,
        notification_type=notification_type,
        test_id=test_definition.id,
        year=schedule.year if schedule else None,
        period=schedule.period if schedule else None
    )
    
    # 全ユーザーに通知を送信（管理者・学校・教師全て）
    create_user_notifications_for_all(notification)
    
    return notification


def create_user_notifications_for_all(notification: Notification) -> int:
    """
    全ユーザーに通知を送信する
    
    Args:
        notification: 送信する通知オブジェクト
    
    Returns:
        int: 作成されたユーザー通知の数
    """
    # アクティブな全ユーザーを取得
    users = User.objects.filter(is_active=True)
    
    # 各ユーザーに通知を作成
    user_notifications = []
    for user in users:
        user_notifications.append(
            UserNotification(
                user=user,
                notification=notification,
                is_read=False
            )
        )
    
    # バルク作成でパフォーマンスを向上
    UserNotification.objects.bulk_create(user_notifications, ignore_conflicts=True)
    
    return len(user_notifications)


def create_user_notifications_for_users(
    notification: Notification,
    user_ids: List[int]
) -> int:
    """
    特定のユーザーのみに通知を送信する
    
    Args:
        notification: 送信する通知オブジェクト
        user_ids: 通知を送信するユーザーIDのリスト
    
    Returns:
        int: 作成されたユーザー通知の数
    """
    users = User.objects.filter(id__in=user_ids, is_active=True)
    
    user_notifications = []
    for user in users:
        user_notifications.append(
            UserNotification(
                user=user,
                notification=notification,
                is_read=False
            )
        )
    
    UserNotification.objects.bulk_create(user_notifications, ignore_conflicts=True)
    
    return len(user_notifications)


def get_unread_count(user: User) -> int:
    """
    ユーザーの未読通知数を取得する
    
    Args:
        user: 対象ユーザー
    
    Returns:
        int: 未読通知数
    """
    return UserNotification.objects.filter(
        user=user,
        is_read=False
    ).count()


def mark_notification_as_read(user: User, notification_id: int) -> bool:
    """
    特定の通知を既読にする
    
    Args:
        user: 対象ユーザー
        notification_id: 通知ID
    
    Returns:
        bool: 成功したかどうか
    """
    try:
        user_notification = UserNotification.objects.get(
            user=user,
            notification_id=notification_id
        )
        user_notification.mark_as_read()
        return True
    except UserNotification.DoesNotExist:
        return False