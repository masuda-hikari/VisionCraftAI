# -*- coding: utf-8 -*-
"""
VisionCraftAI - リファラルスキーマ定義

APIリクエスト/レスポンスのスキーマを定義します。
"""

from typing import Optional

from pydantic import BaseModel, Field


class ReferralCodeCreate(BaseModel):
    """リファラルコード作成リクエスト"""
    reward_type: str = Field(
        default="default",
        description="報酬タイプ（default, premium）",
    )
    max_uses: int = Field(
        default=0,
        ge=0,
        description="最大使用回数（0=無制限）",
    )


class ReferralCodeResponse(BaseModel):
    """リファラルコードレスポンス"""
    code_id: str = Field(..., description="コードID")
    code: str = Field(..., description="紹介コード")
    referrer_reward_credits: int = Field(..., description="紹介者報酬クレジット")
    referee_reward_credits: int = Field(..., description="被紹介者報酬クレジット")
    max_uses: int = Field(..., description="最大使用回数")
    current_uses: int = Field(..., description="現在の使用回数")
    expires_at: Optional[str] = Field(None, description="有効期限")
    is_active: bool = Field(..., description="アクティブか")
    share_url: str = Field(..., description="共有用URL")


class ApplyCodeRequest(BaseModel):
    """紹介コード適用リクエスト"""
    code: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="紹介コード",
    )


class ApplyCodeResponse(BaseModel):
    """紹介コード適用レスポンス"""
    success: bool = Field(..., description="成功か")
    message: str = Field(..., description="メッセージ")
    referral_id: Optional[str] = Field(None, description="リファラルID")
    reward_credits: int = Field(default=0, description="獲得クレジット")


class ReferralResponse(BaseModel):
    """リファラルレスポンス"""
    referral_id: str = Field(..., description="リファラルID")
    referral_code: str = Field(..., description="紹介コード")
    referrer_user_id: str = Field(..., description="紹介者ユーザーID")
    referee_user_id: str = Field(..., description="被紹介者ユーザーID")
    status: str = Field(..., description="ステータス")
    referrer_reward_credits: int = Field(..., description="紹介者報酬")
    referee_reward_credits: int = Field(..., description="被紹介者報酬")
    referrer_rewarded: bool = Field(..., description="紹介者報酬付与済み")
    referee_rewarded: bool = Field(..., description="被紹介者報酬付与済み")
    created_at: str = Field(..., description="作成日時")


class ReferralStatsResponse(BaseModel):
    """リファラル統計レスポンス"""
    total_referrals: int = Field(..., description="総紹介数")
    successful_referrals: int = Field(..., description="成功した紹介数")
    pending_referrals: int = Field(..., description="保留中の紹介数")
    total_credits_earned: int = Field(..., description="累計獲得クレジット")
    rank: int = Field(..., description="ランキング順位")


class LeaderboardEntry(BaseModel):
    """ランキングエントリー"""
    rank: int = Field(..., description="順位")
    user_id: str = Field(..., description="ユーザーID")
    successful_referrals: int = Field(..., description="成功した紹介数")
    total_credits_earned: int = Field(..., description="累計獲得クレジット")


class LeaderboardResponse(BaseModel):
    """ランキングレスポンス"""
    leaderboard: list[LeaderboardEntry] = Field(..., description="ランキング")
    updated_at: str = Field(..., description="更新日時")


class ValidateCodeResponse(BaseModel):
    """コード検証レスポンス"""
    valid: bool = Field(..., description="有効か")
    message: str = Field(..., description="メッセージ")
    referrer_name: Optional[str] = Field(None, description="紹介者名")
    reward_credits: int = Field(default=0, description="獲得予定クレジット")
