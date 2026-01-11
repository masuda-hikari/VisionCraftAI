# -*- coding: utf-8 -*-
"""
VisionCraftAI - 通知APIスキーマ

通知関連のPydanticスキーマ定義。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.api.notifications.models import NotificationType, EmailStatus


class NotificationPreferenceResponse(BaseModel):
    """通知設定レスポンス"""
    user_id: str
    email: str

    marketing_emails: bool
    transactional_emails: bool
    usage_alerts: bool
    weekly_summary: bool
    monthly_report: bool
    referral_notifications: bool

    language: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    """通知設定更新リクエスト"""
    marketing_emails: bool | None = None
    transactional_emails: bool | None = None
    usage_alerts: bool | None = None
    weekly_summary: bool | None = None
    monthly_report: bool | None = None
    referral_notifications: bool | None = None
    language: str | None = Field(None, pattern="^(ja|en)$")


class SendNotificationRequest(BaseModel):
    """通知送信リクエスト"""
    user_id: str
    notification_type: NotificationType
    context: dict[str, Any] = Field(default_factory=dict)
    force: bool = False


class SendNotificationResponse(BaseModel):
    """通知送信レスポンス"""
    success: bool
    log_id: str | None = None
    error: str | None = None


class EmailLogResponse(BaseModel):
    """メールログレスポンス"""
    log_id: str
    user_id: str
    email: str
    notification_type: NotificationType
    subject: str
    template_id: str
    status: EmailStatus
    sent_at: datetime | None
    opened_at: datetime | None
    clicked_at: datetime | None
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailLogsResponse(BaseModel):
    """メールログ一覧レスポンス"""
    logs: list[EmailLogResponse]
    total: int


class NotificationStatsResponse(BaseModel):
    """通知統計レスポンス"""
    total: int
    sent: int
    failed: int
    opened: int
    clicked: int
    delivery_rate: float
    open_rate: float
    click_rate: float


class TrackingPixelRequest(BaseModel):
    """トラッキングピクセルリクエスト"""
    log_id: str


class TestEmailRequest(BaseModel):
    """テストメール送信リクエスト"""
    email: EmailStr
    notification_type: NotificationType
    context: dict[str, Any] = Field(default_factory=dict)


class EmailServiceStatusResponse(BaseModel):
    """メールサービス状態レスポンス"""
    configured: bool
    enabled: bool
    smtp_host: str | None = None
    from_email: str | None = None


class UnsubscribeRequest(BaseModel):
    """配信停止リクエスト"""
    user_id: str
    notification_types: list[NotificationType] | None = None
    unsubscribe_all: bool = False
