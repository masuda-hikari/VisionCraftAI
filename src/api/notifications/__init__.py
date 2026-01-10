# -*- coding: utf-8 -*-
"""
VisionCraftAI - メール通知モジュール

ユーザー通知・メール送信機能を提供します。
"""

from src.api.notifications.models import (
    NotificationPreference,
    NotificationType,
    EmailTemplate,
    EmailLog,
)
from src.api.notifications.email_service import EmailService
from src.api.notifications.manager import NotificationManager

__all__ = [
    "NotificationPreference",
    "NotificationType",
    "EmailTemplate",
    "EmailLog",
    "EmailService",
    "NotificationManager",
]
