# テスト期間外入力制限機能実装

## 概要
テスト期間外でフロントエンド側での得点入力を制限する機能を実装しました。TestScheduleモデルの期間設定を使用して、現在の日時がテスト期間内かどうかを判定し、期間外は入力を無効にします。

## 実装内容

### 1. モデル拡張 (`tests/models.py`)

#### TestScheduleモデル
- **`is_active_now()`**: 現在がテスト期間内かどうかを判定
- **`get_period_status()`**: テスト期間の状態を取得 (not_started/active/ended)

#### TestDefinitionモデル  
- **`is_input_allowed()`**: 現在、得点入力が許可されているかどうか
- **`get_input_status()`**: 入力状況の詳細を取得（理由、状態、日程含む）

### 2. API拡張 (`tests/views.py`)

#### 新規エンドポイント
- **`GET /api/tests/{id}/input_status/`**: テストの入力可能状況を取得

#### 既存エンドポイント拡張
- **`test_structure`**: 入力ステータス情報を追加
- **`available_tests`**: 各テストの入力可否と期限情報を追加

### 3. 得点提出API制限 (`scores/views.py`)
- **`submit_test_scores`**: 得点提出時に期間チェックを実行
- 期間外の場合は403エラーで詳細情報を返却

## 期間判定ロジック

### テスト期間の状態
1. **`not_started`**: テスト開始前 
   - 現在日時 < テスト開始日
2. **`active`**: テスト期間中（入力可能）
   - テスト開始日 ≤ 現在日時 ≤ 締切日時
3. **`ended`**: テスト期間終了
   - 現在日時 > 締切日時

### 入力可否判定
```python
def is_input_allowed(self):
    return self.is_active and self.schedule.is_active_now()
```

## API レスポンス例

### 入力可能な場合
```json
{
  "test_id": 1,
  "test_info": {
    "year": 2024,
    "period": "spring",
    "period_display": "春期",
    "grade_level": "elementary",
    "subject": "japanese"
  },
  "input_status": {
    "allowed": true,
    "reason": "入力可能",
    "status": "active",
    "deadline": "2024-03-31T23:59:59Z"
  }
}
```

### 期間外の場合
```json
{
  "success": false,
  "error": "テスト期間が終了しています",
  "status": "ended",
  "input_status": {
    "allowed": false,
    "reason": "テスト期間が終了しています", 
    "status": "ended",
    "deadline": "2024-03-31T23:59:59Z"
  }
}
```

## フロントエンド連携

### 推奨実装フロー
1. **テスト一覧取得時**: `available_tests` APIで各テストの入力可否を確認
2. **テスト選択時**: `test_structure` APIでテスト詳細と入力ステータスを取得
3. **入力画面表示**: `input_allowed`フラグでフォームの有効/無効を制御
4. **得点提出時**: API側で期間チェック（二重チェック）

### UI表示例
```javascript
if (!testData.input_allowed) {
  // 入力フォームを無効化
  // メッセージ表示: testData.input_status.reason
  // 期限表示: testData.input_status.deadline
}
```

## セキュリティ機能

### フロントエンド制御
- 期間外は入力フォームを無効化
- 明確なメッセージで理由を表示
- 期限情報を表示

### バックエンド制御  
- 得点提出API で期間チェック
- 期間外提出は403エラーで拒否
- 詳細なエラー情報を返却

## テスト結果
✅ 期間判定ロジック正常動作  
✅ API エンドポイント動作確認  
✅ 得点提出制限動作確認  
✅ 詳細ステータス情報取得確認  

## 実装状況
- ✅ TestScheduleモデル期間判定機能
- ✅ TestDefinition入力制御機能  
- ✅ API入力ステータス情報追加
- ✅ 得点提出API期間制限
- ✅ 包括的テスト実行

フロントエンド側でこれらのAPIを活用することで、テスト期間外での不正な入力を効果的に防止できます。