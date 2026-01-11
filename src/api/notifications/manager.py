# -*- coding: utf-8 -*-
"""
VisionCraftAI - 通知マネージャー

ユーザー通知の管理・送信を行うマネージャークラス。
"""

import logging
import uuid
from datetime import datetime, UTC
from typing import Any


def _utcnow() -> datetime:
    """現在のUTC時刻を返す（タイムゾーン対応）"""
    return datetime.now(UTC)

from src.api.notifications.models import (
    NotificationPreference,
    NotificationType,
    EmailLog,
    EmailStatus,
)
from src.api.notifications.email_service import EmailService
from src.api.notifications.templates import get_template

logger = logging.getLogger(__name__)


class NotificationManager:
    """通知マネージャー"""

    def __init__(self, email_service: EmailService | None = None):
        """
        初期化

        Args:
            email_service: メール送信サービス
        """
        self.email_service = email_service or EmailService()

        # ユーザー通知設定ストレージ（本番ではDB使用）
        self._preferences: dict[str, NotificationPreference] = {}

        # 送信ログストレージ（本番ではDB使用）
        self._logs: dict[str, EmailLog] = {}

        # デフォルトのベースURL
        self._base_url = "https://visioncraft.ai"

    def set_base_url(self, url: str) -> None:
        """ベースURLを設定"""
        self._base_url = url.rstrip("/")

    def get_preference(self, user_id: str) -> NotificationPreference | None:
        """ユーザーの通知設定を取得"""
        return self._preferences.get(user_id)

    def set_preference(self, preference: NotificationPreference) -> None:
        """ユーザーの通知設定を保存"""
        preference.updated_at = _utcnow()
        self._preferences[preference.user_id] = preference

    def create_default_preference(
        self,
        user_id: str,
        email: str,
        language: str = "ja",
    ) -> NotificationPreference:
        """デフォルトの通知設定を作成"""
        preference = NotificationPreference(
            user_id=user_id,
            email=email,
            language=language,
        )
        self.set_preference(preference)
        return preference

    def update_preference(
        self,
        user_id: str,
        **kwargs: Any,
    ) -> NotificationPreference | None:
        """
        通知設定を更新

        Args:
            user_id: ユーザーID
            **kwargs: 更新するフィールド

        Returns:
            NotificationPreference | None: 更新後の設定
        """
        preference = self.get_preference(user_id)
        if not preference:
            return None

        for key, value in kwargs.items():
            if hasattr(preference, key):
                setattr(preference, key, value)

        preference.updated_at = _utcnow()
        self._preferences[user_id] = preference
        return preference

    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        context: dict[str, Any],
        force: bool = False,
    ) -> tuple[bool, str | None, str | None]:
        """
        通知を送信

        Args:
            user_id: ユーザーID
            notification_type: 通知タイプ
            context: テンプレート変数
            force: 設定を無視して強制送信

        Returns:
            tuple[bool, str | None, str | None]: (成功, ログID, エラーメッセージ)
        """
        # 通知設定を取得
        preference = self.get_preference(user_id)
        if not preference:
            return False, None, "Notification preference not found"

        # 通知を受け取れるかチェック
        if not force and not preference.can_receive(notification_type):
            logger.info(
                f"User {user_id} has opted out of {notification_type.value}"
            )
            return False, None, "User opted out of this notification type"

        # テンプレートを取得
        template = get_template(notification_type, preference.language)
        if not template:
            return False, None, f"Template not found for {notification_type.value}"

        # コンテキストにデフォルト値を追加
        context = {
            **context,
            "base_url": self._base_url,
            "unsubscribe_url": f"{self._base_url}/dashboard#notifications",
            "language": preference.language,
            "user_id": user_id,
        }

        # テンプレートをレンダリング
        subject, html_body, text_body = template.render(context)

        # ログを作成
        log = EmailLog(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            email=preference.email,
            notification_type=notification_type,
            subject=subject,
            template_id=template.template_id,
        )

        # メール送信
        success, error = await self.email_service.send(
            to_email=preference.email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
        )

        if success:
            log.mark_sent()
        else:
            log.mark_failed(error or "Unknown error")

        # ログを保存
        self._logs[log.log_id] = log

        return success, log.log_id, error

    async def send_welcome(
        self,
        user_id: str,
        user_name: str,
    ) -> tuple[bool, str | None, str | None]:
        """ウェルカムメールを送信"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.WELCOME,
            context={"user_name": user_name},
        )

    async def send_trial_started(
        self,
        user_id: str,
        user_name: str,
        trial_credits: int,
        trial_days: int,
        trial_end_date: str,
    ) -> tuple[bool, str | None, str | None]:
        """トライアル開始メールを送信"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TRIAL_STARTED,
            context={
                "user_name": user_name,
                "trial_credits": trial_credits,
                "trial_days": trial_days,
                "trial_end_date": trial_end_date,
            },
        )

    async def send_trial_ending(
        self,
        user_id: str,
        user_name: str,
        days_remaining: int,
        images_generated: int,
        credits_used: int,
    ) -> tuple[bool, str | None, str | None]:
        """トライアル終了間近メールを送信"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TRIAL_ENDING,
            context={
                "user_name": user_name,
                "days_remaining": days_remaining,
                "images_generated": images_generated,
                "credits_used": credits_used,
            },
        )

    async def send_payment_succeeded(
        self,
        user_id: str,
        user_name: str,
        amount: str,
        plan_name: str,
        next_billing_date: str,
    ) -> tuple[bool, str | None, str | None]:
        """支払い成功メールを送信"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.PAYMENT_SUCCEEDED,
            context={
                "user_name": user_name,
                "amount": amount,
                "plan_name": plan_name,
                "next_billing_date": next_billing_date,
            },
        )

    async def send_payment_failed(
        self,
        user_id: str,
        user_name: str,
        error_message: str,
    ) -> tuple[bool, str | None, str | None]:
        """支払い失敗メールを送信"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.PAYMENT_FAILED,
            context={
                "user_name": user_name,
                "error_message": error_message,
            },
        )

    async def send_referral_reward(
        self,
        user_id: str,
        user_name: str,
        referred_user: str,
        reward_credits: int,
        total_referrals: int,
    ) -> tuple[bool, str | None, str | None]:
        """紹介報酬メールを送信"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.REFERRAL_REWARD,
            context={
                "user_name": user_name,
                "referred_user": referred_user,
                "reward_credits": reward_credits,
                "total_referrals": total_referrals,
            },
        )

    async def send_credits_low(
        self,
        user_id: str,
        user_name: str,
        credits_remaining: int,
    ) -> tuple[bool, str | None, str | None]:
        """クレジット残高低下メールを送信"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.CREDITS_LOW,
            context={
                "user_name": user_name,
                "credits_remaining": credits_remaining,
            },
        )

    async def send_weekly_summary(
        self,
        user_id: str,
        user_name: str,
        images_generated: int,
        credits_used: int,
        credits_remaining: int,
        weekly_highlight: str,
    ) -> tuple[bool, str | None, str | None]:
        """週次サマリーメールを送信"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.WEEKLY_SUMMARY,
            context={
                "user_name": user_name,
                "images_generated": images_generated,
                "credits_used": credits_used,
                "credits_remaining": credits_remaining,
                "weekly_highlight": weekly_highlight,
            },
        )

    def get_log(self, log_id: str) -> EmailLog | None:
        """送信ログを取得"""
        return self._logs.get(log_id)

    def get_user_logs(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[EmailLog]:
        """ユーザーの送信ログを取得"""
        user_logs = [
            log for log in self._logs.values()
            if log.user_id == user_id
        ]
        user_logs.sort(key=lambda x: x.created_at, reverse=True)
        return user_logs[:limit]

    def get_stats(self, user_id: str | None = None) -> dict[str, Any]:
        """送信統計を取得"""
        logs = list(self._logs.values())
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]

        total = len(logs)
        sent = len([l for l in logs if l.status == EmailStatus.SENT])
        failed = len([l for l in logs if l.status == EmailStatus.FAILED])
        opened = len([l for l in logs if l.status == EmailStatus.OPENED])
        clicked = len([l for l in logs if l.status == EmailStatus.CLICKED])

        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "opened": opened,
            "clicked": clicked,
            "delivery_rate": (sent / total * 100) if total > 0 else 0,
            "open_rate": (opened / sent * 100) if sent > 0 else 0,
            "click_rate": (clicked / opened * 100) if opened > 0 else 0,
        }

    def mark_opened(self, log_id: str) -> bool:
        """メール開封をマーク"""
        log = self.get_log(log_id)
        if log:
            log.mark_opened()
            return True
        return False

    def mark_clicked(self, log_id: str) -> bool:
        """リンククリックをマーク"""
        log = self.get_log(log_id)
        if log:
            log.mark_clicked()
            return True
        return False


# シングルトンインスタンス
_notification_manager: NotificationManager | None = None


def get_notification_manager() -> NotificationManager:
    """NotificationManagerのシングルトンインスタンスを取得"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
