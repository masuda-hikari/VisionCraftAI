# VisionCraftAI - ステータス

最終更新: 2026-01-08

## 現在の状況
- 状況: Phase 5 Stripe決済統合・クレジットシステム完了
- 進捗: テストスイート全パス（216 passed, 1 skipped）

## Phase 1 進捗（完了）
| タスク | 状態 |
|--------|------|
| プロジェクト構成セットアップ | 完了 |
| Gemini APIクライアント実装 | 完了 |
| プロンプトハンドラー実装 | 完了 |
| 画像後処理モジュール実装 | 完了 |
| 設定管理モジュール実装 | 完了 |
| テストスイート作成・実行 | 完了 |
| pyproject.toml作成 | 完了 |
| API接続確認 | 未実施（認証情報待ち） |

## Phase 2 進捗（完了）
| タスク | 状態 |
|--------|------|
| バッチ処理機能実装 | 完了 |
| リトライ機能実装 | 完了 |
| 使用量トラッキング機能実装 | 完了 |
| テストスイート拡充 | 完了 |
| API接続テスト | 未実施（認証情報待ち） |

## Phase 3 進捗（完了）
| タスク | 状態 |
|--------|------|
| FastAPI RESTful API実装 | 完了 |
| APIスキーマ・モデル定義 | 完了 |
| 画像生成エンドポイント | 完了 |
| バッチ処理エンドポイント | 完了 |
| 使用量・コスト管理エンドポイント | 完了 |
| プロンプト検証・拡張エンドポイント | 完了 |
| APIテスト作成・実行 | 完了 |

## Phase 4 進捗（完了）
| タスク | 状態 |
|--------|------|
| 認証モデル定義（APIKey, UsageQuota） | 完了 |
| APIキー管理（生成・検証・CRUD） | 完了 |
| レート制限（スライディングウィンドウ方式） | 完了 |
| FastAPI依存性注入・ミドルウェア | 完了 |
| プラン階層別クォータ管理 | 完了 |
| 認証テスト | 完了 |

## Phase 5 進捗（完了）
| タスク | 状態 |
|--------|------|
| 決済モデル定義（Subscription, CreditBalance） | 完了 |
| Stripeクライアント実装（テストモード対応） | 完了 |
| サブスクリプション管理モジュール | 完了 |
| クレジット管理モジュール | 完了 |
| 決済エンドポイント実装 | 完了 |
| Webhook処理実装 | 完了 |
| 決済テスト52件 | 完了 |

## 次のアクション
1. Google Cloud認証情報の設定・API接続テスト
2. Stripe本番環境設定（APIキー、価格ID登録）
3. 簡易Webインターフェースの作成
4. ユーザー登録・アカウント管理機能
5. 本番デプロイ準備

## ブロッカー
- Google Cloud サービスアカウント認証情報が必要
- Stripe本番APIキー・Webhookシークレットが必要

## 実装済みモジュール
### コア
- `src/generator/gemini_client.py` - Gemini APIクライアント
- `src/generator/prompt_handler.py` - プロンプト処理・バリデーション
- `src/generator/batch_processor.py` - バッチ処理・レート制限
- `src/editor/post_processor.py` - 画像後処理
- `src/utils/config.py` - 設定管理
- `src/utils/retry.py` - リトライ・バックオフ
- `src/utils/usage_tracker.py` - 使用量トラッキング・コスト管理

### API
- `src/api/app.py` - FastAPIアプリケーション
- `src/api/routes.py` - APIルーター・エンドポイント
- `src/api/schemas.py` - Pydanticスキーマ定義

### 認証
- `src/api/auth/models.py` - APIKey, UsageQuota モデル
- `src/api/auth/key_manager.py` - APIキー管理（CRUD・永続化）
- `src/api/auth/rate_limiter.py` - レート制限（スライディングウィンドウ）
- `src/api/auth/dependencies.py` - FastAPI依存性注入
- `src/api/auth/schemas.py` - 認証スキーマ
- `src/api/auth/routes.py` - 認証エンドポイント

### 決済（新規）
- `src/api/payment/models.py` - Subscription, CreditBalance, CreditTransaction モデル
- `src/api/payment/stripe_client.py` - Stripe APIクライアント（テストモード対応）
- `src/api/payment/subscription_manager.py` - サブスクリプション管理
- `src/api/payment/credit_manager.py` - クレジット管理
- `src/api/payment/schemas.py` - 決済スキーマ
- `src/api/payment/routes.py` - 決済エンドポイント

## APIエンドポイント一覧
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/` | GET | 不要 | API情報 |
| `/api/v1/health` | GET | 不要 | ヘルスチェック |
| `/api/v1/generate` | POST | **必須** | 画像生成 |
| `/api/v1/batch/generate` | POST | **必須** | バッチ画像生成 |
| `/api/v1/batch/estimate` | POST | 不要 | 処理時間見積もり |
| `/api/v1/usage` | GET | 不要 | 使用量サマリー |
| `/api/v1/usage/daily` | GET | 不要 | 日別使用量 |
| `/api/v1/usage/export` | POST | 不要 | レポートエクスポート |
| `/api/v1/prompt/validate` | POST | 不要 | プロンプト検証 |
| `/api/v1/prompt/enhance` | POST | 不要 | プロンプト拡張 |

### 認証エンドポイント
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/api/v1/auth/keys` | POST | 不要 | APIキー作成 |
| `/api/v1/auth/keys` | GET | **必須** | APIキー一覧 |
| `/api/v1/auth/keys/me` | GET | **必須** | 現在のキー情報 |
| `/api/v1/auth/keys/{key_id}` | PATCH | **必須** | キー更新 |
| `/api/v1/auth/keys/{key_id}` | DELETE | **必須** | キー削除 |
| `/api/v1/auth/quota` | GET | **必須** | クォータ状況 |
| `/api/v1/auth/usage` | GET | **必須** | 使用量詳細 |
| `/api/v1/auth/rate-limit` | GET | **必須** | レート制限状況 |
| `/api/v1/auth/verify` | GET | **必須** | 認証確認 |

### 決済エンドポイント（新規）
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/api/v1/payment/plans` | GET | 不要 | プラン一覧 |
| `/api/v1/payment/subscriptions` | POST | **必須** | サブスクリプション作成 |
| `/api/v1/payment/subscriptions/me` | GET | **必須** | サブスクリプション状況 |
| `/api/v1/payment/subscriptions/me` | PATCH | **必須** | プラン変更 |
| `/api/v1/payment/subscriptions/me/cancel` | POST | **必須** | サブスクリプションキャンセル |
| `/api/v1/payment/credits/packages` | GET | 不要 | クレジットパッケージ一覧 |
| `/api/v1/payment/credits/balance` | GET | **必須** | クレジット残高 |
| `/api/v1/payment/credits/purchase` | POST | **必須** | クレジット購入 |
| `/api/v1/payment/credits/transactions` | GET | **必須** | 取引履歴 |
| `/api/v1/payment/webhook` | POST | 不要 | Stripe Webhook |

## プラン階層
| プラン | 月間制限 | 日間制限 | 最大解像度 | バッチ上限 | 価格 |
|--------|---------|---------|-----------|----------|------|
| Free | 5枚 | 3枚 | 512x512 | 1 | 無料 |
| Basic | 100枚 | 20枚 | 1024x1024 | 10 | $9.99/月 |
| Pro | 500枚 | 50枚 | 2048x2048 | 50 | $29.99/月 |
| Enterprise | 無制限 | 無制限 | 4096x4096 | 100 | $99.99/月 |

## クレジットパッケージ（新規）
| パッケージ | クレジット | ボーナス | 価格 |
|-----------|-----------|---------|------|
| credits_10 | 10 | 0 | $4.99 |
| credits_50 | 50 | +5 | $19.99 |
| credits_100 | 100 | +15 | $34.99 |
| credits_500 | 500 | +100 | $149.99 |

## 最近の変更
- 2026-01-08: Phase 5 Stripe決済統合完了
  - 決済モデル定義（Subscription, CreditBalance, CreditTransaction）
  - Stripeクライアント実装（テストモード・本番モード対応）
  - サブスクリプション管理（作成・更新・キャンセル）
  - クレジットシステム（購入・使用・ボーナス・履歴）
  - 決済エンドポイント実装
  - Webhook処理（checkout.session.completed, subscription.updated等）
  - 決済テスト52件追加
  - 全216テストパス
- 2026-01-08: Phase 4 認証・認可システム実装
- 2026-01-08: Phase 3 FastAPI RESTful API実装
- 2026-01-08: Phase 2 コア機能拡充
- 2026-01-08: Phase 1 コアモジュール実装

## 起動方法
```bash
# 開発サーバー起動
python -m src.api.app

# または
uvicorn src.api.app:app --reload --port 8000

# APIドキュメント
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

## 認証方法
```bash
# APIキー作成
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"tier": "basic", "name": "My App"}'

# 画像生成（認証付き）
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vca_xxxxxxxx.xxxxxxxx" \
  -d '{"prompt": "A beautiful sunset"}'
```

## サブスクリプション作成
```bash
# サブスクリプション作成（Freeプラン）
curl -X POST http://localhost:8000/api/v1/payment/subscriptions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vca_xxxxxxxx.xxxxxxxx" \
  -d '{"email": "user@example.com", "plan_id": "free"}'

# サブスクリプション作成（有料プラン）
curl -X POST http://localhost:8000/api/v1/payment/subscriptions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vca_xxxxxxxx.xxxxxxxx" \
  -d '{"email": "user@example.com", "plan_id": "basic"}'
# → checkout_url にリダイレクトして決済完了
```

## クレジット購入
```bash
# クレジット購入Intent作成
curl -X POST http://localhost:8000/api/v1/payment/credits/purchase \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vca_xxxxxxxx.xxxxxxxx" \
  -d '{"package_id": "credits_50"}'
# → client_secret を使用してStripe.jsで決済完了
```
