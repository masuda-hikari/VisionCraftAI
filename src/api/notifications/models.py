# -*- coding: utf-8 -*-
"""
VisionCraftAI - メール通知モデル

通知設定、メールテンプレート、送信ログのデータモデル。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class NotificationType(str, Enum):
    """通知タイプ"""
    WELCOME = "welcome"                    # ウェルカムメール
    TRIAL_STARTED = "trial_started"        # トライアル開始
    TRIAL_ENDING = "trial_ending"          # トライアル終了間近
    TRIAL_ENDED = "trial_ended"            # トライアル終了
    SUBSCRIPTION_CREATED = "subscription_created"    # サブスクリプション開始
    SUBSCRIPTION_RENEWED = "subscription_renewed"    # サブスクリプション更新
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"  # サブスクリプションキャンセル
    PAYMENT_SUCCEEDED = "payment_succeeded"  # 支払い成功
    PAYMENT_FAILED = "payment_failed"        # 支払い失敗
    CREDITS_PURCHASED = "credits_purchased"  # クレジット購入
    CREDITS_LOW = "credits_low"              # クレジット残高低下
    REFERRAL_SIGNED_UP = "referral_signed_up"  # 紹介した人が登録
    REFERRAL_REWARD = "referral_reward"        # 紹介報酬獲得
    USAGE_WARNING = "usage_warning"          # 使用量警告
    USAGE_LIMIT_REACHED = "usage_limit_reached"  # 使用量上限到達
    WEEKLY_SUMMARY = "weekly_summary"        # 週次サマリー
    MONTHLY_REPORT = "monthly_report"        # 月次レポート


class EmailStatus(str, Enum):
    """メール送信状態"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"


@dataclass
class NotificationPreference:
    """ユーザー通知設定"""
    user_id: str
    email: str

    # 通知カテゴリ別設定
    marketing_emails: bool = True           # マーケティングメール
    transactional_emails: bool = True       # トランザクションメール（必須）
    usage_alerts: bool = True               # 使用量アラート
    weekly_summary: bool = True             # 週次サマリー
    monthly_report: bool = False            # 月次レポート
    referral_notifications: bool = True     # 紹介関連通知

    # 言語設定
    language: str = "ja"

    # 最終更新
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def can_receive(self, notification_type: NotificationType) -> bool:
        """指定された通知タイプを受け取れるかチェック"""
        # トランザクションメールは常に送信
        transactional_types = {
            NotificationType.WELCOME,
            NotificationType.SUBSCRIPTION_CREATED,
            NotificationType.SUBSCRIPTION_RENEWED,
            NotificationType.SUBSCRIPTION_CANCELLED,
            NotificationType.PAYMENT_SUCCEEDED,
            NotificationType.PAYMENT_FAILED,
            NotificationType.CREDITS_PURCHASED,
            NotificationType.TRIAL_STARTED,
            NotificationType.TRIAL_ENDED,
        }

        if notification_type in transactional_types:
            return self.transactional_emails

        # 使用量アラート
        usage_types = {
            NotificationType.USAGE_WARNING,
            NotificationType.USAGE_LIMIT_REACHED,
            NotificationType.CREDITS_LOW,
        }
        if notification_type in usage_types:
            return self.usage_alerts

        # 紹介関連
        referral_types = {
            NotificationType.REFERRAL_SIGNED_UP,
            NotificationType.REFERRAL_REWARD,
        }
        if notification_type in referral_types:
            return self.referral_notifications

        # レポート系
        if notification_type == NotificationType.WEEKLY_SUMMARY:
            return self.weekly_summary
        if notification_type == NotificationType.MONTHLY_REPORT:
            return self.monthly_report

        # トライアル警告
        if notification_type == NotificationType.TRIAL_ENDING:
            return self.usage_alerts

        return self.marketing_emails


@dataclass
class EmailTemplate:
    """メールテンプレート"""
    template_id: str
    notification_type: NotificationType
    language: str = "ja"

    # テンプレート内容
    subject: str = ""
    html_body: str = ""
    text_body: str = ""

    # メタデータ
    version: int = 1
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def render(self, context: dict[str, Any]) -> tuple[str, str, str]:
        """
        テンプレートをレンダリング

        Args:
            context: テンプレート変数

        Returns:
            tuple[str, str, str]: (subject, html_body, text_body)
        """
        rendered_subject = self.subject
        rendered_html = self.html_body
        rendered_text = self.text_body

        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered_subject = rendered_subject.replace(placeholder, str(value))
            rendered_html = rendered_html.replace(placeholder, str(value))
            rendered_text = rendered_text.replace(placeholder, str(value))

        return rendered_subject, rendered_html, rendered_text


@dataclass
class EmailLog:
    """メール送信ログ"""
    log_id: str
    user_id: str
    email: str
    notification_type: NotificationType

    # 送信内容
    subject: str
    template_id: str

    # 状態
    status: EmailStatus = EmailStatus.PENDING

    # 追跡情報
    sent_at: datetime | None = None
    opened_at: datetime | None = None
    clicked_at: datetime | None = None

    # エラー情報
    error_message: str | None = None
    retry_count: int = 0

    # メタデータ
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def mark_sent(self) -> None:
        """送信済みにマーク"""
        self.status = EmailStatus.SENT
        self.sent_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """失敗にマーク"""
        self.status = EmailStatus.FAILED
        self.error_message = error
        self.retry_count += 1

    def mark_opened(self) -> None:
        """開封にマーク"""
        self.status = EmailStatus.OPENED
        self.opened_at = datetime.utcnow()

    def mark_clicked(self) -> None:
        """クリックにマーク"""
        self.status = EmailStatus.CLICKED
        self.clicked_at = datetime.utcnow()
