# -*- coding: utf-8 -*-
"""
VisionCraftAI - メールテンプレート

各種通知用のHTMLテンプレートを定義。
"""

from src.api.notifications.models import NotificationType, EmailTemplate


# 共通HTMLベーステンプレート
_BASE_HTML = """
<!DOCTYPE html>
<html lang="{{language}}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{subject}}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .email-wrapper {
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 700;
        }
        .content {
            padding: 30px;
        }
        .button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 12px 30px;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
        }
        .button:hover {
            opacity: 0.9;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        .highlight-box {
            background-color: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 0 4px 4px 0;
        }
        .stats-grid {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }
        .stat-item {
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="email-wrapper">
            {{content}}
            <div class="footer">
                <p>© 2026 VisionCraftAI. All rights reserved.</p>
                <p>
                    <a href="{{base_url}}/dashboard">ダッシュボード</a> |
                    <a href="{{base_url}}/privacy">プライバシーポリシー</a> |
                    <a href="{{base_url}}/terms">利用規約</a>
                </p>
                <p>
                    <a href="{{unsubscribe_url}}">メール配信設定を変更</a>
                </p>
            </div>
        </div>
    </div>
</body>
</html>
"""


def get_default_templates() -> dict[str, dict[str, EmailTemplate]]:
    """デフォルトテンプレートを取得"""
    templates: dict[str, dict[str, EmailTemplate]] = {}

    # ウェルカムメール
    templates[NotificationType.WELCOME.value] = {
        "ja": EmailTemplate(
            template_id="welcome_ja",
            notification_type=NotificationType.WELCOME,
            language="ja",
            subject="VisionCraftAIへようこそ！",
            html_body=_BASE_HTML.replace("{{content}}", """
            <div class="header">
                <h1>🎨 VisionCraftAI</h1>
            </div>
            <div class="content">
                <h2>{{user_name}}さん、ご登録ありがとうございます！</h2>
                <p>VisionCraftAIへようこそ。AIによる画像生成の世界を体験する準備が整いました。</p>

                <div class="highlight-box">
                    <strong>今すぐ始める:</strong>
                    <ol>
                        <li>ダッシュボードにアクセス</li>
                        <li>プロンプトを入力</li>
                        <li>高品質な画像を生成</li>
                    </ol>
                </div>

                <p style="text-align: center;">
                    <a href="{{base_url}}/dashboard" class="button">ダッシュボードを開く</a>
                </p>

                <p>ご不明な点がございましたら、お気軽にお問い合わせください。</p>
            </div>
            """),
            text_body="""
VisionCraftAIへようこそ！

{{user_name}}さん、ご登録ありがとうございます！

VisionCraftAIへようこそ。AIによる画像生成の世界を体験する準備が整いました。

今すぐ始める:
1. ダッシュボードにアクセス
2. プロンプトを入力
3. 高品質な画像を生成

ダッシュボード: {{base_url}}/dashboard

ご不明な点がございましたら、お気軽にお問い合わせください。
            """,
        ),
        "en": EmailTemplate(
            template_id="welcome_en",
            notification_type=NotificationType.WELCOME,
            language="en",
            subject="Welcome to VisionCraftAI!",
            html_body=_BASE_HTML.replace("{{content}}", """
            <div class="header">
                <h1>🎨 VisionCraftAI</h1>
            </div>
            <div class="content">
                <h2>Welcome, {{user_name}}!</h2>
                <p>Thank you for joining VisionCraftAI. You're ready to explore the world of AI image generation.</p>

                <div class="highlight-box">
                    <strong>Get Started:</strong>
                    <ol>
                        <li>Access your dashboard</li>
                        <li>Enter a prompt</li>
                        <li>Generate high-quality images</li>
                    </ol>
                </div>

                <p style="text-align: center;">
                    <a href="{{base_url}}/dashboard" class="button">Open Dashboard</a>
                </p>

                <p>If you have any questions, feel free to contact us.</p>
            </div>
            """),
            text_body="""
Welcome to VisionCraftAI!

Welcome, {{user_name}}!

Thank you for joining VisionCraftAI. You're ready to explore the world of AI image generation.

Get Started:
1. Access your dashboard
2. Enter a prompt
3. Generate high-quality images

Dashboard: {{base_url}}/dashboard

If you have any questions, feel free to contact us.
            """,
        ),
    }

    # トライアル開始
    templates[NotificationType.TRIAL_STARTED.value] = {
        "ja": EmailTemplate(
            template_id="trial_started_ja",
            notification_type=NotificationType.TRIAL_STARTED,
            language="ja",
            subject="7日間無料トライアルが開始されました！",
            html_body=_BASE_HTML.replace("{{content}}", """
            <div class="header">
                <h1>🎉 トライアル開始</h1>
            </div>
            <div class="content">
                <h2>{{user_name}}さん、無料トライアルへようこそ！</h2>
                <p>7日間のProプラン無料トライアルが開始されました。</p>

                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{{trial_credits}}</div>
                        <div class="stat-label">クレジット</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{trial_days}}日</div>
                        <div class="stat-label">トライアル期間</div>
                    </div>
                </div>

                <div class="highlight-box">
                    <strong>トライアル特典:</strong>
                    <ul>
                        <li>Proプランの全機能を利用可能</li>
                        <li>高解像度画像生成（2048x2048まで）</li>
                        <li>優先処理</li>
                    </ul>
                </div>

                <p style="text-align: center;">
                    <a href="{{base_url}}/dashboard" class="button">今すぐ試す</a>
                </p>

                <p><strong>トライアル終了日:</strong> {{trial_end_date}}</p>
            </div>
            """),
            text_body="""
トライアル開始

{{user_name}}さん、無料トライアルへようこそ！

7日間のProプラン無料トライアルが開始されました。

- クレジット: {{trial_credits}}
- トライアル期間: {{trial_days}}日

トライアル特典:
- Proプランの全機能を利用可能
- 高解像度画像生成（2048x2048まで）
- 優先処理

ダッシュボード: {{base_url}}/dashboard

トライアル終了日: {{trial_end_date}}
            """,
        ),
    }

    # トライアル終了間近
    templates[NotificationType.TRIAL_ENDING.value] = {
        "ja": EmailTemplate(
            template_id="trial_ending_ja",
            notification_type=NotificationType.TRIAL_ENDING,
            language="ja",
            subject="トライアル終了まであと{{days_remaining}}日です",
            html_body=_BASE_HTML.replace("{{content}}", """
            <div class="header">
                <h1>⏰ トライアル終了間近</h1>
            </div>
            <div class="content">
                <h2>{{user_name}}さん</h2>
                <p>無料トライアルの終了まであと<strong>{{days_remaining}}日</strong>です。</p>

                <div class="highlight-box">
                    <strong>これまでの利用状況:</strong>
                    <ul>
                        <li>生成した画像: {{images_generated}}枚</li>
                        <li>使用クレジット: {{credits_used}}</li>
                    </ul>
                </div>

                <p>トライアル終了後もVisionCraftAIをお楽しみいただくには、プランへのアップグレードをご検討ください。</p>

                <p style="text-align: center;">
                    <a href="{{base_url}}/dashboard#pricing" class="button">プランを選ぶ</a>
                </p>
            </div>
            """),
            text_body="""
トライアル終了間近

{{user_name}}さん

無料トライアルの終了まであと{{days_remaining}}日です。

これまでの利用状況:
- 生成した画像: {{images_generated}}枚
- 使用クレジット: {{credits_used}}

プランを選ぶ: {{base_url}}/dashboard#pricing
            """,
        ),
    }

    # 支払い成功
    templates[NotificationType.PAYMENT_SUCCEEDED.value] = {
        "ja": EmailTemplate(
            template_id="payment_succeeded_ja",
            notification_type=NotificationType.PAYMENT_SUCCEEDED,
            language="ja",
            subject="お支払いを受け付けました",
            html_body=_BASE_HTML.replace("{{content}}", """
            <div class="header">
                <h1>✅ お支払い完了</h1>
            </div>
            <div class="content">
                <h2>{{user_name}}さん</h2>
                <p>お支払いが正常に処理されました。</p>

                <div class="highlight-box">
                    <strong>お支払い詳細:</strong>
                    <ul>
                        <li>金額: {{amount}}</li>
                        <li>プラン: {{plan_name}}</li>
                        <li>次回請求日: {{next_billing_date}}</li>
                    </ul>
                </div>

                <p>ご利用いただきありがとうございます。</p>

                <p style="text-align: center;">
                    <a href="{{base_url}}/dashboard" class="button">ダッシュボードを開く</a>
                </p>
            </div>
            """),
            text_body="""
お支払い完了

{{user_name}}さん

お支払いが正常に処理されました。

お支払い詳細:
- 金額: {{amount}}
- プラン: {{plan_name}}
- 次回請求日: {{next_billing_date}}

ご利用いただきありがとうございます。
            """,
        ),
    }

    # 支払い失敗
    templates[NotificationType.PAYMENT_FAILED.value] = {
        "ja": EmailTemplate(
            template_id="payment_failed_ja",
            notification_type=NotificationType.PAYMENT_FAILED,
            language="ja",
            subject="お支払いに問題が発生しました",
            html_body=_BASE_HTML.replace("{{content}}", """
            <div class="header" style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);">
                <h1>⚠️ お支払いエラー</h1>
            </div>
            <div class="content">
                <h2>{{user_name}}さん</h2>
                <p>お支払いの処理中に問題が発生しました。</p>

                <div class="highlight-box" style="border-left-color: #e74c3c;">
                    <strong>エラー内容:</strong>
                    <p>{{error_message}}</p>
                </div>

                <p>お支払い方法をご確認の上、再度お試しください。</p>

                <p style="text-align: center;">
                    <a href="{{base_url}}/dashboard#billing" class="button" style="background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);">
                        支払い方法を更新
                    </a>
                </p>

                <p>ご不明な点がございましたら、サポートまでお問い合わせください。</p>
            </div>
            """),
            text_body="""
お支払いエラー

{{user_name}}さん

お支払いの処理中に問題が発生しました。

エラー内容: {{error_message}}

お支払い方法をご確認の上、再度お試しください。

支払い方法を更新: {{base_url}}/dashboard#billing
            """,
        ),
    }

    # 紹介報酬獲得
    templates[NotificationType.REFERRAL_REWARD.value] = {
        "ja": EmailTemplate(
            template_id="referral_reward_ja",
            notification_type=NotificationType.REFERRAL_REWARD,
            language="ja",
            subject="🎁 紹介報酬を獲得しました！",
            html_body=_BASE_HTML.replace("{{content}}", """
            <div class="header">
                <h1>🎁 紹介報酬獲得</h1>
            </div>
            <div class="content">
                <h2>おめでとうございます、{{user_name}}さん！</h2>
                <p>あなたの紹介で<strong>{{referred_user}}</strong>さんが登録しました。</p>

                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">+{{reward_credits}}</div>
                        <div class="stat-label">獲得クレジット</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{total_referrals}}</div>
                        <div class="stat-label">紹介人数</div>
                    </div>
                </div>

                <p>友達を紹介すると、双方に<strong>5クレジット</strong>がプレゼントされます。</p>

                <p style="text-align: center;">
                    <a href="{{base_url}}/dashboard#referral" class="button">紹介リンクを共有</a>
                </p>
            </div>
            """),
            text_body="""
紹介報酬獲得

おめでとうございます、{{user_name}}さん！

あなたの紹介で{{referred_user}}さんが登録しました。

獲得クレジット: +{{reward_credits}}
紹介人数: {{total_referrals}}

紹介リンクを共有: {{base_url}}/dashboard#referral
            """,
        ),
    }

    # 週次サマリー
    templates[NotificationType.WEEKLY_SUMMARY.value] = {
        "ja": EmailTemplate(
            template_id="weekly_summary_ja",
            notification_type=NotificationType.WEEKLY_SUMMARY,
            language="ja",
            subject="今週のVisionCraftAI利用状況",
            html_body=_BASE_HTML.replace("{{content}}", """
            <div class="header">
                <h1>📊 週次レポート</h1>
            </div>
            <div class="content">
                <h2>{{user_name}}さん、今週の利用状況です</h2>

                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">{{images_generated}}</div>
                        <div class="stat-label">生成画像数</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{credits_used}}</div>
                        <div class="stat-label">使用クレジット</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{{credits_remaining}}</div>
                        <div class="stat-label">残りクレジット</div>
                    </div>
                </div>

                <div class="highlight-box">
                    <strong>今週のハイライト:</strong>
                    <p>{{weekly_highlight}}</p>
                </div>

                <p style="text-align: center;">
                    <a href="{{base_url}}/dashboard" class="button">ダッシュボードを開く</a>
                </p>
            </div>
            """),
            text_body="""
週次レポート

{{user_name}}さん、今週の利用状況です

- 生成画像数: {{images_generated}}
- 使用クレジット: {{credits_used}}
- 残りクレジット: {{credits_remaining}}

今週のハイライト: {{weekly_highlight}}

ダッシュボード: {{base_url}}/dashboard
            """,
        ),
    }

    # クレジット残高低下
    templates[NotificationType.CREDITS_LOW.value] = {
        "ja": EmailTemplate(
            template_id="credits_low_ja",
            notification_type=NotificationType.CREDITS_LOW,
            language="ja",
            subject="⚠️ クレジット残高が少なくなっています",
            html_body=_BASE_HTML.replace("{{content}}", """
            <div class="header" style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);">
                <h1>⚠️ クレジット残高</h1>
            </div>
            <div class="content">
                <h2>{{user_name}}さん</h2>
                <p>クレジット残高が<strong>{{credits_remaining}}</strong>になりました。</p>

                <div class="highlight-box" style="border-left-color: #f39c12;">
                    <p>画像生成を続けるには、クレジットを追加購入してください。</p>
                </div>

                <p style="text-align: center;">
                    <a href="{{base_url}}/dashboard#credits" class="button" style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);">
                        クレジットを購入
                    </a>
                </p>
            </div>
            """),
            text_body="""
クレジット残高

{{user_name}}さん

クレジット残高が{{credits_remaining}}になりました。

画像生成を続けるには、クレジットを追加購入してください。

クレジットを購入: {{base_url}}/dashboard#credits
            """,
        ),
    }

    return templates


# デフォルトテンプレートのキャッシュ
_TEMPLATES_CACHE: dict[str, dict[str, EmailTemplate]] | None = None


def get_template(
    notification_type: NotificationType,
    language: str = "ja",
) -> EmailTemplate | None:
    """
    テンプレートを取得

    Args:
        notification_type: 通知タイプ
        language: 言語コード

    Returns:
        EmailTemplate | None: テンプレート
    """
    global _TEMPLATES_CACHE

    if _TEMPLATES_CACHE is None:
        _TEMPLATES_CACHE = get_default_templates()

    type_templates = _TEMPLATES_CACHE.get(notification_type.value)
    if not type_templates:
        return None

    # 指定言語のテンプレートを探す、なければ日本語にフォールバック
    return type_templates.get(language) or type_templates.get("ja")
