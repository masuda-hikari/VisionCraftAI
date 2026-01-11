﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿# VisionCraftAI - ステータス

最終更新: 2026-01-11

## 現在の状況
- 状況: デプロイ準備完了（ブロッカー解消待ち）
- 進捗: テストスイート全パス（598 passed, 1 skipped）
- 警告: 1件のみ（外部ライブラリ由来）
- カバレッジ: 80%+
- デプロイ可能: Render.com / Vercel / Cloudflare / Railway / Fly.io
- ガバナンス: LLM名称露出禁止ルール準拠
- 自動化: quick_deploy.py でブロッカー確認可能

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

## Phase 6 進捗（完了）
| タスク | 状態 |
|--------|------|
| ランディングページHTML/CSS | 完了 |
| フロントエンドJavaScript | 完了 |
| 静的ファイル配信設定（FastAPI） | 完了 |
| テンプレートエンジン統合（Jinja2） | 完了 |
| デモ機能（画像生成UI） | 完了 |
| 料金プラン表示 | 完了 |

## Phase 7 進捗（完了）
| タスク | 状態 |
|--------|------|
| Dockerfile作成（マルチステージビルド） | 完了 |
| docker-compose.yml作成 | 完了 |
| .env.example更新（Stripe設定追加） | 完了 |
| デプロイガイド作成 | 完了 |

## Phase 8 進捗（完了）
| タスク | 状態 |
|--------|------|
| Google Cloud セットアップスクリプト（setup_gcloud.py） | 完了 |
| Cloud Run デプロイスクリプト（deploy_cloudrun.py） | 完了 |
| Stripe セットアップスクリプト（setup_stripe.py） | 完了 |

## Phase 9 進捗（完了）
| タスク | 状態 |
|--------|------|
| GitHub Actions CI/CDワークフロー | 完了 |
| Dependabot設定（依存関係自動更新） | 完了 |
| セキュリティスキャン（Bandit） | 完了 |
| CORS設定の環境変数化 | 完了 |
| ServerConfig追加 | 完了 |

## Phase 10 進捗（完了）
| タスク | 状態 |
|--------|------|
| マーケティング戦略ドキュメント作成 | 完了 |
| SEO最適化（meta tags, schema.org, Open Graph） | 完了 |
| E2Eテスト15件追加 | 完了 |
| デモAPI実装（/api/v1/demo/*） | 完了 |
| デモ画像生成（SVGプレースホルダー） | 完了 |
| フロントエンドデモモード対応 | 完了 |
| デモテスト21件追加 | 完了 |

## Phase 11 進捗（完了）
| タスク | 状態 |
|--------|------|
| ユーザーガイド作成（docs/USER_GUIDE.md） | 完了 |
| APIクイックスタートガイド作成（docs/API_QUICKSTART.md） | 完了 |
| 利用規約ページ（templates/terms.html） | 完了 |
| プライバシーポリシーページ（templates/privacy.html） | 完了 |
| お問い合わせページ（templates/contact.html） | 完了 |
| お問い合わせAPI（src/api/contact_routes.py） | 完了 |
| お問い合わせテスト17件追加 | 完了 |
| フッターリンク更新 | 完了 |

## Phase 12 進捗（完了）
| タスク | 状態 |
|--------|------|
| 管理者ダッシュボード機能（AdminDashboard） | 完了 |
| 管理者APIエンドポイント（/api/v1/admin/*） | 完了 |
| 管理者ダッシュボードページ（templates/admin.html） | 完了 |
| 収益・ユーザー・使用量メトリクス | 完了 |
| チャートデータAPI（収益・使用量推移） | 完了 |
| システムヘルス監視 | 完了 |
| お問い合わせ統計 | 完了 |
| 管理者テスト31件追加 | 完了 |

## Phase 13 進捗（完了）
| タスク | 状態 |
|--------|------|
| ユーザーダッシュボードページ（templates/dashboard.html） | 完了 |
| ダッシュボードCSS（static/css/dashboard.css） | 完了 |
| ダッシュボードJS（static/js/dashboard.js） | 完了 |
| ログイン/ログアウト機能 | 完了 |
| サブスクリプション管理UI | 完了 |
| 使用量表示UI | 完了 |
| APIキー管理UI | 完了 |
| クレジット管理UI | 完了 |
| ナビゲーションリンク追加 | 完了 |
| ダッシュボードテスト18件追加 | 完了 |

## Phase 14 進捗（完了）
| タスク | 状態 |
|--------|------|
| モニタリングモジュール実装（src/utils/monitoring.py） | 完了 |
| ヘルスチェッカー（複数コンポーネント対応） | 完了 |
| メトリクスコレクター（Prometheus対応） | 完了 |
| 構造化ロガー（JSON出力） | 完了 |
| Kubernetes Liveness/Readiness Probe | 完了 |
| モニタリングAPIエンドポイント（/api/v1/monitoring/*） | 完了 |
| モニタリングテスト28件追加 | 完了 |

## Phase 15 進捗（完了）
| タスク | 状態 |
|--------|------|
| Banditセキュリティスキャン・修正 | 完了 |
| README.md大幅更新（バッジ・機能一覧・デモ） | 完了 |
| Product Huntローンチコピー作成 | 完了 |
| ロードテストスクリプト作成 | 完了 |

## Phase 15+ 進捗（完了）
| タスク | 状態 |
|--------|------|
| Stripeクライアントテスト強化（24件追加） | 完了 |
| pyproject.toml本番メタデータ完備（v1.0.0） | 完了 |
| テストカバレッジ向上（76%→77%） | 完了 |

## Phase 16 進捗（完了）
| タスク | 状態 |
|--------|------|
| payment/routes.pyテスト追加（44%→84%） | 完了 |
| subscription_manager.pyテスト追加（64%→79%） | 完了 |
| auth/dependencies.pyテスト追加（52%→56%） | 完了 |
| テストカバレッジ80%達成（+39件） | 完了 |

## Phase 17 進捗（完了）
| タスク | 状態 |
|--------|------|
| 年額/月額切り替えトグルUI実装 | 完了 |
| 年額プラン価格表示（割引%OFF表示） | 完了 |
| モバイルレスポンシブ最適化 | 完了 |
| ハンバーガーメニュー実装 | 完了 |
| 年額プランテスト10件追加 | 完了 |
| テスト420件全パス | 完了 |

## Phase 18 進捗（完了）
| タスク | 状態 |
|--------|------|
| Critical CSS（above-the-fold）実装 | 完了 |
| CSS/フォント遅延読み込み（LCP最適化） | 完了 |
| WebSite構造化データ追加 | 完了 |
| BreadcrumbList構造化データ追加 | 完了 |
| Core Web Vitals計測（LCP/CLS） | 完了 |
| スキップリンク実装（アクセシビリティ） | 完了 |
| ARIA属性追加（navigation/main/footer） | 完了 |
| フォーカス表示強化（:focus-visible） | 完了 |
| 減少モーション対応（prefers-reduced-motion） | 完了 |
| テスト420件全パス確認 | 完了 |

## Phase 19 進捗（完了）
| タスク | 状態 |
|--------|------|
| 画像ライトボックス実装（拡大・ダウンロード・共有） | 完了 |
| 画像ギャラリー機能（生成履歴・削除） | 完了 |
| サービスワーカー実装（オフライン対応） | 完了 |
| PWAマニフェスト作成 | 完了 |
| キャッシュ戦略実装（stale-while-revalidate） | 完了 |
| フロントエンドJS統合（app.js・lightbox.js連携） | 完了 |
| PWAアイコンプレースホルダー作成 | 完了 |
| テスト420件全パス確認 | 完了 |

## Phase 20 進捗（完了）
| タスク | 状態 |
|--------|------|
| 多言語対応（i18n）モジュール実装 | 完了 |
| 日本語/英語翻訳データ作成 | 完了 |
| 言語切り替えUI（JA/ENトグル） | 完了 |
| index.htmlにdata-i18n属性追加 | 完了 |
| ブラウザ言語自動検出 | 完了 |
| localStorage言語設定保存 | 完了 |
| hreflang多言語SEO対応 | 完了 |
| テスト420件全パス確認 | 完了 |

## Phase 21 進捗（完了）
| タスク | 状態 |
|--------|------|
| ShareManager クラス実装 | 完了 |
| SNS共有ボタン（Twitter/Facebook/LINE/Pinterest） | 完了 |
| 共有モーダルUI実装 | 完了 |
| 共有CSSスタイル作成 | 完了 |
| ライトボックス共有機能統合 | 完了 |
| デモ結果に共有ボタン追加 | 完了 |
| i18n翻訳追加（日本語/英語） | 完了 |
| テスト420件全パス確認 | 完了 |

## Phase 22 進捗（完了）
| タスク | 状態 |
|--------|------|
| リファラル（紹介）システム実装 | 完了 |
| 紹介コード生成・管理 | 完了 |
| 紹介報酬（クレジット付与）機能 | 完了 |
| リファラルAPI（/api/v1/referral/*） | 完了 |
| リファラルテスト30件追加 | 完了 |
| オンボーディング進捗管理実装 | 完了 |
| 無料トライアル機能実装 | 完了 |
| オンボーディングAPI（/api/v1/onboarding/*） | 完了 |
| オンボーディングテスト37件追加 | 完了 |
| テスト487件全パス確認 | 完了 |

## Phase 23 進捗（完了）
| タスク | 状態 |
|--------|------|
| EmailServiceクラス実装（SMTP送信・開発モード対応） | 完了 |
| NotificationManagerクラス実装 | 完了 |
| メールテンプレート実装（日本語/英語） | 完了 |
| 通知設定モデル・スキーマ実装 | 完了 |
| 通知APIエンドポイント（/api/v1/notifications/*） | 完了 |
| 開封・クリックトラッキング機能 | 完了 |
| メール通知テスト45件追加 | 完了 |
| テスト532件全パス確認 | 完了 |

## Phase 24 進捗（完了）
| タスク | 状態 |
|--------|------|
| ABTestモデル実装（ABTest, ABTestVariant, ABTestAssignment） | 完了 |
| ABTestManagerクラス実装（テスト作成・管理・バリアント割り当て） | 完了 |
| AnalyticsTrackerクラス実装（イベント記録・統計） | 完了 |
| AnalyticsEventモデル実装（UTM・収益・デバイス情報） | 完了 |
| ConversionGoalモデル実装（目標管理・進捗追跡） | 完了 |
| ファネル分析・リテンション分析機能 | 完了 |
| 分析APIエンドポイント（/api/v1/analytics/*） | 完了 |
| 分析テスト66件追加 | 完了 |
| テスト598件全パス確認 | 完了 |

## Phase 25 進捗（完了）
| タスク | 状態 |
|--------|------|
| Vercelデプロイ設定（vercel.json, api/index.py） | 完了 |
| Cloudflare Workers設定（wrangler.toml, workers/index.js） | 完了 |
| Render.com設定（render.yaml） | 完了 |
| requirements.txt更新（pyproject.toml同期） | 完了 |
| デプロイガイド大幅更新（無料プラットフォーム追加） | 完了 |
| テスト598件全パス確認 | 完了 |

## Phase 26 進捗（完了）
| タスク | 状態 |
|--------|------|
| Pydantic ConfigDict移行（deprecation警告解消） | 完了 |
| datetime.utcnow() → datetime.now(UTC)移行 | 完了 |
| テストコードの警告修正 | 完了 |
| 警告238件→1件に削減 | 完了 |
| テスト598件全パス確認 | 完了 |

## 次のアクション

### クイックデプロイ
```bash
# ブロッカー確認スクリプトを実行
python scripts/quick_deploy.py
```

### ブロッカー（人間対応必要・4件）

1. **GitHubリポジトリをPublicに変更**（デプロイ前提）
   - 現状: リポジトリが非公開またはアクセス不可
   - 対応: GitHub Settings > Danger Zone > Change visibility > Public
   - または: Render.comでPrivateリポジトリ連携設定

2. **Google Cloud認証情報の設定**（本番AI生成機能用）
   ```bash
   gcloud auth login
   python scripts/setup_gcloud.py --project YOUR_PROJECT_ID
   ```

3. **.envファイル作成**
   ```bash
   cp .env.example .env
   # 必要な値を設定
   ```

4. **Stripe本番環境設定**（課金機能用）
   ```bash
   python scripts/setup_stripe.py --api-key sk_live_xxx --webhook-url https://your-domain.com
   ```

### ブロッカー解消後即時実行
5. **Render.comでデモモードデプロイ**
   - GitHubリポジトリを連携
   - render.yamlが自動検出
   - DEMO_MODE=true で起動

6. **本番デプロイ実行**（Google Cloud/Stripe設定後）
   ```bash
   python scripts/deploy_cloudrun.py --project YOUR_PROJECT_ID
   ```

### デプロイ後の作業
7. カスタムドメイン設定・SSL証明書
8. Product Huntローンチ
9. マーケティング・初期ユーザー獲得

## ブロッカーサマリー
| 項目 | 状態 | 対応者 |
|------|------|--------|
| GitHubリポジトリ公開設定 | 404 | 人間 |
| Google Cloud認証情報 | 未設定 | 人間 |
| .envファイル作成 | 未作成 | 人間 |
| Stripe本番APIキー | 未設定 | 人間 |

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
- `src/api/demo_routes.py` - デモAPIエンドポイント
- `src/api/contact_routes.py` - お問い合わせAPIエンドポイント
- `src/api/monitoring_routes.py` - モニタリングAPIエンドポイント

### モニタリング
- `src/utils/monitoring.py` - ヘルスチェック・メトリクス・構造化ロギング

### 管理者
- `src/api/admin/dashboard.py` - 管理者ダッシュボード機能
- `src/api/admin/routes.py` - 管理者APIエンドポイント
- `src/api/admin/schemas.py` - 管理者スキーマ定義

### 認証
- `src/api/auth/models.py` - APIKey, UsageQuota モデル
- `src/api/auth/key_manager.py` - APIキー管理（CRUD・永続化）
- `src/api/auth/rate_limiter.py` - レート制限（スライディングウィンドウ）
- `src/api/auth/dependencies.py` - FastAPI依存性注入
- `src/api/auth/schemas.py` - 認証スキーマ
- `src/api/auth/routes.py` - 認証エンドポイント

### 決済
- `src/api/payment/models.py` - Subscription, CreditBalance, CreditTransaction モデル
- `src/api/payment/stripe_client.py` - Stripe APIクライアント（テストモード対応）
- `src/api/payment/subscription_manager.py` - サブスクリプション管理
- `src/api/payment/credit_manager.py` - クレジット管理
- `src/api/payment/schemas.py` - 決済スキーマ
- `src/api/payment/routes.py` - 決済エンドポイント

### 通知
- `src/api/notifications/models.py` - NotificationPreference, EmailTemplate, EmailLog モデル
- `src/api/notifications/email_service.py` - SMTP送信サービス
- `src/api/notifications/templates.py` - メールテンプレート（日本語/英語）
- `src/api/notifications/manager.py` - 通知管理（設定・送信・ログ）
- `src/api/notifications/schemas.py` - 通知スキーマ
- `src/api/notifications/routes.py` - 通知エンドポイント

### 分析・A/Bテスト
- `src/api/analytics/models.py` - ABTest, ABTestVariant, AnalyticsEvent, ConversionGoal モデル
- `src/api/analytics/manager.py` - ABTestManager, AnalyticsTracker（テスト管理・分析）
- `src/api/analytics/schemas.py` - 分析・A/Bテストスキーマ
- `src/api/analytics/routes.py` - 分析APIエンドポイント

### フロントエンド
- `templates/index.html` - ランディングページ
- `templates/terms.html` - 利用規約ページ
- `templates/privacy.html` - プライバシーポリシーページ
- `templates/contact.html` - お問い合わせページ
- `templates/admin.html` - 管理者ダッシュボードページ
- `templates/dashboard.html` - ユーザーダッシュボードページ
- `static/css/style.css` - スタイルシート
- `static/css/dashboard.css` - ダッシュボードスタイル
- `static/js/app.js` - フロントエンドJavaScript
- `static/js/dashboard.js` - ダッシュボードJavaScript

### ドキュメント
- `docs/USER_GUIDE.md` - ユーザーガイド
- `docs/API_QUICKSTART.md` - APIクイックスタートガイド
- `docs/DEPLOY_GUIDE.md` - デプロイ手順書
- `docs/MARKETING_STRATEGY.md` - マーケティング戦略

### デプロイ
- `Dockerfile` - 本番用Dockerイメージ（マルチステージビルド）
- `docker-compose.yml` - Docker Compose設定（開発/本番）

### 自動化スクリプト
- `scripts/setup_gcloud.py` - Google Cloud環境セットアップ
- `scripts/deploy_cloudrun.py` - Cloud Runデプロイ自動化
- `scripts/setup_stripe.py` - Stripe本番環境セットアップ

### CI/CD
- `.github/workflows/ci.yml` - GitHub Actions CI/CDパイプライン
- `.github/dependabot.yml` - 依存関係自動更新設定

## APIエンドポイント一覧
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/` | GET | 不要 | ランディングページ / API情報 |
| `/terms` | GET | 不要 | 利用規約ページ |
| `/privacy` | GET | 不要 | プライバシーポリシーページ |
| `/contact` | GET | 不要 | お問い合わせページ |
| `/dashboard` | GET | 不要 | ユーザーダッシュボード |
| `/api/v1/health` | GET | 不要 | ヘルスチェック |
| `/api/v1/generate` | POST | **必須** | 画像生成 |
| `/api/v1/batch/generate` | POST | **必須** | バッチ画像生成 |
| `/api/v1/batch/estimate` | POST | 不要 | 処理時間見積もり |
| `/api/v1/usage` | GET | 不要 | 使用量サマリー |
| `/api/v1/usage/daily` | GET | 不要 | 日別使用量 |
| `/api/v1/usage/export` | POST | 不要 | レポートエクスポート |
| `/api/v1/prompt/validate` | POST | 不要 | プロンプト検証 |
| `/api/v1/prompt/enhance` | POST | 不要 | プロンプト拡張 |

### デモエンドポイント
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/api/v1/demo/samples` | GET | 不要 | デモサンプル一覧 |
| `/api/v1/demo/generate` | POST | 不要 | デモ画像生成 |
| `/api/v1/demo/info` | GET | 不要 | デモモード情報 |

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

### 決済エンドポイント
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

### お問い合わせエンドポイント
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/api/v1/contact` | POST | 不要 | お問い合わせ送信 |
| `/api/v1/contact/categories` | GET | 不要 | カテゴリ一覧 |

### 管理者エンドポイント
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/admin` | GET | 不要 | 管理者ダッシュボードページ |
| `/api/v1/admin/dashboard` | GET | **管理者** | ダッシュボード概要 |
| `/api/v1/admin/revenue` | GET | **管理者** | 収益メトリクス |
| `/api/v1/admin/users` | GET | **管理者** | ユーザーメトリクス |
| `/api/v1/admin/usage` | GET | **管理者** | 使用量メトリクス |
| `/api/v1/admin/plans` | GET | **管理者** | プラン分布 |
| `/api/v1/admin/users/list` | GET | **管理者** | ユーザー一覧 |
| `/api/v1/admin/charts/revenue` | GET | **管理者** | 収益チャートデータ |
| `/api/v1/admin/charts/usage` | GET | **管理者** | 使用量チャートデータ |
| `/api/v1/admin/health` | GET | **管理者** | システムヘルス |
| `/api/v1/admin/contacts/stats` | GET | **管理者** | お問い合わせ統計 |
| `/api/v1/admin/export` | GET | **管理者** | データエクスポート |

### モニタリングエンドポイント
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/api/v1/monitoring/liveness` | GET | 不要 | Kubernetes Liveness Probe |
| `/api/v1/monitoring/readiness` | GET | 不要 | Kubernetes Readiness Probe |
| `/api/v1/monitoring/health` | GET | 不要 | 詳細ヘルスチェック |
| `/api/v1/monitoring/metrics` | GET | 不要 | アプリメトリクス（JSON） |
| `/api/v1/monitoring/metrics/prometheus` | GET | 不要 | Prometheusメトリクス |

### リファラルエンドポイント
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/api/v1/referral/code` | POST | **必須** | 紹介コード作成 |
| `/api/v1/referral/code` | GET | **必須** | 自分の紹介コード取得 |
| `/api/v1/referral/validate` | GET | 不要 | 紹介コード検証 |
| `/api/v1/referral/apply` | POST | **必須** | 紹介コード適用 |
| `/api/v1/referral/referrals` | GET | **必須** | 自分の紹介一覧 |
| `/api/v1/referral/stats` | GET | **必須** | 紹介統計 |
| `/api/v1/referral/leaderboard` | GET | 不要 | 紹介ランキング |
| `/api/v1/referral/pending-rewards` | GET | **必須** | 報酬待ちリスト |

### オンボーディングエンドポイント
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/api/v1/onboarding/welcome` | GET | **必須** | ウェルカム情報 |
| `/api/v1/onboarding/progress` | GET | **必須** | 進捗取得 |
| `/api/v1/onboarding/hint` | GET | **必須** | 次ステップヒント |
| `/api/v1/onboarding/step/complete` | POST | **必須** | ステップ完了 |
| `/api/v1/onboarding/checklist/complete` | POST | **必須** | チェックリスト完了 |
| `/api/v1/onboarding/trial/start` | POST | **必須** | トライアル開始 |
| `/api/v1/onboarding/trial` | GET | **必須** | トライアル状況 |
| `/api/v1/onboarding/trial/use-credits` | POST | **必須** | クレジット使用 |
| `/api/v1/onboarding/trial/convert` | POST | **必須** | 有料転換 |
| `/api/v1/onboarding/trial/stats` | GET | **必須** | トライアル統計 |

### 通知エンドポイント
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/api/v1/notifications/types` | GET | 不要 | 通知タイプ一覧 |
| `/api/v1/notifications/service/status` | GET | 不要 | メールサービス状態 |
| `/api/v1/notifications/preferences` | GET | **必須** | 通知設定取得 |
| `/api/v1/notifications/preferences` | PATCH | **必須** | 通知設定更新 |
| `/api/v1/notifications/logs` | GET | **必須** | 送信ログ一覧 |
| `/api/v1/notifications/logs/{log_id}` | GET | **必須** | 送信ログ詳細 |
| `/api/v1/notifications/stats` | GET | **必須** | 自分の通知統計 |
| `/api/v1/notifications/stats/all` | GET | **管理者** | 全体通知統計 |
| `/api/v1/notifications/send` | POST | **管理者** | 通知送信 |
| `/api/v1/notifications/test` | POST | **管理者** | テストメール送信 |
| `/api/v1/notifications/unsubscribe` | POST | 不要 | 配信停止 |
| `/api/v1/notifications/track/open/{log_id}` | GET | 不要 | 開封トラッキング |
| `/api/v1/notifications/track/click/{log_id}` | GET | 不要 | クリックトラッキング |

### 分析・A/Bテストエンドポイント
| エンドポイント | メソッド | 認証 | 説明 |
|---------------|---------|------|------|
| `/api/v1/analytics/event-types` | GET | 不要 | イベントタイプ一覧 |
| `/api/v1/analytics/events` | POST | 不要 | イベント記録 |
| `/api/v1/analytics/events` | GET | 不要 | イベント一覧 |
| `/api/v1/analytics/stats/daily` | GET | 不要 | 日次統計 |
| `/api/v1/analytics/stats/summary` | GET | 不要 | サマリー統計 |
| `/api/v1/analytics/funnel` | POST | 不要 | ファネル分析 |
| `/api/v1/analytics/retention` | POST | 不要 | リテンション分析 |
| `/api/v1/analytics/goals` | POST | 不要 | ゴール作成 |
| `/api/v1/analytics/goals` | GET | 不要 | ゴール一覧 |
| `/api/v1/analytics/goals/{goal_id}` | GET | 不要 | ゴール詳細 |
| `/api/v1/analytics/ab-tests` | POST | 不要 | A/Bテスト作成 |
| `/api/v1/analytics/ab-tests` | GET | 不要 | A/Bテスト一覧 |
| `/api/v1/analytics/ab-tests/{test_id}` | GET | 不要 | A/Bテスト詳細 |
| `/api/v1/analytics/ab-tests/{test_id}/variants` | POST | 不要 | バリアント追加 |
| `/api/v1/analytics/ab-tests/{test_id}/start` | POST | 不要 | テスト開始 |
| `/api/v1/analytics/ab-tests/{test_id}/pause` | POST | 不要 | テスト一時停止 |
| `/api/v1/analytics/ab-tests/{test_id}/resume` | POST | 不要 | テスト再開 |
| `/api/v1/analytics/ab-tests/{test_id}/complete` | POST | 不要 | テスト完了 |
| `/api/v1/analytics/ab-tests/{test_id}/results` | GET | 不要 | テスト結果 |
| `/api/v1/analytics/ab-tests/{test_id}/assign` | POST | 不要 | バリアント割り当て |
| `/api/v1/analytics/ab-tests/{test_id}/assignment` | GET | 不要 | 割り当て取得 |
| `/api/v1/analytics/ab-tests/{test_id}/conversion` | POST | 不要 | コンバージョン記録 |
| `/api/v1/analytics/ab-tests/{test_id}` | DELETE | 不要 | テスト削除 |

## プラン階層
| プラン | 月間制限 | 日間制限 | 最大解像度 | バッチ上限 | 価格 |
|--------|---------|---------|-----------|----------|------|
| Free | 5枚 | 3枚 | 512x512 | 1 | 無料 |
| Basic | 100枚 | 20枚 | 1024x1024 | 10 | $9.99/月 |
| Pro | 500枚 | 50枚 | 2048x2048 | 50 | $29.99/月 |
| Enterprise | 無制限 | 無制限 | 4096x4096 | 100 | $99.99/月 |

## クレジットパッケージ
| パッケージ | クレジット | ボーナス | 価格 |
|-----------|-----------|---------|------|
| credits_10 | 10 | 0 | $4.99 |
| credits_50 | 50 | +5 | $19.99 |
| credits_100 | 100 | +15 | $34.99 |
| credits_500 | 500 | +100 | $149.99 |

## 最近の変更
- 2026-01-11: デプロイ準備・ブロッカー確認自動化
  - REVENUE_METRICS.md作成（ガバナンス必須ファイル）
  - quick_deploy.py作成（ブロッカー確認・対応手順自動表示）
  - テスト598件全パス再確認（22.75秒）
  - ブロッカー4件を明確化
  - 収益化直結: デプロイ自動化・収益追跡体制整備
- 2026-01-11: 商用化基準対応（LLM名称露出修正）
  - index.html: Google Gemini 3 → 最先端AI技術に変更
  - README.md: 同上 + Phase 26までの進捗更新
  - USER_GUIDE.md, PRODUCT_HUNT_LAUNCH.md, MARKETING_STRATEGY.md: 同上
  - admin.html: Gemini API → AI APIに変更
  - ガバナンス「LLM名称露出禁止」ルールに準拠
  - 収益化直結: プラットフォーム規約違反リスク排除・独自ブランド強化
- 2026-01-11: Phase 26 コード品質向上
  - Pydantic ConfigDict移行（deprecation警告解消）
  - datetime.utcnow() → datetime.now(UTC)移行（Python 3.17対応）
  - テストコードの警告修正
  - 警告238件→1件に大幅削減（残り1件は外部ライブラリ由来）
  - テスト598件全パス確認
  - 収益化直結: 本番品質コード・長期サポート可能
- 2026-01-11: Phase 25 マルチプラットフォームデプロイ対応
  - Vercelデプロイ設定（vercel.json, api/index.py）
  - Cloudflare Workers設定（wrangler.toml, workers/index.js）
  - Render.com設定（render.yaml）
  - requirements.txt更新（pyproject.toml同期）
  - デプロイガイド大幅更新（無料プラットフォーム追加）
  - 収益化直結: 認証情報待ちでもデモモードでの公開が可能に
- 2026-01-11: Phase 24 A/Bテスト・分析基盤実装
  - ABTestモデル実装（ABTest, ABTestVariant, ABTestAssignment）
  - ABTestManagerクラス実装（テスト作成・管理・バリアント割り当て）
  - AnalyticsTrackerクラス実装（イベント記録・統計集計）
  - AnalyticsEventモデル実装（UTMパラメータ・収益・デバイス情報対応）
  - ConversionGoalモデル実装（目標設定・進捗追跡）
  - ファネル分析機能（ページビュー→サインアップ→購入の流れ分析）
  - コホートリテンション分析機能
  - 分析APIエンドポイント23件（/api/v1/analytics/*）
  - 分析テスト66件追加
  - テスト598件全パス確認（+66件）
  - 収益化直結機能：A/BテストでUI最適化・ファネル分析でコンバージョン改善
- 2026-01-11: Phase 23 メール通知システム実装
  - EmailServiceクラス実装（SMTP送信・開発モード対応）
  - NotificationManagerクラス実装（通知設定・送信・ログ管理）
  - メールテンプレート実装（ウェルカム/トライアル/決済/紹介報酬/週次サマリー）
  - 日本語/英語対応テンプレート
  - 通知設定API（オプトイン/オプトアウト管理）
  - 開封・クリックトラッキング機能
  - メール通知テスト45件追加
  - テスト532件全パス確認（+45件）
  - 収益化直結機能：トライアル終了間近通知で有料転換促進・紹介報酬通知でユーザー獲得
- 2026-01-11: Phase 22 ユーザー獲得・コンバージョン強化
  - リファラル（紹介）システム実装（src/api/referral/*）
  - 紹介コード生成・検証・適用機能
  - 紹介報酬（クレジット付与）・統計・ランキング
  - オンボーディング進捗管理（src/api/onboarding/*）
  - 無料トライアル機能（7日間Proプラン体験）
  - チェックリスト・ステップガイド機能
  - リファラルテスト30件・オンボーディングテスト37件追加
  - テスト487件全パス確認（+67件）
  - 収益化直結機能：紹介ボーナスでユーザー獲得・トライアルで有料転換促進
- 2026-01-11: Phase 21 ソーシャル共有・バイラル機能
  - ShareManagerクラス実装（static/js/share.js）
  - SNS共有ボタン（Twitter/Facebook/LINE/Pinterest）
  - 共有モーダルUI・CSS（static/css/share.css）
  - ライトボックス共有機能統合
  - デモ結果に共有ボタン追加
  - i18n翻訳追加（日本語/英語）
  - 収益化直結機能：SNS共有でバイラル獲得・ユーザー増加
- 2026-01-10: Phase 20 多言語対応（i18n）
  - i18nモジュール実装（static/js/i18n.js）
  - 日本語/英語翻訳データ100+項目
  - 言語切り替えUI（JA/ENボタン）
  - ブラウザ言語自動検出機能
  - localStorage言語設定永続化
  - hreflang多言語SEO対応
  - 収益化直結機能：英語圏ユーザー獲得で市場拡大
- 2026-01-10: Phase 19 PWA化・UX機能強化
  - 画像ライトボックス実装（拡大表示・ダウンロード・共有・フルスクリーン）
  - 画像ギャラリー機能（生成履歴保存・サムネイル表示・削除機能）
  - サービスワーカー実装（オフライン対応・キャッシュ戦略）
  - PWAマニフェスト作成（ホーム画面追加対応・ショートカット）
  - フロントエンドJS統合（app.js・lightbox.js連携）
  - テスト420件全パス維持
  - 収益化直結機能：UX向上でユーザー継続率・コンバージョン改善
- 2026-01-10: Phase 18 SEO・パフォーマンス・アクセシビリティ最適化
  - Critical CSS（above-the-fold）で初期描画高速化
  - CSS/フォント遅延読み込みでLCP最適化
  - WebSite・BreadcrumbList構造化データ追加（Google検索対応）
  - Core Web Vitals計測コード追加（LCP/CLS）
  - スキップリンク・ARIA属性でアクセシビリティ向上
  - フォーカス表示強化・減少モーション対応
  - テスト420件全パス維持
- 2026-01-10: Phase 17 年額プラン・モバイル対応強化
  - 年額/月額切り替えトグルUI実装（2ヶ月分お得バッジ付き）
  - 年額価格表示（月額換算 + 割引%OFF表示）
  - モバイルレスポンシブ最適化（タブレット/モバイル/小型モバイル対応）
  - ハンバーガーメニュー実装（768px以下でアクティブ）
  - 年額プランテスト10件追加（420 passed, 1 skipped）
  - 収益化直結機能：年額プラン20%割引でキャッシュフロー改善
- 2026-01-10: Phase 16 テストカバレッジ80%達成
  - payment/routes.pyテスト追加（44%→84%）
  - subscription_manager.pyテスト追加（64%→79%）
  - auth/dependencies.pyテスト追加（52%→56%）
  - テスト39件追加（410 passed, 1 skipped）
  - テストカバレッジ80%達成
- 2026-01-10: Phase 15+ 品質強化
  - Stripeクライアントテスト24件追加（371 passed）
  - pyproject.toml v1.0.0へ更新、本番メタデータ完備
  - テストカバレッジ77%達成
- 2026-01-09: Phase 15 ローンチ最終準備
  - Banditセキュリティスキャン実行・MD5警告修正
  - README.md大幅更新（バッジ・機能一覧・デモ情報）
  - Product Huntローンチコピー作成（docs/PRODUCT_HUNT_LAUNCH.md）
  - ロードテストスクリプト作成（scripts/load_test.py）
- 2026-01-09: Phase 14 本番運用監視機能
  - モニタリングモジュール（src/utils/monitoring.py）
  - ヘルスチェッカー（複数コンポーネント並列チェック）
  - メトリクスコレクター（カウンター/ゲージ/ヒストグラム）
  - 構造化ロガー（JSON出力対応）
  - Kubernetes Liveness/Readiness Probe
  - Prometheusメトリクスエクスポート
  - モニタリングテスト28件追加（347 passed, 1 skipped）
- 2026-01-09: Phase 13 ユーザーダッシュボード
  - ユーザーダッシュボードページ（templates/dashboard.html）
  - ダッシュボードCSS（static/css/dashboard.css）
  - ダッシュボードJS（static/js/dashboard.js）
  - ログイン/ログアウト機能（APIキー認証）
  - サブスクリプション管理UI
  - 使用量・レート制限表示UI
  - APIキー管理UI（一覧・作成・無効化）
  - クレジット管理UI（残高・購入・履歴）
  - ダッシュボードテスト18件追加（319 passed, 1 skipped）
- 2026-01-09: Phase 12 管理者ダッシュボード
  - 管理者ダッシュボード機能（src/api/admin/dashboard.py）
  - 管理者APIエンドポイント（src/api/admin/routes.py）
  - 管理者ダッシュボードページ（templates/admin.html）
  - 収益・ユーザー・使用量メトリクス機能
  - チャートデータAPI（30日間の推移）
  - システムヘルス監視機能
  - お問い合わせ統計機能
  - 管理者テスト31件追加（301 passed, 1 skipped）
- 2026-01-09: Phase 11 ドキュメント・法的ページ・お問い合わせ機能
  - ユーザーガイド作成（docs/USER_GUIDE.md）
  - APIクイックスタートガイド作成（docs/API_QUICKSTART.md）
  - 利用規約ページ作成（templates/terms.html）
  - プライバシーポリシーページ作成（templates/privacy.html）
  - お問い合わせページ・API実装（templates/contact.html, src/api/contact_routes.py）
  - お問い合わせテスト17件追加（270 passed, 1 skipped）
- 2026-01-08: Phase 10+ デモモード実装
- 2026-01-08: Phase 10 マーケティング準備・E2Eテスト追加
- 2026-01-08: Phase 9 CI/CD・セキュリティ強化
- 2026-01-08: Phase 8 デプロイ自動化スクリプト作成
- 2026-01-08: Phase 7 デプロイ準備完了
- 2026-01-08: Phase 6 Webインターフェース実装完了
- 2026-01-08: Phase 5 Stripe決済統合完了
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

# アクセス先
# http://localhost:8000 (ランディングページ)
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
# http://localhost:8000/terms (利用規約)
# http://localhost:8000/privacy (プライバシーポリシー)
# http://localhost:8000/contact (お問い合わせ)
# http://localhost:8000/admin (管理者ダッシュボード)
# http://localhost:8000/dashboard (ユーザーダッシュボード)
```

## デプロイ手順
```bash
# 1. Google Cloud セットアップ
python scripts/setup_gcloud.py --project YOUR_PROJECT_ID

# 2. Stripe セットアップ（本番APIキー使用）
python scripts/setup_stripe.py --api-key sk_live_xxx --webhook-url https://your-domain.com

# 3. Cloud Run デプロイ
python scripts/deploy_cloudrun.py --project YOUR_PROJECT_ID
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
