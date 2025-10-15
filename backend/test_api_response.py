#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autograder.settings')
django.setup()

import json
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from scores.views import TestResultViewSet

User = get_user_model()

def test_api_response():
    # テスト用のリクエストを作成
    factory = RequestFactory()
    
    # 管理者ユーザーを作成（既存の場合は取得）
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@test.com', 'role': 'school_admin'}
    )
    
    # APIリクエストをシミュレート
    request = factory.get('/api/test-results/detailed_results/', {
        'student_id': '10574',
        'year': '2025'
    })
    request.user = user
    
    # ViewSetのインスタンスを作成
    view = TestResultViewSet()
    view.request = request
    
    try:
        # detailed_results メソッドを直接呼び出し
        response = view.detailed_results(request)
        
        print("=== API Response ===")
        print(f"Status Code: {response.status_code}")
        
        if hasattr(response, 'data'):
            data = response.data
        else:
            # DRF Response でない場合
            data = json.loads(response.content.decode())
        
        print(f"Response Keys: {list(data.keys())}")
        print(f"Results Count: {len(data.get('results', []))}")
        
        if data.get('results'):
            result = data['results'][0]  # 最初の結果を確認
            print(f"\n=== First Result Structure ===")
            for key, value in result.items():
                if isinstance(value, dict):
                    print(f"{key}: {list(value.keys())}")
                else:
                    print(f"{key}: {value}")
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_response()