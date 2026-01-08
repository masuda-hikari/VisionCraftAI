# VisionCraftAI - ステータス

最終更新: 2026-01-08

## 現在の状況
- 状況: Phase 4 認証・認可システム完了
- 進捗: テストスイート全パス（164 passed, 1 skipped）

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
| テストスイート拡充 | 完了（86テスト全パス） |
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
| APIテスト作成・実行 | 完了（30テスト追加） |

## Phase 4 進捗（完了）
| タスク | 状態 |
|--------|------|
| 認証モデル定義（APIKey, UsageQuota） | 完了 |
| APIキー管理（生成・検証・CRUD） | 完了 |
| レート制限（スライディングウィンドウ方式） | 完了 |
| FastAPI依存性注入・ミドルウェア | 完了 |
| プラン階層別クォータ管理 | 完了 |
| 認証テスト（46テスト） | 完了 |
| 既存APIテスト更新 | 完了 |

## 次のアクション
1. Google Cloud認証情報の設定・API接続テスト
2. Phase 5: Stripe決済統合・クレジットシステム
3. Phase 5: 簡易Webインターフェースの作成
4. ユーザー登録・アカウント管理機能

## ブロッカー
- Google Cloud サービスアカウント認証情報が必要

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

### 認証（新規）
- `src/api/auth/models.py` - APIKey, UsageQuota モデル
- `src/api/auth/key_manager.py` - APIキー管理（CRUD・永続化）
- `src/api/auth/rate_limiter.py` - レート制限（スライディングウィンドウ）
- `src/api/auth/dependencies.py` - FastAPI依存性注入
- `src/api/auth/schemas.py` - 認証スキーマ
- `src/api/auth/routes.py` - 認証エンドポイント

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

### 認証エンドポイント（新規）
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

## プラン階層
| プラン | 月間制限 | 日間制限 | 最大解像度 | バッチ上限 | 価格 |
|--------|---------|---------|-----------|----------|------|
| Free | 5枚 | 3枚 | 512x512 | 1 | 無料 |
| Basic | 100枚 | 20枚 | 1024x1024 | 10 | $9.99/月 |
| Pro | 500枚 | 50枚 | 2048x2048 | 50 | $29.99/月 |
| Enterprise | 無制限 | 無制限 | 4096x4096 | 100 | 要見積 |

## 最近の変更
- 2026-01-08: Phase 4 認証・認可システム実装
  - APIキーモデル・クォータ管理（models.py）
  - キー生成・検証・CRUD（key_manager.py）
  - スライディングウィンドウレート制限（rate_limiter.py）
  - FastAPI依存性注入（dependencies.py）
  - 認証エンドポイント（routes.py）
  - 認証テスト46件追加（test_auth.py）
  - 既存APIテスト更新（認証ヘッダー対応）
  - 全164テストパス
- 2026-01-08: Phase 3 FastAPI RESTful API実装
- 2026-01-08: Phase 2 コア機能拡充
- 2026-01-08: パッケージ構造修正、pyproject.toml作成
- 2026-01-08: Phase 1 コアモジュール実装
- 2026-01-07: オーケストレーター統合

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

# または Authorization ヘッダー
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Authorization: Bearer vca_xxxxxxxx.xxxxxxxx" \
  -d '{"prompt": "A beautiful sunset"}'
```
