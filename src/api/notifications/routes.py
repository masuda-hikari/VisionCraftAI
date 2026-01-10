# -*- coding: utf-8 -*-
"""
VisionCraftAI - 通知APIルート

通知設定・送信・ログ関連のAPIエンドポイント。
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from src.api.auth.dependencies import get_api_key, TierChecker
from src.api.auth.models import APIKey, APIKeyTier
from src.api.notifications.manager import get_notification_manager, NotificationManager
from src.api.notifications.models import NotificationType, NotificationPreference
from src.api.notifications.schemas import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    SendNotificationRequest,
    SendNotificationResponse,
    EmailLogResponse,
    EmailLogsResponse,
    NotificationStatsResponse,
    TestEmailRequest,
    EmailServiceStatusResponse,
    UnsubscribeRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_manager() -> NotificationManager:
    """NotificationManagerの依存性注入"""
    return get_notification_manager()


# 通知設定エンドポイント
@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="通知設定を取得",
    description="現在のユーザーの通知設定を取得します。",
)
async def get_preferences(
    api_key: APIKey = Depends(get_api_key),
    manager: NotificationManager = Depends(get_manager),
) -> NotificationPreferenceResponse:
    """通知設定を取得"""
    preference = manager.get_preference(api_key.owner_id)

    if not preference:
        # デフォルト設定を作成
        email = f"{api_key.owner_id}@example.com"  # 本番ではユーザー情報から取得
        preference = manager.create_default_preference(
            user_id=api_key.owner_id,
            email=email,
        )

    return NotificationPreferenceResponse(
        user_id=preference.user_id,
        email=preference.email,
        marketing_emails=preference.marketing_emails,
        transactional_emails=preference.transactional_emails,
        usage_alerts=preference.usage_alerts,
        weekly_summary=preference.weekly_summary,
        monthly_report=preference.monthly_report,
        referral_notifications=preference.referral_notifications,
        language=preference.language,
        updated_at=preference.updated_at,
    )


@router.patch(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="通知設定を更新",
    description="通知設定を更新します。",
)
async def update_preferences(
    update: NotificationPreferenceUpdate,
    api_key: APIKey = Depends(get_api_key),
    manager: NotificationManager = Depends(get_manager),
) -> NotificationPreferenceResponse:
    """通知設定を更新"""
    # 設定が存在しない場合は作成
    preference = manager.get_preference(api_key.owner_id)
    if not preference:
        email = f"{api_key.owner_id}@example.com"
        preference = manager.create_default_preference(
            user_id=api_key.owner_id,
            email=email,
        )

    # 更新
    update_data = update.model_dump(exclude_unset=True)
    if update_data:
        preference = manager.update_preference(api_key.owner_id, **update_data)
        if not preference:
            raise HTTPException(status_code=404, detail="Preference not found")

    return NotificationPreferenceResponse(
        user_id=preference.user_id,
        email=preference.email,
        marketing_emails=preference.marketing_emails,
        transactional_emails=preference.transactional_emails,
        usage_alerts=preference.usage_alerts,
        weekly_summary=preference.weekly_summary,
        monthly_report=preference.monthly_report,
        referral_notifications=preference.referral_notifications,
        language=preference.language,
        updated_at=preference.updated_at,
    )


# 通知送信エンドポイント（管理者用）
@router.post(
    "/send",
    response_model=SendNotificationResponse,
    summary="通知を送信（管理者）",
    description="指定ユーザーに通知を送信します。管理者権限が必要です。",
)
async def send_notification(
    request: SendNotificationRequest,
    api_key: APIKey = Depends(TierChecker(APIKeyTier.ENTERPRISE)),
    manager: NotificationManager = Depends(get_manager),
) -> SendNotificationResponse:
    """通知を送信"""
    success, log_id, error = await manager.send_notification(
        user_id=request.user_id,
        notification_type=request.notification_type,
        context=request.context,
        force=request.force,
    )

    return SendNotificationResponse(
        success=success,
        log_id=log_id,
        error=error,
    )


# メールログエンドポイント
@router.get(
    "/logs",
    response_model=EmailLogsResponse,
    summary="送信ログを取得",
    description="自分のメール送信ログを取得します。",
)
async def get_logs(
    limit: int = Query(default=50, ge=1, le=100),
    api_key: APIKey = Depends(get_api_key),
    manager: NotificationManager = Depends(get_manager),
) -> EmailLogsResponse:
    """送信ログを取得"""
    logs = manager.get_user_logs(api_key.owner_id, limit=limit)

    return EmailLogsResponse(
        logs=[
            EmailLogResponse(
                log_id=log.log_id,
                user_id=log.user_id,
                email=log.email,
                notification_type=log.notification_type,
                subject=log.subject,
                template_id=log.template_id,
                status=log.status,
                sent_at=log.sent_at,
                opened_at=log.opened_at,
                clicked_at=log.clicked_at,
                error_message=log.error_message,
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=len(logs),
    )


@router.get(
    "/logs/{log_id}",
    response_model=EmailLogResponse,
    summary="送信ログ詳細を取得",
    description="特定のメール送信ログを取得します。",
)
async def get_log_detail(
    log_id: str,
    api_key: APIKey = Depends(get_api_key),
    manager: NotificationManager = Depends(get_manager),
) -> EmailLogResponse:
    """送信ログ詳細を取得"""
    log = manager.get_log(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    # 自分のログのみ閲覧可能
    if log.user_id != api_key.owner_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return EmailLogResponse(
        log_id=log.log_id,
        user_id=log.user_id,
        email=log.email,
        notification_type=log.notification_type,
        subject=log.subject,
        template_id=log.template_id,
        status=log.status,
        sent_at=log.sent_at,
        opened_at=log.opened_at,
        clicked_at=log.clicked_at,
        error_message=log.error_message,
        created_at=log.created_at,
    )


# 統計エンドポイント
@router.get(
    "/stats",
    response_model=NotificationStatsResponse,
    summary="通知統計を取得",
    description="自分の通知送信統計を取得します。",
)
async def get_stats(
    api_key: APIKey = Depends(get_api_key),
    manager: NotificationManager = Depends(get_manager),
) -> NotificationStatsResponse:
    """通知統計を取得"""
    stats = manager.get_stats(api_key.owner_id)
    return NotificationStatsResponse(**stats)


@router.get(
    "/stats/all",
    response_model=NotificationStatsResponse,
    summary="全体統計を取得（管理者）",
    description="全ユーザーの通知統計を取得します。管理者権限が必要です。",
)
async def get_all_stats(
    api_key: APIKey = Depends(TierChecker(APIKeyTier.ENTERPRISE)),
    manager: NotificationManager = Depends(get_manager),
) -> NotificationStatsResponse:
    """全体統計を取得"""
    stats = manager.get_stats()
    return NotificationStatsResponse(**stats)


# トラッキングエンドポイント（メール開封・クリック追跡）
@router.get(
    "/track/open/{log_id}",
    summary="メール開封トラッキング",
    description="メール開封を記録します（トラッキングピクセル用）。",
    include_in_schema=False,
)
async def track_open(
    log_id: str,
    manager: NotificationManager = Depends(get_manager),
) -> Response:
    """メール開封をトラッキング"""
    manager.mark_opened(log_id)

    # 1x1透明GIF画像を返す
    gif_bytes = (
        b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff"
        b"\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00"
        b"\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
    )

    return Response(
        content=gif_bytes,
        media_type="image/gif",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get(
    "/track/click/{log_id}",
    summary="リンククリックトラッキング",
    description="メール内リンクのクリックを記録してリダイレクトします。",
    include_in_schema=False,
)
async def track_click(
    log_id: str,
    url: str = Query(...),
    manager: NotificationManager = Depends(get_manager),
) -> Response:
    """リンククリックをトラッキング"""
    manager.mark_clicked(log_id)

    return Response(
        status_code=302,
        headers={"Location": url},
    )


# メールサービス状態エンドポイント
@router.get(
    "/service/status",
    response_model=EmailServiceStatusResponse,
    summary="メールサービス状態を取得",
    description="メールサービスの設定状態を取得します。",
)
async def get_service_status(
    manager: NotificationManager = Depends(get_manager),
) -> EmailServiceStatusResponse:
    """メールサービス状態を取得"""
    service = manager.email_service
    config = service.config

    return EmailServiceStatusResponse(
        configured=service.is_configured(),
        enabled=config.enabled,
        smtp_host=config.smtp_host if service.is_configured() else None,
        from_email=config.from_email if service.is_configured() else None,
    )


# テストメール送信（管理者用）
@router.post(
    "/test",
    response_model=SendNotificationResponse,
    summary="テストメールを送信（管理者）",
    description="テストメールを送信します。管理者権限が必要です。",
)
async def send_test_email(
    request: TestEmailRequest,
    api_key: APIKey = Depends(TierChecker(APIKeyTier.ENTERPRISE)),
    manager: NotificationManager = Depends(get_manager),
) -> SendNotificationResponse:
    """テストメールを送信"""
    # テスト用のダミー設定を作成
    test_user_id = f"test_{api_key.owner_id}"
    manager.create_default_preference(
        user_id=test_user_id,
        email=request.email,
    )

    success, log_id, error = await manager.send_notification(
        user_id=test_user_id,
        notification_type=request.notification_type,
        context={
            "user_name": "テストユーザー",
            **request.context,
        },
        force=True,
    )

    return SendNotificationResponse(
        success=success,
        log_id=log_id,
        error=error,
    )


# 配信停止エンドポイント（公開）
@router.post(
    "/unsubscribe",
    summary="配信停止",
    description="メール配信を停止します。",
)
async def unsubscribe(
    request: UnsubscribeRequest,
    manager: NotificationManager = Depends(get_manager),
) -> dict[str, Any]:
    """配信停止"""
    preference = manager.get_preference(request.user_id)

    if not preference:
        raise HTTPException(status_code=404, detail="User not found")

    if request.unsubscribe_all:
        # 全配信停止
        manager.update_preference(
            request.user_id,
            marketing_emails=False,
            usage_alerts=False,
            weekly_summary=False,
            monthly_report=False,
            referral_notifications=False,
        )
        return {"message": "全てのメール配信を停止しました"}

    if request.notification_types:
        # 特定タイプのみ停止
        updates: dict[str, bool] = {}
        for nt in request.notification_types:
            if nt in {NotificationType.WEEKLY_SUMMARY}:
                updates["weekly_summary"] = False
            elif nt in {NotificationType.MONTHLY_REPORT}:
                updates["monthly_report"] = False
            elif nt in {NotificationType.REFERRAL_SIGNED_UP, NotificationType.REFERRAL_REWARD}:
                updates["referral_notifications"] = False
            elif nt in {NotificationType.USAGE_WARNING, NotificationType.USAGE_LIMIT_REACHED, NotificationType.CREDITS_LOW}:
                updates["usage_alerts"] = False

        if updates:
            manager.update_preference(request.user_id, **updates)

        return {"message": f"指定された{len(request.notification_types)}種類の通知を停止しました"}

    return {"message": "変更はありません"}


# 通知タイプ一覧エンドポイント
@router.get(
    "/types",
    summary="通知タイプ一覧を取得",
    description="利用可能な通知タイプの一覧を取得します。",
)
async def get_notification_types() -> dict[str, Any]:
    """通知タイプ一覧を取得"""
    return {
        "types": [
            {
                "value": nt.value,
                "name": nt.name,
                "category": _get_notification_category(nt),
            }
            for nt in NotificationType
        ]
    }


def _get_notification_category(nt: NotificationType) -> str:
    """通知タイプのカテゴリを取得"""
    transactional = {
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

    usage = {
        NotificationType.USAGE_WARNING,
        NotificationType.USAGE_LIMIT_REACHED,
        NotificationType.CREDITS_LOW,
        NotificationType.TRIAL_ENDING,
    }

    referral = {
        NotificationType.REFERRAL_SIGNED_UP,
        NotificationType.REFERRAL_REWARD,
    }

    reports = {
        NotificationType.WEEKLY_SUMMARY,
        NotificationType.MONTHLY_REPORT,
    }

    if nt in transactional:
        return "transactional"
    if nt in usage:
        return "usage"
    if nt in referral:
        return "referral"
    if nt in reports:
        return "reports"
    return "marketing"
