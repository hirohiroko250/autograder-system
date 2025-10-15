"""
通知システム用のDjangoシグナル
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from tests.models import TestDefinition
from .services import create_test_notification


@receiver(post_save, sender=TestDefinition)
def create_test_notification_on_save(sender, instance, created, **kwargs):
    """
    TestDefinition作成・更新時に通知を生成する
    
    Args:
        sender: シグナルの送信者（TestDefinition）
        instance: 保存されたTestDefinitionインスタンス
        created: 新規作成かどうか
        **kwargs: 追加のキーワード引数
    """
    try:
        # 新規作成の場合のみ通知を作成
        if created:
            create_test_notification(
                test_definition=instance,
                notification_type='test_created'
            )
            print(f"✅ Test creation notification created for: {instance}")
        # 更新の場合は通知を作成しない（必要に応じて変更可能）
        # else:
        #     create_test_notification(
        #         test_definition=instance,
        #         notification_type='test_updated'
        #     )
        #     print(f"✅ Test update notification created for: {instance}")
            
    except Exception as e:
        # エラーが発生してもテスト作成は継続させる
        print(f"❌ Error creating notification for test {instance.id}: {str(e)}")
        import traceback
        traceback.print_exc()