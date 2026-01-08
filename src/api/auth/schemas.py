# -*- coding: utf-8 -*-
"""
VisionCraftAI - 認証スキーマ定義

認証関連のPydanticスキーマを定義します。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class APIKeyCreateRequest(BaseModel):
    """APIキー作成リクエスト"""
    tier: str = Field(
        "free",
        description="プラン階層 (free, basic, pro, enterprise)",
        examples=["free"],
    )
    name: str = Field(
        "",
        max_length=100,
        description="キー名",
        examples=["My Application"],
    )
    description: str = Field(
        "",
        max_length=500,
        description="説明",
        examples=["開発用APIキー"],
    )
    expires_at: Optional[str] = Field(
        None,
        description="有効期限（ISO形式）",
        examples=["2025-12-31T23:59:59"],
    )
    allowed_ips: Optional[list[str]] = Field(
        None,
        description="許可IPアドレスリスト",
        examples=[["192.168.1.1", "10.0.0.0/24"]],
    )


class APIKeyCreateResponse(BaseModel):
    """APIキー作成レスポンス"""
    success: bool = True
    key_id: str = Field(..., description="キーID")
    api_key: str = Field(
        ...,
        description="APIキー（この応答でのみ表示）",
    )
    tier: str = Field(..., description="プラン階層")
    message: str = Field(
        "APIキーを作成しました。このキーは再表示できません。安全に保管してください。",
        description="メッセージ",
    )


class APIKeyInfoResponse(BaseModel):
    """APIキー情報レスポンス"""
    key_id: str
    tier: str
    name: str
    description: str
    is_active: bool
    created_at: str
    last_used_at: Optional[str]
    expires_at: Optional[str]
    allowed_ips: list[str]


class APIKeyListResponse(BaseModel):
    """APIキー一覧レスポンス"""
    total: int
    keys: list[APIKeyInfoResponse]


class QuotaResponse(BaseModel):
    """クォータ情報レスポンス"""
    key_id: str
    tier: str
    monthly_remaining: int
    daily_remaining: int
    monthly_limit: int
    daily_limit: int
    max_width: int
    max_height: int
    max_batch_size: int
    priority_processing: bool


class RateLimitResponse(BaseModel):
    """レート制限情報レスポンス"""
    key: str
    current_count: int
    limit: int
    effective_limit: int
    remaining: int
    window_seconds: int
    reset_at: float


class APIKeyUpdateRequest(BaseModel):
    """APIキー更新リクエスト"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    expires_at: Optional[str] = None
    allowed_ips: Optional[list[str]] = None


class APIKeyUpdateResponse(BaseModel):
    """APIキー更新レスポンス"""
    success: bool = True
    key_id: str
    message: str = "APIキーを更新しました"


class TokenUsageResponse(BaseModel):
    """トークン使用量レスポンス"""
    key_id: str
    tier: str
    monthly_used: int
    monthly_limit: int
    monthly_remaining: int
    daily_used: int
    daily_limit: int
    daily_remaining: int
    reset_dates: dict = Field(
        default_factory=dict,
        description="リセット日時",
    )
