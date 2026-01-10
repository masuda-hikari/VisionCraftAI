# -*- coding: utf-8 -*-
"""
VisionCraftAI - オンボーディングAPIルーター

新規ユーザー導入と無料トライアルのエンドポイントを提供します。
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_api_key, get_optional_api_key
from ..auth.models import APIKey
from .manager import OnboardingManager, get_onboarding_manager
from .models import OnboardingStep
from .schemas import (
    CompleteChecklistRequest,
    CompleteStepRequest,
    ConvertTrialRequest,
    OnboardingHintResponse,
    OnboardingProgressResponse,
    StartTrialRequest,
    TrialResponse,
    TrialStatsResponse,
    UseCreditsRequest,
    WelcomeResponse,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def get_manager() -> OnboardingManager:
    """オンボーディングマネージャーを取得"""
    storage_path = Path("data/onboarding")
    return get_onboarding_manager(storage_path)


@router.get("/welcome", response_model=WelcomeResponse)
async def get_welcome_info(
    api_key: APIKey = Depends(get_api_key),
    manager: OnboardingManager = Depends(get_manager),
) -> WelcomeResponse:
    """
    ウェルカム情報を取得

    新規ユーザー向けのウェルカムメッセージとオンボーディング情報を返します。
    """
    user_id = api_key.owner_id or api_key.key_id
    progress = manager.get_or_create_progress(user_id, api_key.key_id)
    trial = manager.get_trial(user_id)

    # トライアル利用可能かチェック
    has_trial = trial is not None and trial.is_active()
    trial_credits = trial.get_remaining_credits() if trial else 20  # デフォルト値

    # 次のステップヒント
    hint = manager.get_next_step_hint(user_id)

    # ヒント生成
    tips = []
    if not progress.checklist.get("first_image_generated"):
        tips.append("まずは画像を1枚生成してみましょう！")
    if not progress.checklist.get("prompt_enhanced"):
        tips.append("プロンプト拡張機能でより詳細な画像を生成できます")
    if not progress.checklist.get("referral_code_created"):
        tips.append("友達を紹介してボーナスクレジットをゲット！")
    if api_key.tier.value == "free":
        tips.append("有料プランで高解像度画像を生成できます")

    return WelcomeResponse(
        message="VisionCraftAIへようこそ！AI画像生成を始めましょう。",
        has_trial=has_trial or trial is None,  # トライアル未使用もOK
        trial_credits=trial_credits,
        onboarding_progress=progress.get_completion_rate(),
        next_step=hint.get("step", "welcome"),
        tips=tips[:3],  # 最大3つ
    )


@router.get("/progress", response_model=OnboardingProgressResponse)
async def get_onboarding_progress(
    api_key: APIKey = Depends(get_api_key),
    manager: OnboardingManager = Depends(get_manager),
) -> OnboardingProgressResponse:
    """
    オンボーディング進捗を取得
    """
    user_id = api_key.owner_id or api_key.key_id
    progress = manager.get_or_create_progress(user_id, api_key.key_id)

    return OnboardingProgressResponse(
        user_id=progress.user_id,
        current_step=progress.current_step.value,
        completed_steps=progress.completed_steps,
        checklist=progress.checklist,
        completion_rate=progress.get_completion_rate(),
        is_completed=progress.is_completed(),
        started_at=progress.started_at,
        completed_at=progress.completed_at,
    )


@router.get("/hint", response_model=OnboardingHintResponse)
async def get_onboarding_hint(
    api_key: APIKey = Depends(get_api_key),
    manager: OnboardingManager = Depends(get_manager),
) -> OnboardingHintResponse:
    """
    次のステップのヒントを取得
    """
    user_id = api_key.owner_id or api_key.key_id
    hint = manager.get_next_step_hint(user_id)

    return OnboardingHintResponse(
        step=hint.get("step", ""),
        title=hint.get("title", ""),
        description=hint.get("description", ""),
        action=hint.get("action", ""),
        completion_rate=hint.get("completion_rate", 0.0),
    )


@router.post("/step/complete", response_model=OnboardingProgressResponse)
async def complete_onboarding_step(
    body: CompleteStepRequest,
    api_key: APIKey = Depends(get_api_key),
    manager: OnboardingManager = Depends(get_manager),
) -> OnboardingProgressResponse:
    """
    オンボーディングステップを完了
    """
    user_id = api_key.owner_id or api_key.key_id

    try:
        step = OnboardingStep(body.step)
    except ValueError:
        raise HTTPException(status_code=400, detail="無効なステップです")

    progress = manager.complete_step(user_id, step)

    return OnboardingProgressResponse(
        user_id=progress.user_id,
        current_step=progress.current_step.value,
        completed_steps=progress.completed_steps,
        checklist=progress.checklist,
        completion_rate=progress.get_completion_rate(),
        is_completed=progress.is_completed(),
        started_at=progress.started_at,
        completed_at=progress.completed_at,
    )


@router.post("/checklist/complete", response_model=OnboardingProgressResponse)
async def complete_checklist_item(
    body: CompleteChecklistRequest,
    api_key: APIKey = Depends(get_api_key),
    manager: OnboardingManager = Depends(get_manager),
) -> OnboardingProgressResponse:
    """
    チェックリスト項目を完了
    """
    user_id = api_key.owner_id or api_key.key_id

    success, progress = manager.complete_checklist_item(user_id, body.item)

    if not success:
        raise HTTPException(status_code=400, detail="無効なチェックリスト項目です")

    return OnboardingProgressResponse(
        user_id=progress.user_id,
        current_step=progress.current_step.value,
        completed_steps=progress.completed_steps,
        checklist=progress.checklist,
        completion_rate=progress.get_completion_rate(),
        is_completed=progress.is_completed(),
        started_at=progress.started_at,
        completed_at=progress.completed_at,
    )


# === トライアルエンドポイント ===


@router.post("/trial/start", response_model=TrialResponse)
async def start_free_trial(
    body: StartTrialRequest = StartTrialRequest(),
    api_key: APIKey = Depends(get_api_key),
    manager: OnboardingManager = Depends(get_manager),
) -> TrialResponse:
    """
    無料トライアルを開始

    7日間のProプラン体験が可能です。
    """
    user_id = api_key.owner_id or api_key.key_id

    success, message, trial = manager.start_trial(
        user_id=user_id,
        api_key_id=api_key.key_id,
        trial_type=body.trial_type,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return TrialResponse(
        trial_id=trial.trial_id,
        plan_id=trial.plan_id,
        status=trial.status.value,
        duration_days=trial.duration_days,
        remaining_days=trial.get_remaining_days(),
        credits_granted=trial.credits_granted,
        credits_used=trial.credits_used,
        remaining_credits=trial.get_remaining_credits(),
        images_generated=trial.images_generated,
        starts_at=trial.starts_at,
        expires_at=trial.expires_at,
        is_active=trial.is_active(),
    )


@router.get("/trial", response_model=TrialResponse)
async def get_trial_status(
    api_key: APIKey = Depends(get_api_key),
    manager: OnboardingManager = Depends(get_manager),
) -> TrialResponse:
    """
    トライアル状況を取得
    """
    user_id = api_key.owner_id or api_key.key_id
    trial = manager.get_trial(user_id)

    if not trial:
        raise HTTPException(status_code=404, detail="トライアルがありません")

    return TrialResponse(
        trial_id=trial.trial_id,
        plan_id=trial.plan_id,
        status=trial.status.value,
        duration_days=trial.duration_days,
        remaining_days=trial.get_remaining_days(),
        credits_granted=trial.credits_granted,
        credits_used=trial.credits_used,
        remaining_credits=trial.get_remaining_credits(),
        images_generated=trial.images_generated,
        starts_at=trial.starts_at,
        expires_at=trial.expires_at,
        is_active=trial.is_active(),
    )


@router.post("/trial/use-credits")
async def use_trial_credits(
    body: UseCreditsRequest = UseCreditsRequest(),
    api_key: APIKey = Depends(get_api_key),
    manager: OnboardingManager = Depends(get_manager),
) -> dict:
    """
    トライアルクレジットを使用
    """
    user_id = api_key.owner_id or api_key.key_id

    success, message = manager.use_trial_credits(user_id, body.amount)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    trial = manager.get_trial(user_id)

    return {
        "success": True,
        "message": message,
        "remaining_credits": trial.get_remaining_credits() if trial else 0,
    }


@router.post("/trial/convert")
async def convert_trial(
    body: ConvertTrialRequest,
    api_key: APIKey = Depends(get_api_key),
    manager: OnboardingManager = Depends(get_manager),
) -> dict:
    """
    トライアルを有料プランに転換
    """
    user_id = api_key.owner_id or api_key.key_id

    success, message = manager.convert_trial(user_id, body.plan_id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "converted_to": body.plan_id,
    }


@router.get("/trial/stats", response_model=TrialStatsResponse)
async def get_trial_stats(
    api_key: APIKey = Depends(get_api_key),
    manager: OnboardingManager = Depends(get_manager),
) -> TrialStatsResponse:
    """
    トライアル統計を取得（管理者向け）
    """
    stats = manager.get_trial_stats()

    return TrialStatsResponse(
        total_trials=stats["total_trials"],
        active_trials=stats["active_trials"],
        converted_trials=stats["converted_trials"],
        expired_trials=stats["expired_trials"],
        conversion_rate=stats["conversion_rate"],
    )
