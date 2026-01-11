# VisionCraftAI ユーザーガイド

## はじめに

VisionCraftAIは、最先端AI技術を活用した画像生成プラットフォームです。テキストプロンプトを入力するだけで、高品質な画像を数秒で生成できます。

---

## クイックスタート

### 1. APIキーの取得

#### 無料プランで始める
```bash
curl -X POST https://api.visioncraftai.com/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"tier": "free", "name": "My First Key"}'
```

レスポンス例:
```json
{
  "key": "vca_abc123.xyz789",
  "tier": "free",
  "name": "My First Key",
  "created_at": "2026-01-09T00:00:00Z"
}
```

**重要**: APIキーは一度だけ表示されます。安全な場所に保存してください。

### 2. 最初の画像を生成

```bash
curl -X POST https://api.visioncraftai.com/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vca_abc123.xyz789" \
  -d '{
    "prompt": "A beautiful sunset over the ocean",
    "width": 512,
    "height": 512
  }'
```

レスポンス例:
```json
{
  "id": "gen_abc123",
  "status": "completed",
  "image_base64": "iVBORw0KGgo...",
  "format": "png",
  "metadata": {
    "prompt": "A beautiful sunset over the ocean",
    "width": 512,
    "height": 512,
    "processing_time_ms": 2500
  }
}
```

### 3. 画像の保存

Base64エンコードされた画像をファイルに保存:

#### Python
```python
import base64
import json

# APIレスポンスをパース
response = json.loads(api_response)
image_data = base64.b64decode(response["image_base64"])

# ファイルに保存
with open("generated_image.png", "wb") as f:
    f.write(image_data)
```

#### JavaScript (Node.js)
```javascript
const fs = require('fs');

// APIレスポンスをパース
const response = JSON.parse(apiResponse);
const imageBuffer = Buffer.from(response.image_base64, 'base64');

// ファイルに保存
fs.writeFileSync('generated_image.png', imageBuffer);
```

---

## プロンプトのコツ

### 基本構造

効果的なプロンプトは以下の要素を含みます:

1. **被写体**: 何を描くか
2. **スタイル**: どのような表現か
3. **品質指定**: 詳細度・解像度
4. **雰囲気**: 色調・照明

### 例

#### 風景写真風
```
A majestic mountain peak at sunrise,
photorealistic, 4K quality,
warm golden light, dramatic clouds
```

#### アニメ風
```
A cute anime girl with long blue hair,
anime style, Studio Ghibli inspired,
soft lighting, detailed background
```

#### デジタルアート
```
Futuristic cyberpunk cityscape at night,
digital art, neon lights,
highly detailed, cinematic composition
```

### ネガティブプロンプト

避けたい要素を指定することも可能です:

```json
{
  "prompt": "A beautiful flower garden",
  "negative_prompt": "people, animals, buildings",
  "width": 1024,
  "height": 1024
}
```

---

## APIリファレンス

### 認証

すべてのAPIリクエストには`X-API-Key`ヘッダーが必要です:

```
X-API-Key: vca_xxxxxxxx.xxxxxxxx
```

### エンドポイント一覧

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/v1/generate` | POST | 画像生成 |
| `/api/v1/batch/generate` | POST | バッチ画像生成 |
| `/api/v1/prompt/validate` | POST | プロンプト検証 |
| `/api/v1/prompt/enhance` | POST | プロンプト拡張 |
| `/api/v1/auth/quota` | GET | クォータ確認 |
| `/api/v1/auth/usage` | GET | 使用量詳細 |

### 画像生成パラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|------|-----------|------|
| prompt | string | ○ | - | 画像生成プロンプト |
| negative_prompt | string | × | null | ネガティブプロンプト |
| width | int | × | 1024 | 画像幅 (512-4096) |
| height | int | × | 1024 | 画像高さ (512-4096) |
| style | string | × | null | スタイルプリセット |
| num_images | int | × | 1 | 生成枚数 (1-4) |

### スタイルプリセット

| スタイル | 説明 |
|---------|------|
| photorealistic | 写真風 |
| artistic | アーティスティック |
| anime | アニメ調 |
| digital_art | デジタルアート |
| oil_painting | 油絵風 |
| watercolor | 水彩画風 |

---

## プラン別制限

| 機能 | Free | Basic | Pro | Enterprise |
|------|------|-------|-----|------------|
| 月間生成数 | 5枚 | 100枚 | 500枚 | 無制限 |
| 日間生成数 | 3枚 | 20枚 | 50枚 | 無制限 |
| 最大解像度 | 512x512 | 1024x1024 | 2048x2048 | 4096x4096 |
| バッチ処理 | × | 10枚 | 50枚 | 100枚 |
| 優先処理 | × | × | ○ | ○ |
| APIアクセス | × | ○ | ○ | ○ |

---

## エラーハンドリング

### 一般的なエラーコード

| コード | 説明 | 対処法 |
|-------|------|--------|
| 400 | 不正なリクエスト | パラメータを確認 |
| 401 | 認証エラー | APIキーを確認 |
| 403 | アクセス拒否 | プランの制限を確認 |
| 429 | レート制限超過 | しばらく待ってリトライ |
| 500 | サーバーエラー | サポートに連絡 |

### エラーレスポンス例

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "日間生成制限に達しました",
    "detail": {
      "limit": 3,
      "used": 3,
      "reset_at": "2026-01-10T00:00:00Z"
    }
  }
}
```

---

## SDK・ライブラリ

### Python SDK（近日公開）

```python
from visioncraftai import VisionCraftAI

client = VisionCraftAI(api_key="vca_xxx")
image = client.generate("A beautiful sunset")
image.save("sunset.png")
```

### JavaScript SDK（近日公開）

```javascript
import { VisionCraftAI } from 'visioncraftai';

const client = new VisionCraftAI({ apiKey: 'vca_xxx' });
const image = await client.generate('A beautiful sunset');
await image.save('sunset.png');
```

---

## よくある質問

### Q: 生成した画像は商用利用できますか？

有料プラン（Basic以上）で生成した画像は商用利用可能です。ただし、以下の点にご注意ください:
- 第三者の著作権・商標を侵害するプロンプトは禁止
- 違法なコンテンツの生成は禁止
- 生成画像に関する責任はユーザーに帰属

### Q: APIキーを紛失しました

セキュリティ上の理由から、APIキーの再表示はできません。新しいAPIキーを作成し、古いキーを削除してください。

### Q: レート制限を超えました

- 日間制限: 翌日0時（UTC）にリセット
- 月間制限: 翌月1日にリセット
- 急ぎの場合: プランのアップグレードを検討

### Q: 画像が生成されません

以下を確認してください:
1. プロンプトが適切か（禁止語句を含んでいないか）
2. APIキーが有効か
3. クォータ残量があるか

---

## サポート

### ドキュメント
- [API Reference](/docs)
- [ReDoc](/redoc)

### お問い合わせ
- Email: support@visioncraftai.example.com
- [お問い合わせフォーム](/contact)

### コミュニティ
- [GitHub](https://github.com/VisionCraftAI)
- [Twitter](https://twitter.com/VisionCraftAI)

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-01-09 | 初版作成 |
