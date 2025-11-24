from django.contrib import admin

# デフォルトのadmin.siteのget_app_listメソッドをオーバーライド
_original_get_app_list = admin.site.get_app_list

def custom_get_app_list(self, request, app_label=None):
    """
    管理画面のトップページに表示するアプリとモデルをカスタマイズ
    """
    app_list = _original_get_app_list(request, app_label)

    # 非表示にするモデルのリスト
    hidden_models = {
        'CSV得点インポート',
        'Test comments',
        'Student comments',
        'Test results',
        'Comment templates v2s',
        'Question scores',
        'Individual problems',
        'Individual problem scores',
        'Test attendances',
        'Scores',
        'Notifications',
        'User notifications',
    }

    # アプリごとにモデルをフィルタリング
    filtered_app_list = []
    for app in app_list:
        # モデルをフィルタリング
        filtered_models = [
            model for model in app['models']
            if model['name'] not in hidden_models
        ]

        # フィルタリング後にモデルが残っている場合のみアプリを追加
        if filtered_models:
            app['models'] = filtered_models
            filtered_app_list.append(app)

    return filtered_app_list

# メソッドを置き換え
admin.site.get_app_list = custom_get_app_list

# サイトヘッダーもカスタマイズ
admin.site.site_header = '全国学力向上テストシステム 管理画面'
admin.site.site_title = '管理画面'
admin.site.index_title = 'システム管理'
