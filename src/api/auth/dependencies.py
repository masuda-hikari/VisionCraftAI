# -*- coding: utf-8 -*-
"""
VisionCraftAI - 認証依存性注入

FastAPIの依存性注入を使用した認証機能を提供します。
"""

import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from src.api.auth.models import APIKey, APIKeyTier
from src.api.auth.key_manager import get_key_manager, APIKeyManager
from src.api.auth.rate_limiter import get_rate_limiter, RateLimiter

logger = logging.getLogger(__name__)


async def get_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    request: Request = None,
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> APIKey:
    """
    APIキーを取得・検証する依存性

    認証方法:
    1. X-API-Key ヘッダー
    2. Authorization: Bearer <key> ヘッダー

    Raises:
        HTTPException: 認証失敗時
    """
    raw_key = None

    # X-API-Keyヘッダーをチェック
    if x_api_key:
        raw_key = x_api_key
    # Authorizationヘッダーをチェック
    elif authorization:
        if authorization.startswith("Bearer "):
            raw_key = authorization[7:]
        else:
            raw_key = authorization

    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "MISSING_API_KEY",
                "message": "APIキーが必要です",
                "hint": "X-API-Key ヘッダーまたは Authorization: Bearer <key> を使用してください",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # クライアントIP取得
    client_ip = None
    if request:
        client_ip = request.client.host if request.client else None
        # プロキシ経由の場合
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

    # キー検証
    is_valid, api_key, reason = key_manager.validate_key(raw_key, ip=client_ip)

    if not is_valid:
        logger.warning(f"認証失敗: {reason} (IP: {client_ip})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_API_KEY",
                "message": reason,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key


async def get_optional_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    request: Request = None,
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> Optional[APIKey]:
    """
    オプショナルなAPIキー取得

    キーがない場合はNoneを返す（認証なしでも動作するエンドポイント用）
    """
    raw_key = None

    if x_api_key:
        raw_key = x_api_key
    elif authorization:
        if authorization.startswith("Bearer "):
            raw_key = authorization[7:]
        else:
            raw_key = authorization

    if not raw_key:
        return None

    # クライアントIP取得
    client_ip = None
    if request:
        client_ip = request.client.host if request.client else None
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

    # キー検証
    is_valid, api_key, _ = key_manager.validate_key(raw_key, ip=client_ip)

    return api_key if is_valid else None


def require_tier(*allowed_tiers: APIKeyTier) -> Callable:
    """
    特定のプラン階層を要求するデコレータ

    使用例:
        @router.get("/premium")
        @require_tier(APIKeyTier.PRO, APIKeyTier.ENTERPRISE)
        async def premium_endpoint(api_key: APIKey = Depends(get_api_key)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # api_keyを探す
            api_key = kwargs.get("api_key")
            if not api_key:
                for arg in args:
                    if isinstance(arg, APIKey):
                        api_key = arg
                        break

            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": "MISSING_API_KEY",
                        "message": "認証が必要です",
                    },
                )

            if api_key.tier not in allowed_tiers:
                tier_names = [t.value for t in allowed_tiers]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "INSUFFICIENT_TIER",
                        "message": f"この機能には {tier_names} プランが必要です",
                        "current_tier": api_key.tier.value,
                        "required_tiers": tier_names,
                    },
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


class TierChecker:
    """プラン階層チェック用の依存性クラス"""

    def __init__(self, *allowed_tiers: APIKeyTier):
        self.allowed_tiers = allowed_tiers

    async def __call__(self, api_key: APIKey = Depends(get_api_key)) -> APIKey:
        if api_key.tier not in self.allowed_tiers:
            tier_names = [t.value for t in self.allowed_tiers]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "INSUFFICIENT_TIER",
                    "message": f"この機能には {tier_names} プランが必要です",
                    "current_tier": api_key.tier.value,
                    "required_tiers": tier_names,
                },
            )
        return api_key


async def check_rate_limit(
    request: Request,
    api_key: Optional[APIKey] = Depends(get_optional_api_key),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> dict:
    """
    レート制限をチェックする依存性

    Returns:
        レート制限状態情報

    Raises:
        HTTPException: レート制限超過時
    """
    # キーまたはIPで識別
    if api_key:
        key = api_key.key_id
        limit = api_key.quota.rate_limit_per_minute
    else:
        # 認証なしの場合はIPでレート制限
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        key = f"ip:{client_ip}"
        limit = 10  # 認証なしの場合は厳しい制限

    # レート制限チェック
    allowed, status_info = rate_limiter.check_and_record(key, limit)

    if not allowed:
        retry_after = status_info.get("retry_after", 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": "リクエスト制限を超過しました",
                "limit": limit,
                "window_seconds": status_info.get("window_seconds", 60),
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(int(retry_after))},
        )

    return status_info


async def check_quota(
    api_key: APIKey = Depends(get_api_key),
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> dict:
    """
    クォータをチェックする依存性

    Returns:
        クォータ状態情報

    Raises:
        HTTPException: クォータ超過時
    """
    can_generate, reason = api_key.quota.can_generate(1)

    if not can_generate:
        remaining = api_key.quota.get_remaining()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "QUOTA_EXCEEDED",
                "message": reason,
                "tier": api_key.tier.value,
                **remaining,
            },
        )

    return api_key.quota.get_remaining()


async def record_usage(
    api_key: APIKey = Depends(get_api_key),
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> None:
    """
    使用量を記録する依存性

    画像生成後に呼び出して使用量を記録
    """
    success, message = key_manager.record_usage(api_key.key_id, 1)
    if not success:
        logger.error(f"使用量記録に失敗: {api_key.key_id} - {message}")


class QuotaEnforcer:
    """クォータ強制用の依存性クラス"""

    def __init__(self, count: int = 1):
        self.count = count

    async def __call__(
        self,
        api_key: APIKey = Depends(get_api_key),
        key_manager: APIKeyManager = Depends(get_key_manager),
    ) -> APIKey:
        can_generate, reason = api_key.quota.can_generate(self.count)

        if not can_generate:
            remaining = api_key.quota.get_remaining()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "QUOTA_EXCEEDED",
                    "message": reason,
                    "tier": api_key.tier.value,
                    "requested_count": self.count,
                    **remaining,
                },
            )

        return api_key
