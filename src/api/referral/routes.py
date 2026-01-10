# -*- coding: utf-8 -*-
"""
VisionCraftAI - リファラルAPIルーター

紹介コードの管理、適用、統計のエンドポイントを提供します。
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..auth.dependencies import get_api_key, get_optional_api_key
from ..auth.models import APIKey
from .manager import ReferralManager, get_referral_manager
from .schemas import (
    ApplyCodeRequest,
    ApplyCodeResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    ReferralCodeCreate,
    ReferralCodeResponse,
    ReferralResponse,
    ReferralStatsResponse,
    ValidateCodeResponse,
)

router = APIRouter(prefix="/referral", tags=["referral"])


def get_manager() -> ReferralManager:
    """リファラルマネージャーを取得"""
    storage_path = Path("data/referrals")
    return get_referral_manager(storage_path)


@router.post("/code", response_model=ReferralCodeResponse)
async def create_referral_code(
    request: Request,
    body: ReferralCodeCreate = ReferralCodeCreate(),
    api_key: APIKey = Depends(get_api_key),
    manager: ReferralManager = Depends(get_manager),
) -> ReferralCodeResponse:
    """
    紹介コードを作成

    ユーザーごとに1つの紹介コードを作成します。
    既にコードがある場合は既存のコードを返します。
    """
    code = manager.create_code(
        owner_user_id=api_key.owner_id or api_key.key_id,
        owner_api_key_id=api_key.key_id,
        reward_type=body.reward_type,
        max_uses=body.max_uses,
    )

    # 共有用URL生成
    base_url = str(request.base_url).rstrip("/")
    share_url = f"{base_url}/?ref={code.code}"

    return ReferralCodeResponse(
        code_id=code.code_id,
        code=code.code,
        referrer_reward_credits=code.referrer_reward_credits,
        referee_reward_credits=code.referee_reward_credits,
        max_uses=code.max_uses,
        current_uses=code.current_uses,
        expires_at=code.expires_at,
        is_active=code.is_active,
        share_url=share_url,
    )


@router.get("/code", response_model=ReferralCodeResponse)
async def get_my_referral_code(
    request: Request,
    api_key: APIKey = Depends(get_api_key),
    manager: ReferralManager = Depends(get_manager),
) -> ReferralCodeResponse:
    """
    自分の紹介コードを取得

    コードがない場合は自動的に作成します。
    """
    user_id = api_key.owner_id or api_key.key_id
    code = manager.get_user_code(user_id)

    if not code:
        # 自動作成
        code = manager.create_code(
            owner_user_id=user_id,
            owner_api_key_id=api_key.key_id,
        )

    base_url = str(request.base_url).rstrip("/")
    share_url = f"{base_url}/?ref={code.code}"

    return ReferralCodeResponse(
        code_id=code.code_id,
        code=code.code,
        referrer_reward_credits=code.referrer_reward_credits,
        referee_reward_credits=code.referee_reward_credits,
        max_uses=code.max_uses,
        current_uses=code.current_uses,
        expires_at=code.expires_at,
        is_active=code.is_active,
        share_url=share_url,
    )


@router.get("/validate", response_model=ValidateCodeResponse)
async def validate_referral_code(
    code: str = Query(..., min_length=1, max_length=20, description="紹介コード"),
    manager: ReferralManager = Depends(get_manager),
) -> ValidateCodeResponse:
    """
    紹介コードを検証

    コードが有効かどうかを確認します（認証不要）。
    """
    ref_code = manager.get_code(code)

    if not ref_code:
        return ValidateCodeResponse(
            valid=False,
            message="無効な紹介コードです",
            reward_credits=0,
        )

    is_valid, reason = ref_code.is_valid()

    if not is_valid:
        return ValidateCodeResponse(
            valid=False,
            message=reason,
            reward_credits=0,
        )

    return ValidateCodeResponse(
        valid=True,
        message="有効な紹介コードです",
        referrer_name=None,  # プライバシー保護のため非公開
        reward_credits=ref_code.referee_reward_credits,
    )


@router.post("/apply", response_model=ApplyCodeResponse)
async def apply_referral_code(
    body: ApplyCodeRequest,
    api_key: APIKey = Depends(get_api_key),
    manager: ReferralManager = Depends(get_manager),
) -> ApplyCodeResponse:
    """
    紹介コードを適用

    新規ユーザーが紹介コードを適用してボーナスを獲得します。
    """
    user_id = api_key.owner_id or api_key.key_id

    success, message, referral = manager.apply_code(
        code=body.code,
        referee_user_id=user_id,
        referee_api_key_id=api_key.key_id,
    )

    if not success or not referral:
        return ApplyCodeResponse(
            success=False,
            message=message,
            referral_id=None,
            reward_credits=0,
        )

    return ApplyCodeResponse(
        success=True,
        message=message,
        referral_id=referral.referral_id,
        reward_credits=referral.referee_reward_credits,
    )


@router.get("/referrals", response_model=list[ReferralResponse])
async def get_my_referrals(
    api_key: APIKey = Depends(get_api_key),
    manager: ReferralManager = Depends(get_manager),
) -> list[ReferralResponse]:
    """
    自分の紹介一覧を取得

    紹介者として行った紹介の一覧を取得します。
    """
    user_id = api_key.owner_id or api_key.key_id
    referrals = manager.get_user_referrals(user_id, as_referrer=True)

    return [
        ReferralResponse(
            referral_id=r.referral_id,
            referral_code=r.referral_code,
            referrer_user_id=r.referrer_user_id,
            referee_user_id=r.referee_user_id,
            status=r.status.value,
            referrer_reward_credits=r.referrer_reward_credits,
            referee_reward_credits=r.referee_reward_credits,
            referrer_rewarded=r.referrer_rewarded_at is not None,
            referee_rewarded=r.referee_rewarded_at is not None,
            created_at=r.created_at,
        )
        for r in referrals
    ]


@router.get("/stats", response_model=ReferralStatsResponse)
async def get_referral_stats(
    api_key: APIKey = Depends(get_api_key),
    manager: ReferralManager = Depends(get_manager),
) -> ReferralStatsResponse:
    """
    リファラル統計を取得

    自分の紹介実績の統計情報を取得します。
    """
    user_id = api_key.owner_id or api_key.key_id
    stats = manager.get_stats(user_id)

    return ReferralStatsResponse(
        total_referrals=stats.total_referrals,
        successful_referrals=stats.successful_referrals,
        pending_referrals=stats.pending_referrals,
        total_credits_earned=stats.total_credits_earned,
        rank=stats.rank,
    )


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(default=10, ge=1, le=100, description="取得件数"),
    manager: ReferralManager = Depends(get_manager),
) -> LeaderboardResponse:
    """
    リファラルランキングを取得

    紹介成功数のランキングを取得します（認証不要）。
    """
    leaderboard = manager.get_leaderboard(limit)

    entries = [
        LeaderboardEntry(
            rank=i + 1,
            user_id=entry["user_id"][:8] + "...",  # プライバシー保護
            successful_referrals=entry["successful_referrals"],
            total_credits_earned=entry["total_credits_earned"],
        )
        for i, entry in enumerate(leaderboard)
    ]

    return LeaderboardResponse(
        leaderboard=entries,
        updated_at=datetime.now().isoformat(),
    )


@router.get("/pending-rewards")
async def get_pending_rewards(
    api_key: APIKey = Depends(get_api_key),
    manager: ReferralManager = Depends(get_manager),
) -> dict:
    """
    報酬付与待ちのリファラルを取得

    クレジット付与待ちのリファラル一覧を取得します。
    """
    user_id = api_key.owner_id or api_key.key_id
    pending = manager.get_pending_rewards(user_id)

    total_pending_credits = 0
    for referral in pending:
        if referral.referrer_user_id == user_id and not referral.referrer_rewarded_at:
            total_pending_credits += referral.referrer_reward_credits
        if referral.referee_user_id == user_id and not referral.referee_rewarded_at:
            total_pending_credits += referral.referee_reward_credits

    return {
        "pending_count": len(pending),
        "total_pending_credits": total_pending_credits,
        "referrals": [
            {
                "referral_id": r.referral_id,
                "type": "referrer" if r.referrer_user_id == user_id else "referee",
                "credits": (
                    r.referrer_reward_credits
                    if r.referrer_user_id == user_id
                    else r.referee_reward_credits
                ),
            }
            for r in pending
        ],
    }
