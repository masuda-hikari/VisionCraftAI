# -*- coding: utf-8 -*-
"""
VisionCraftAI - 認証APIルーター

APIキー管理のエンドポイントを定義します。
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.auth.models import APIKey, APIKeyTier
from src.api.auth.key_manager import get_key_manager, APIKeyManager
from src.api.auth.rate_limiter import get_rate_limiter, RateLimiter
from src.api.auth.dependencies import (
    get_api_key,
    get_optional_api_key,
    check_rate_limit,
    TierChecker,
)
from src.api.auth.schemas import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyInfoResponse,
    APIKeyListResponse,
    QuotaResponse,
    RateLimitResponse,
    APIKeyUpdateRequest,
    APIKeyUpdateResponse,
    TokenUsageResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# =====================
# APIキー管理
# =====================

@router.post(
    "/keys",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="APIキー作成",
    description="新しいAPIキーを作成します。管理者またはEnterpriseプラン限定。",
)
async def create_api_key(
    request: APIKeyCreateRequest,
    # 本番環境では管理者認証を追加
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> APIKeyCreateResponse:
    """
    APIキーを作成

    - tier: プラン階層を指定
    - 作成されたキーは一度だけ表示されます
    """
    # プラン階層の検証
    try:
        tier = APIKeyTier(request.tier)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_TIER",
                "message": f"無効なプラン階層: {request.tier}",
                "valid_tiers": [t.value for t in APIKeyTier],
            },
        )

    # キー作成
    api_key, raw_key = key_manager.create_key(
        tier=tier,
        name=request.name,
        description=request.description,
        expires_at=request.expires_at,
        allowed_ips=request.allowed_ips,
    )

    return APIKeyCreateResponse(
        success=True,
        key_id=api_key.key_id,
        api_key=raw_key,
        tier=api_key.tier.value,
    )


@router.get(
    "/keys",
    response_model=APIKeyListResponse,
    summary="APIキー一覧",
    description="所有するAPIキーの一覧を取得します。",
)
async def list_api_keys(
    active_only: bool = Query(True, description="アクティブなキーのみ"),
    api_key: APIKey = Depends(get_api_key),
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> APIKeyListResponse:
    """
    APIキー一覧を取得

    - 認証済みユーザーの所有キーのみ表示
    """
    keys = key_manager.list_keys(
        owner_id=api_key.owner_id,
        active_only=active_only,
    )

    return APIKeyListResponse(
        total=len(keys),
        keys=[
            APIKeyInfoResponse(
                key_id=k.key_id,
                tier=k.tier.value,
                name=k.name,
                description=k.description,
                is_active=k.is_active,
                created_at=k.created_at,
                last_used_at=k.last_used_at,
                expires_at=k.expires_at,
                allowed_ips=k.allowed_ips,
            )
            for k in keys
        ],
    )


@router.get(
    "/keys/me",
    response_model=APIKeyInfoResponse,
    summary="現在のAPIキー情報",
    description="現在使用中のAPIキーの情報を取得します。",
)
async def get_current_key_info(
    api_key: APIKey = Depends(get_api_key),
) -> APIKeyInfoResponse:
    """
    現在のAPIキー情報を取得
    """
    return APIKeyInfoResponse(
        key_id=api_key.key_id,
        tier=api_key.tier.value,
        name=api_key.name,
        description=api_key.description,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        allowed_ips=api_key.allowed_ips,
    )


@router.patch(
    "/keys/{key_id}",
    response_model=APIKeyUpdateResponse,
    summary="APIキー更新",
    description="APIキーの情報を更新します。",
)
async def update_api_key(
    key_id: str,
    request: APIKeyUpdateRequest,
    api_key: APIKey = Depends(get_api_key),
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> APIKeyUpdateResponse:
    """
    APIキーを更新

    - 自分のキーのみ更新可能
    """
    # 所有確認（または管理者権限）
    target_key = key_manager.get_key(key_id)
    if not target_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "KEY_NOT_FOUND", "message": "APIキーが見つかりません"},
        )

    if target_key.owner_id != api_key.owner_id and api_key.tier != APIKeyTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "このキーを更新する権限がありません"},
        )

    # 更新
    updated_key = key_manager.update_key(
        key_id=key_id,
        name=request.name,
        description=request.description,
        is_active=request.is_active,
        expires_at=request.expires_at,
        allowed_ips=request.allowed_ips,
    )

    if not updated_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "UPDATE_FAILED", "message": "更新に失敗しました"},
        )

    return APIKeyUpdateResponse(
        success=True,
        key_id=key_id,
        message="APIキーを更新しました",
    )


@router.delete(
    "/keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="APIキー削除",
    description="APIキーを無効化・削除します。",
)
async def revoke_api_key(
    key_id: str,
    permanent: bool = Query(False, description="永久削除（true）または無効化（false）"),
    api_key: APIKey = Depends(get_api_key),
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> None:
    """
    APIキーを削除/無効化

    - permanent=false: 無効化（復旧可能）
    - permanent=true: 永久削除
    """
    # 所有確認
    target_key = key_manager.get_key(key_id)
    if not target_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "KEY_NOT_FOUND", "message": "APIキーが見つかりません"},
        )

    if target_key.owner_id != api_key.owner_id and api_key.tier != APIKeyTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "このキーを削除する権限がありません"},
        )

    if permanent:
        success = key_manager.delete_key(key_id)
    else:
        success = key_manager.revoke_key(key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "DELETE_FAILED", "message": "削除に失敗しました"},
        )


# =====================
# クォータ・使用量
# =====================

@router.get(
    "/quota",
    response_model=QuotaResponse,
    summary="クォータ状況",
    description="現在のクォータ使用状況を取得します。",
)
async def get_quota_status(
    api_key: APIKey = Depends(get_api_key),
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> QuotaResponse:
    """
    クォータ状況を取得

    - 月間・日間の残り使用量
    - 解像度制限
    - バッチ処理制限
    """
    status = key_manager.get_quota_status(api_key.key_id)

    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "KEY_NOT_FOUND", "message": "APIキーが見つかりません"},
        )

    return QuotaResponse(**status)


@router.get(
    "/usage",
    response_model=TokenUsageResponse,
    summary="使用量詳細",
    description="詳細な使用量情報を取得します。",
)
async def get_usage_details(
    api_key: APIKey = Depends(get_api_key),
) -> TokenUsageResponse:
    """
    使用量詳細を取得
    """
    remaining = api_key.quota.get_remaining()

    return TokenUsageResponse(
        key_id=api_key.key_id,
        tier=api_key.tier.value,
        monthly_used=api_key.quota.monthly_used,
        monthly_limit=api_key.quota.monthly_limit,
        monthly_remaining=remaining["monthly_remaining"],
        daily_used=api_key.quota.daily_used,
        daily_limit=api_key.quota.daily_limit,
        daily_remaining=remaining["daily_remaining"],
        reset_dates={
            "monthly_reset": api_key.quota.last_monthly_reset,
            "daily_reset": api_key.quota.last_daily_reset,
        },
    )


# =====================
# レート制限
# =====================

@router.get(
    "/rate-limit",
    response_model=RateLimitResponse,
    summary="レート制限状況",
    description="現在のレート制限状況を取得します。",
)
async def get_rate_limit_status(
    api_key: APIKey = Depends(get_api_key),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> RateLimitResponse:
    """
    レート制限状況を取得

    - 現在のリクエスト数
    - 残りリクエスト数
    - リセット時刻
    """
    status = rate_limiter.get_status(api_key.key_id)
    return RateLimitResponse(**status)


# =====================
# 認証確認
# =====================

@router.get(
    "/verify",
    summary="認証確認",
    description="APIキーの有効性を確認します。",
)
async def verify_api_key(
    api_key: APIKey = Depends(get_api_key),
) -> dict:
    """
    APIキーの有効性を確認

    - 有効なキーの場合は情報を返す
    - 無効な場合は401エラー
    """
    return {
        "valid": True,
        "key_id": api_key.key_id,
        "tier": api_key.tier.value,
        "name": api_key.name,
        "expires_at": api_key.expires_at,
    }
