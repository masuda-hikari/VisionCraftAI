# -*- coding: utf-8 -*-
"""
VisionCraftAI - 認証・認可モジュール

APIキー認証とレート制限を提供します。
"""

from src.api.auth.models import APIKey, APIKeyTier, UsageQuota
from src.api.auth.key_manager import APIKeyManager
from src.api.auth.dependencies import (
    get_api_key,
    get_optional_api_key,
    require_tier,
    check_rate_limit,
)
from src.api.auth.rate_limiter import RateLimiter, RateLimitConfig

__all__ = [
    "APIKey",
    "APIKeyTier",
    "UsageQuota",
    "APIKeyManager",
    "get_api_key",
    "get_optional_api_key",
    "require_tier",
    "check_rate_limit",
    "RateLimiter",
    "RateLimitConfig",
]
