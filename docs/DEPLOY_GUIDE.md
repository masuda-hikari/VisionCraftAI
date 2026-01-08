# VisionCraftAI デプロイガイド

## 概要
本ドキュメントはVisionCraftAIの本番環境へのデプロイ手順を説明します。

## 前提条件

### 必須
- Docker / Docker Compose
- Google Cloudアカウント（Gemini API用）
- Stripeアカウント（決済用）

### 推奨
- ドメイン（SSL証明書用）
- クラウドプラットフォームアカウント（Cloud Run / Fly.io / Railway等）

---

## 1. Google Cloud設定

### 1.1 プロジェクト作成
```bash
# Google Cloud CLIでプロジェクト作成
gcloud projects create visioncraftai-prod --name="VisionCraftAI"
gcloud config set project visioncraftai-prod
```

### 1.2 Gemini API有効化
```bash
gcloud services enable aiplatform.googleapis.com
```

### 1.3 サービスアカウント作成
```bash
# サービスアカウント作成
gcloud iam service-accounts create visioncraftai-sa \
    --display-name="VisionCraftAI Service Account"

# 権限付与
gcloud projects add-iam-policy-binding visioncraftai-prod \
    --member="serviceAccount:visioncraftai-sa@visioncraftai-prod.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# 認証キー生成
gcloud iam service-accounts keys create ./credentials/service-account.json \
    --iam-account=visioncraftai-sa@visioncraftai-prod.iam.gserviceaccount.com
```

---

## 2. Stripe設定

### 2.1 商品・価格設定
Stripe Dashboardで以下を設定:

| プラン | 月額 | 価格ID（設定後に取得） |
|--------|------|---------------------|
| Basic | $9.99 | price_xxx_basic |
| Pro | $29.99 | price_xxx_pro |
| Enterprise | $99.99 | price_xxx_enterprise |

### 2.2 Webhook設定
1. Stripe Dashboard > Developers > Webhooks
2. エンドポイント追加: `https://your-domain.com/api/v1/payment/webhook`
3. イベント選択:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
4. Webhookシークレットを取得

### 2.3 APIキー取得
- Stripe Dashboard > Developers > API keys
- 本番キー（`sk_live_xxx`）をメモ

---

## 3. ローカルデプロイ（Docker）

### 3.1 環境設定
```bash
# 認証情報ディレクトリ作成
mkdir -p credentials

# サービスアカウントキーを配置
# credentials/service-account.json

# 環境変数設定
cp .env.example .env
# .envを編集して実際の値を設定
```

### 3.2 起動
```bash
# 本番モード
docker compose up -d app

# 開発モード（ホットリロード有効）
docker compose --profile dev up -d app-dev

# ログ確認
docker compose logs -f app
```

### 3.3 動作確認
```bash
# ヘルスチェック
curl http://localhost:8000/api/v1/health

# Webページ
open http://localhost:8000
```

---

## 4. クラウドデプロイ

### 4.1 Google Cloud Run

```bash
# Artifact Registryにプッシュ
gcloud auth configure-docker us-central1-docker.pkg.dev
docker build -t us-central1-docker.pkg.dev/visioncraftai-prod/visioncraftai/app:latest .
docker push us-central1-docker.pkg.dev/visioncraftai-prod/visioncraftai/app:latest

# Cloud Runデプロイ
gcloud run deploy visioncraftai \
    --image us-central1-docker.pkg.dev/visioncraftai-prod/visioncraftai/app:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=visioncraftai-prod" \
    --set-env-vars "STRIPE_API_KEY=sk_live_xxx" \
    --set-env-vars "STRIPE_WEBHOOK_SECRET=whsec_xxx"
```

### 4.2 Fly.io

```bash
# fly.tomlを作成
flyctl launch --no-deploy

# シークレット設定
flyctl secrets set GOOGLE_CLOUD_PROJECT=visioncraftai-prod
flyctl secrets set STRIPE_API_KEY=sk_live_xxx
flyctl secrets set STRIPE_WEBHOOK_SECRET=whsec_xxx

# デプロイ
flyctl deploy
```

### 4.3 Railway

```bash
# GitHubリポジトリと連携後
railway login
railway link
railway up
```

---

## 5. ドメイン・SSL設定

### 5.1 カスタムドメイン
各プラットフォームのドキュメントに従ってカスタムドメインを設定:
- Cloud Run: [カスタムドメインのマッピング](https://cloud.google.com/run/docs/mapping-custom-domains)
- Fly.io: `flyctl certs add your-domain.com`
- Railway: ダッシュボードから設定

### 5.2 SSL証明書
ほとんどのプラットフォームは自動的にSSL証明書を発行します。

---

## 6. 監視・ログ

### 6.1 ヘルスチェック
```bash
# 定期的にヘルスチェックを実行
curl https://your-domain.com/api/v1/health
```

### 6.2 ログ確認
```bash
# Docker
docker compose logs -f

# Cloud Run
gcloud logging read "resource.type=cloud_run_revision"

# Fly.io
flyctl logs
```

---

## 7. トラブルシューティング

### 7.1 認証エラー
```
Google Cloud認証に失敗しました
```
- サービスアカウントキーが正しく配置されているか確認
- `GOOGLE_APPLICATION_CREDENTIALS`環境変数が正しいか確認
- サービスアカウントに適切な権限があるか確認

### 7.2 Stripeエラー
```
Stripe APIキーが無効です
```
- APIキーが正しいか確認（テスト/本番の区別）
- Webhookシークレットが正しいか確認

### 7.3 ポートエラー
```
ポート8000が使用中です
```
- `APP_PORT`環境変数で別のポートを指定
- 競合するプロセスを停止

---

## 8. 本番チェックリスト

### デプロイ前
- [ ] 本番用環境変数を設定
- [ ] `DEBUG=false`を確認
- [ ] `STRIPE_TEST_MODE=false`を確認
- [ ] CORS設定を本番ドメインに制限
- [ ] サービスアカウントキーを安全に管理

### デプロイ後
- [ ] ヘルスチェックが成功
- [ ] ランディングページが表示される
- [ ] API認証が機能する
- [ ] Stripe Webhookが受信できる
- [ ] 画像生成が動作する（認証情報設定後）

---

## 更新履歴
| 日付 | 内容 |
|------|------|
| 2026-01-08 | 初版作成 |
