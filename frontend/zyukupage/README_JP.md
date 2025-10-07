# 全国学力向上テスト – School Admin Dashboard

塾本部向けの年度・期・締切・帳票を一元管理できるB2Bダッシュボードシステム

## 🚀 プロジェクト概要

全国学力向上テストは、塾・学習塾の本部管理者向けに開発された包括的な管理システムです。生徒管理、テスト管理、スコア入力、帳票生成、請求管理などの機能を統合し、効率的な教育事業運営を支援します。

## 📋 主要機能

### 🎯 ダッシュボード
- 年度・期別のKPI監視
- 生徒数・売上・完了率の可視化
- 締切カウントダウン表示
- リアルタイムデータ更新

### 👥 生徒管理
- 生徒情報の CRUD 操作
- CSV インポート/エクスポート
- 教室別フィルタリング
- 生徒ID自動発番機能

### 📝 テスト管理
- 問題・解答ファイルのダウンロード
- 段階的スコア入力ウィザード
- 大問・小問の詳細入力
- Excel一括取込機能

### 📊 結果分析
- 正答率グラフ表示
- 生徒別成績一覧
- 帳票生成・プレビュー
- 一括ZIP対応

### ⚙️ 設定管理
- テスト日程管理
- 塾プロフィール設定
- コメントテンプレート
- 請求金額自動計算

## 🛠️ 技術スタック

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **UI Components**: shadcn/ui, Radix UI
- **State Management**: @tanstack/react-query
- **Styling**: Tailwind CSS v3.4, Framer Motion
- **Font**: Noto Sans JP
- **Testing**: Vitest, Testing Library
- **Code Quality**: ESLint, Prettier, Husky
- **Mock API**: MSW (Mock Service Worker)

## 📁 プロジェクト構成

```
autograder-pro-dashboard/
├── app/                          # Next.js App Router
│   ├── dashboard/               # ダッシュボード
│   ├── students/                # 生徒管理
│   ├── tests/[year]/[period]/   # テスト管理
│   ├── settings/                # 設定
│   └── admin/                   # 管理機能
├── components/                   # 再利用可能コンポーネント
│   ├── layout/                  # レイアウトコンポーネント
│   ├── ui/                      # UIコンポーネント
│   ├── students/                # 生徒関連コンポーネント
│   └── tests/                   # テスト関連コンポーネント
├── lib/                         # ユーティリティ
├── hooks/                       # カスタムフック
└── public/                      # 静的ファイル
```

## 🎨 デザインシステム

### カラーパレット
- **Primary**: #5BC0EB (メインブルー)
- **Accent**: #9BC53D (アクセントグリーン)
- **Warning**: #FDE74C (警告イエロー)
- **Danger**: #E55934 (エラーレッド)

### デザイン原則
- Apple レベルのデザイン品質
- 直感的なユーザーエクスペリエンス
- レスポンシブデザイン
- ダーク/ライトモード対応
- アクセシビリティ配慮

## 🚀 開発環境セットアップ

### 1. 依存関係インストール
```bash
npm install
```

### 2. 環境変数設定
```bash
cp .env.example .env.local
# 必要に応じて環境変数を編集
```

### 3. 開発サーバー起動
```bash
npm run dev
```

### 4. ブラウザでアクセス
```
http://localhost:3000
```

## 🔐 認証情報

### デモアカウント
- **Email**: admin@school.com
- **Password**: password
- **Role**: school_admin

## 📊 API エンドポイント

### 生徒管理
- `GET /api/students` - 生徒一覧取得
- `POST /api/students` - 生徒登録
- `GET /api/students/next-id` - 生徒ID自動発番
- `GET /api/students/export` - CSV エクスポート

### テスト管理
- `GET /api/test-schedule` - テスト日程取得
- `PATCH /api/test-schedule/{id}` - 日程更新
- `POST /api/scores/bulk` - スコア一括登録
- `GET /api/tests/{year}/{period}/files` - テストファイル一覧

### 帳票・レポート
- `GET /api/reports/bulk` - 帳票一括取得
- `POST /api/mail/reports/bulk` - 帳票メール送信
- `GET /api/reports/preview/{id}` - 帳票プレビュー

### 請求管理
- `GET /api/billing/summary` - 請求サマリー
- `POST /api/billing/export` - 請求データエクスポート

## 🧪 テスト

### 単体テスト実行
```bash
npm run test
```

### ウォッチモード
```bash
npm run test:watch
```

### テストUI
```bash
npm run test:ui
```

## 📝 コード品質

### リンター実行
```bash
npm run lint
```

### フォーマッター実行
```bash
npm run format
```

### フォーマット確認
```bash
npm run format:check
```

## 🔄 Django API 連携

### 推奨Django設定
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend-domain.com",
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

### APIレスポンス形式
```json
{
  "status": "success",
  "data": {...},
  "message": "操作が完了しました",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 📈 運用フロー

### 1. 年度・期設定
1. 設定 > テスト日程で新しい年度・期を追加
2. 予定日、実施日、締切日時を設定

### 2. 生徒データ準備
1. 生徒管理でテンプレートをダウンロード
2. 生徒情報を入力してCSVインポート

### 3. テスト実施
1. テスト管理で問題・解答ファイルをダウンロード
2. 実施後、スコア入力ウィザードで成績入力

### 4. 結果処理
1. 結果確認画面で分析・確認
2. 帳票生成・メール送信
3. 請求管理で課金処理

## 🚀 本番環境デプロイ

### 1. ビルド
```bash
npm run build
```

### 2. 静的ファイル出力
```bash
npm run export
```

### 3. 環境変数設定
本番環境で以下の環境変数を設定:
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_MOCK_API=false`

## 🤝 貢献

1. フォークしてブランチを作成
2. 機能追加・バグ修正
3. テスト追加・実行
4. プルリクエスト作成

## 📄 ライセンス

This project is licensed under the MIT License.

## 🆘 サポート

技術的な問題や機能要望については、GitHub Issues をご利用ください。

---

**全国学力向上テスト** - 教育事業の効率化を支援する包括的な管理システム