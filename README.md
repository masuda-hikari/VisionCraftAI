# VisionCraftAI

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-598%20passed-brightgreen.svg)](#テスト)
[![Coverage](https://img.shields.io/badge/Coverage-80%25-brightgreen.svg)](#テスト)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#ライセンス)

**最先端AI技術を活用した高品質画像生成プラットフォーム**

最先端AIモデルによるプロフェッショナル品質のAI画像生成サービス。RESTful API、Webインターフェース、Stripe決済統合を完備。

---

## 主な機能

| 機能 | 説明 |
|------|------|
| **AI画像生成** | Google Gemini 3による最高品質の画像生成 |
| **RESTful API** | 開発者向けの完全なAPIアクセス |
| **Webインターフェース** | 直感的なブラウザベースのUI |
| **バッチ処理** | 複数画像の一括生成 |
| **サブスクリプション** | Stripe統合による柔軟な課金 |
| **クレジット購入** | 従量課金オプション |
| **管理者ダッシュボード** | 収益・使用量のリアルタイム監視 |
| **ユーザーダッシュボード** | セルフサービスでの利用管理 |
| **本番運用監視** | Prometheus対応メトリクス・ヘルスチェック |
| **年額プラン** | 20%割引の年間サブスクリプション |
| **PWA対応** | オフライン対応・ホーム画面追加対応 |
| **画像ギャラリー** | 生成履歴保存・ライトボックス表示 |
| **モバイル対応** | レスポンシブUI・ハンバーガーメニュー |

---

## デモ

**デモモード**を使用して、APIキーなしで機能をお試しいただけます。

```bash
# サーバー起動
python -m src.api.app

# デモ画像生成（認証不要）
curl -X POST http://localhost:8000/api/v1/demo/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A beautiful sunset over mountains"}'
```

ブラウザで http://localhost:8000 にアクセスしてWebインターフェースをお試しください。

---

## クイックスタート

### 前提条件

- Python 3.12以上
- Google Cloud アカウント（本番利用時）
- Stripe アカウント（決済機能利用時）

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/VisionCraftAI.git
cd VisionCraftAI

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt
```

### 環境設定

```bash
# .env.exampleをコピー
cp .env.example .env

# 必要に応じて編集
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
# GOOGLE_CLOUD_PROJECT=your-project-id
# STRIPE_API_KEY=sk_test_xxx
```

### サーバー起動

```bash
# 開発モード
python -m src.api.app

# または
uvicorn src.api.app:app --reload --port 8000
```

### アクセス先

| URL | 説明 |
|-----|------|
| http://localhost:8000 | ランディングページ |
| http://localhost:8000/docs | Swagger UI（APIドキュメント） |
| http://localhost:8000/dashboard | ユーザーダッシュボード |
| http://localhost:8000/admin | 管理者ダッシュボード |

---

## API使用例

### APIキー作成

```bash
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"tier": "basic", "name": "My App"}'
```

### 画像生成（認証付き）

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vca_xxxxxxxx.xxxxxxxx" \
  -d '{"prompt": "A beautiful sunset over mountains", "width": 1024, "height": 1024}'
```

### バッチ生成

```bash
curl -X POST http://localhost:8000/api/v1/batch/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vca_xxxxxxxx.xxxxxxxx" \
  -d '{
    "prompts": [
      "Mountain landscape",
      "Ocean sunset",
      "City skyline"
    ],
    "width": 1024,
    "height": 1024
  }'
```

詳細は [APIクイックスタートガイド](docs/API_QUICKSTART.md) をご参照ください。

---

## 料金プラン

| プラン | 月額 | 月間制限 | 最大解像度 | バッチ上限 |
|--------|------|---------|-----------|----------|
| **Free** | 無料 | 5枚 | 512x512 | 1 |
| **Basic** | $9.99 | 100枚 | 1024x1024 | 10 |
| **Pro** | $29.99 | 500枚 | 2048x2048 | 50 |
| **Enterprise** | $99.99 | 無制限 | 4096x4096 | 100 |

### クレジットパッケージ

追加クレジットを購入して、月間制限を超えた画像生成が可能です。

| パッケージ | クレジット | ボーナス | 価格 |
|-----------|-----------|---------|------|
| Small | 10 | - | $4.99 |
| Medium | 50 | +5 | $19.99 |
| Large | 100 | +15 | $34.99 |
| Mega | 500 | +100 | $149.99 |

---

## プロジェクト構成

```
VisionCraftAI/
├── src/
│   ├── api/                    # FastAPI アプリケーション
│   │   ├── app.py              # メインアプリ
│   │   ├── routes.py           # APIルーター
│   │   ├── schemas.py          # Pydanticスキーマ
│   │   ├── auth/               # 認証・認可
│   │   ├── payment/            # Stripe決済
│   │   ├── admin/              # 管理者機能
│   │   ├── demo_routes.py      # デモAPI
│   │   ├── contact_routes.py   # お問い合わせ
│   │   └── monitoring_routes.py # モニタリング
│   ├── generator/              # 画像生成モジュール
│   │   ├── gemini_client.py    # Gemini APIクライアント
│   │   ├── prompt_handler.py   # プロンプト処理
│   │   └── batch_processor.py  # バッチ処理
│   ├── editor/                 # 画像編集モジュール
│   │   └── post_processor.py   # 後処理
│   └── utils/                  # ユーティリティ
│       ├── config.py           # 設定管理
│       ├── retry.py            # リトライ・バックオフ
│       ├── usage_tracker.py    # 使用量追跡
│       └── monitoring.py       # ヘルスチェック・メトリクス
├── templates/                  # HTMLテンプレート
├── static/                     # 静的ファイル
├── tests/                      # テストスイート（420件）
├── scripts/                    # デプロイスクリプト
├── docs/                       # ドキュメント
└── .github/                    # CI/CD設定
```

---

## デプロイ

### Docker

```bash
# イメージビルド
docker build -t visioncraftai .

# コンテナ起動
docker run -p 8000:8000 --env-file .env visioncraftai
```

### Google Cloud Run

```bash
# 1. Google Cloud セットアップ
python scripts/setup_gcloud.py --project YOUR_PROJECT_ID

# 2. Stripe セットアップ
python scripts/setup_stripe.py --api-key sk_live_xxx --webhook-url https://your-domain.com

# 3. Cloud Run デプロイ
python scripts/deploy_cloudrun.py --project YOUR_PROJECT_ID
```

詳細は [デプロイガイド](docs/DEPLOY_GUIDE.md) をご参照ください。

---

## テスト

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付き
pytest tests/ --cov=src --cov-report=html

# 特定カテゴリのみ
pytest tests/test_api.py -v        # APIテスト
pytest tests/test_auth.py -v       # 認証テスト
pytest tests/test_payment.py -v    # 決済テスト
pytest tests/test_monitoring.py -v # モニタリングテスト
```

**現在の状態**: 420テスト全パス（カバレッジ80%）

---

## モニタリング

### ヘルスチェック

| エンドポイント | 用途 |
|---------------|------|
| `/api/v1/monitoring/liveness` | Kubernetes Liveness Probe |
| `/api/v1/monitoring/readiness` | Kubernetes Readiness Probe |
| `/api/v1/monitoring/health` | 詳細ヘルスチェック |

### メトリクス

```bash
# JSONメトリクス
curl http://localhost:8000/api/v1/monitoring/metrics

# Prometheus形式
curl http://localhost:8000/api/v1/monitoring/metrics/prometheus
```

---

## セキュリティ

- **APIキー認証**: 全ての画像生成APIはAPIキー必須
- **レート制限**: スライディングウィンドウ方式
- **入力検証**: プロンプトのサニタイズ・不適切コンテンツフィルタ
- **Banditスキャン**: 自動セキュリティ監査

**重要**: APIキー・認証情報は絶対にコードにハードコードしないでください。

---

## ドキュメント

- [ユーザーガイド](docs/USER_GUIDE.md)
- [APIクイックスタート](docs/API_QUICKSTART.md)
- [デプロイガイド](docs/DEPLOY_GUIDE.md)
- [マーケティング戦略](docs/MARKETING_STRATEGY.md)

---

## ライセンス

Proprietary - All Rights Reserved

---

## お問い合わせ

- **Web**: http://localhost:8000/contact
- **Email**: contact@visioncraftai.example.com

---

## 開発状況

| Phase | 内容 | 状態 |
|-------|------|------|
| Phase 1-6 | 基盤・認証・決済・UI | ✅ 完了 |
| Phase 7-8 | デプロイ準備・自動化 | ✅ 完了 |
| Phase 9 | CI/CD・セキュリティ | ✅ 完了 |
| Phase 10 | マーケティング準備・デモ | ✅ 完了 |
| Phase 11 | ドキュメント・法的ページ | ✅ 完了 |
| Phase 12 | 管理者ダッシュボード | ✅ 完了 |
| Phase 13 | ユーザーダッシュボード | ✅ 完了 |
| Phase 14 | 本番運用監視 | ✅ 完了 |
| Phase 15 | ローンチ準備 | ✅ 完了 |
| Phase 16 | テストカバレッジ80% | ✅ 完了 |
| Phase 17 | 年額プラン・モバイル対応 | ✅ 完了 |
| Phase 18 | SEO・アクセシビリティ | ✅ 完了 |
| Phase 19 | PWA化・UX強化 | ✅ 完了 |
| Phase 20 | 本番デプロイ | ⏳ 認証情報待ち |
