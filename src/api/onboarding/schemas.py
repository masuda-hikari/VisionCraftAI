# -*- coding: utf-8 -*-
"""
VisionCraftAI - オンボーディングスキーマ定義

APIリクエスト/レスポンスのスキーマを定義します。
"""

from typing import Optional

from pydantic import BaseModel, Field


class OnboardingProgressResponse(BaseModel):
    """オンボーディング進捗レスポンス"""
    user_id: str = Field(..., description="ユーザーID")
    current_step: str = Field(..., description="現在のステップ")
    completed_steps: list[str] = Field(..., description="完了済みステップ")
    checklist: dict[str, bool] = Field(..., description="チェックリスト")
    completion_rate: float = Field(..., description="完了率")
    is_completed: bool = Field(..., description="完了済みか")
    started_at: str = Field(..., description="開始日時")
    completed_at: Optional[str] = Field(None, description="完了日時")


class OnboardingHintResponse(BaseModel):
    """オンボーディングヒントレスポンス"""
    step: str = Field(..., description="現在のステップ")
    title: str = Field(..., description="タイトル")
    description: str = Field(..., description="説明")
    action: str = Field(..., description="推奨アクション")
    completion_rate: float = Field(..., description="完了率")


class CompleteStepRequest(BaseModel):
    """ステップ完了リクエスト"""
    step: str = Field(..., description="完了するステップ")


class CompleteChecklistRequest(BaseModel):
    """チェックリスト完了リクエスト"""
    item: str = Field(..., description="完了する項目")


class StartTrialRequest(BaseModel):
    """トライアル開始リクエスト"""
    trial_type: str = Field(
        default="default",
        description="トライアルタイプ（default, extended, premium）",
    )


class TrialResponse(BaseModel):
    """トライアルレスポンス"""
    trial_id: str = Field(..., description="トライアルID")
    plan_id: str = Field(..., description="対象プラン")
    status: str = Field(..., description="ステータス")
    duration_days: int = Field(..., description="期間（日）")
    remaining_days: int = Field(..., description="残り日数")
    credits_granted: int = Field(..., description="付与クレジット")
    credits_used: int = Field(..., description="使用クレジット")
    remaining_credits: int = Field(..., description="残りクレジット")
    images_generated: int = Field(..., description="生成画像数")
    starts_at: str = Field(..., description="開始日時")
    expires_at: str = Field(..., description="終了日時")
    is_active: bool = Field(..., description="アクティブか")


class TrialStatsResponse(BaseModel):
    """トライアル統計レスポンス"""
    total_trials: int = Field(..., description="総トライアル数")
    active_trials: int = Field(..., description="アクティブ数")
    converted_trials: int = Field(..., description="転換数")
    expired_trials: int = Field(..., description="期限切れ数")
    conversion_rate: float = Field(..., description="転換率")


class UseCreditsRequest(BaseModel):
    """クレジット使用リクエスト"""
    amount: int = Field(default=1, ge=1, le=10, description="使用クレジット数")


class ConvertTrialRequest(BaseModel):
    """トライアル転換リクエスト"""
    plan_id: str = Field(..., description="転換先プラン")


class WelcomeResponse(BaseModel):
    """ウェルカムレスポンス"""
    message: str = Field(..., description="ウェルカムメッセージ")
    has_trial: bool = Field(..., description="トライアル利用可能か")
    trial_credits: int = Field(..., description="トライアルクレジット数")
    onboarding_progress: float = Field(..., description="オンボーディング進捗")
    next_step: str = Field(..., description="次のステップ")
    tips: list[str] = Field(..., description="ヒント")
