# VisionCraftAI プロジェクトガバナンス

継承: O:\Dev\CLAUDE.md → このファイル

## プロジェクト概要

**VisionCraftAI** - 最先端AI画像生成・編集プラットフォーム

Google Gemini 3モデルを活用した高品質AI画像生成サービス。プロンプトベースの画像生成と基本的な編集機能を提供。

---

## 技術スタック

| カテゴリ | 技術 |
|----------|------|
| 言語 | Python 3.12+ |
| AIモデル | Google Gemini 3 (Vertex AI) |
| クライアント | google-cloud-aiplatform |
| 画像処理 | Pillow, OpenCV |
| API | FastAPI (将来) |
| テスト | pytest |

---

## モデル統合

### Google Vertex AI / Gemini 3
- **認証**: Google Cloud サービスアカウント認証
- **認証情報**: 環境変数 `GOOGLE_APPLICATION_CREDENTIALS` 経由
- **レート制限**: API使用量監視必須
- **コスト管理**: 呼び出し回数ログ記録

### セキュリティ要件
- ❌ APIキー/認証情報のハードコード禁止
- ❌ 認証ファイルのGitコミット禁止
- ✅ 環境変数または暗号化設定ファイル使用
- ✅ `.env`ファイルは`.gitignore`に追加

---

## アーキテクチャ設計

```
VisionCraftAI/
├── src/
│   ├── main.py              # エントリーポイント
│   ├── generator/           # 画像生成モジュール
│   │   ├── gemini_client.py # Gemini API クライアント
│   │   └── prompt_handler.py# プロンプト処理
│   ├── editor/              # 画像編集モジュール
│   │   └── post_processor.py# 後処理
│   └── utils/               # ユーティリティ
│       ├── config.py        # 設定管理
│       └── cache.py         # キャッシュ処理
├── outputs/                 # 生成画像出力先
├── tests/                   # テストスイート
├── docs/                    # ドキュメント
└── .claude/                 # Claude Code設定
```

### コンポーネント
1. **APIサーバー** (将来): FastAPIベースのRESTful API
2. **プロンプトハンドラー**: ユーザー入力の前処理・安全性フィルタリング
3. **画像ポストプロセッサー**: 生成画像の後処理・最適化
4. **キャッシュレイヤー**: 重複リクエストのコスト削減

### 制約事項
- モデル使用コストの監視
- レート制限の遵守
- 不適切コンテンツのフィルタリング必須

---

## 収益化戦略

### ビジネスモデル
| プラン | 内容 | 価格帯 |
|--------|------|--------|
| Free | 月5枚生成、低解像度 | 無料 |
| Basic | 月100枚、標準解像度 | $9.99/月 |
| Pro | 月500枚、高解像度、優先処理 | $29.99/月 |
| Enterprise | 無制限、API アクセス、カスタム | 要相談 |

### 収益源
1. **サブスクリプション**: 月額/年額プラン
2. **従量課金**: クレジット購入システム
3. **Enterprise API**: 第三者アプリ向けAPI提供
4. **プレミアム機能**: 高度な編集ツール、バッチ処理

### 将来実装
- ユーザーアカウント管理
- クレジット追跡システム
- 決済統合 (Stripe)
- 使用量ダッシュボード

---

## 開発計画

### Phase 1: 基盤構築 (現在)
- [x] プロジェクト構造作成
- [ ] Google Cloud 認証設定
- [ ] Gemini 3 API接続確認

### Phase 2: コア機能
- [ ] `generate_image(prompt)` 関数実装
- [ ] CLI インターフェース作成
- [ ] 基本的なエラーハンドリング

### Phase 3: 品質向上
- [ ] プロンプト安全性フィルター
- [ ] 画像後処理機能
- [ ] キャッシュ機構

### Phase 4: ユーザーインターフェース
- [ ] Webインターフェース (React/Next.js)
- [ ] API エンドポイント

### Phase 5: 収益化
- [ ] ユーザー認証システム
- [ ] クレジット/サブスクリプション管理
- [ ] 決済統合

---

## 実装ステップ詳細

### Step 1: API認証設定
```python
# 環境変数設定
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
# GOOGLE_CLOUD_PROJECT=your-project-id

from google.cloud import aiplatform
aiplatform.init(project="project-id", location="us-central1")
```

### Step 2: 画像生成関数
```python
def generate_image(prompt: str, options: dict = None) -> bytes:
    """
    プロンプトから画像を生成

    Args:
        prompt: 画像生成プロンプト
        options: 生成オプション（解像度、スタイル等）

    Returns:
        生成された画像のバイナリデータ
    """
    # 実装予定
    pass
```

### Step 3: CLIインターフェース
```bash
python src/main.py --prompt "A beautiful sunset over mountains" --output outputs/sunset.png
```

### Step 4: テスト戦略
- サンプルプロンプトでの品質評価
- API呼び出しコストのログ記録
- エラーケースのハンドリング確認

---

## ガイドライン

### コード品質
- 型ヒント必須
- docstring必須
- pytest でのテストカバレッジ80%以上

### セキュリティ
- 入力プロンプトのサニタイズ
- 不適切コンテンツのフィルタリング
- APIキーの安全な管理

### 出力管理
- 生成画像は `outputs/` に保存
- ファイル名: `{timestamp}_{hash}.png`
- メタデータ保存 (プロンプト、生成日時等)

---

## 禁止事項

- ❌ APIキーのハードコード
- ❌ 認証ファイルのコミット
- ❌ 未フィルタリングのプロンプト実行
- ❌ コスト監視なしの大量API呼び出し
- ❌ テストなしの本番デプロイ
