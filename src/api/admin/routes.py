# -*- coding: utf-8 -*-
"""
VisionCraftAI - 管理者APIルート
"""

import os
import hashlib
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Header, Query
from fastapi.responses import JSONResponse

from .dashboard import AdminDashboard
from .schemas import (
    DashboardSummary,
    RevenueMetrics,
    UserMetrics,
    UsageMetrics,
    PlanDistribution,
    UserListResponse,
    RevenueChartData,
    UsageChartData,
    SystemHealth,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_admin_secret() -> str:
    """管理者シークレットを取得"""
    return os.environ.get("ADMIN_SECRET", "admin_default_secret_change_me")


def verify_admin_auth(x_admin_secret: Optional[str] = Header(None)) -> bool:
    """
    管理者認証を検証

    Args:
        x_admin_secret: 管理者シークレットヘッダー

    Returns:
        認証成功の場合True

    Raises:
        HTTPException: 認証失敗時
    """
    if not x_admin_secret:
        raise HTTPException(
            status_code=401,
            detail={"error": "UNAUTHORIZED", "message": "管理者認証が必要です"},
        )

    expected_secret = get_admin_secret()

    # タイミング攻撃を防ぐためにハッシュ比較
    provided_hash = hashlib.sha256(x_admin_secret.encode()).hexdigest()
    expected_hash = hashlib.sha256(expected_secret.encode()).hexdigest()

    if provided_hash != expected_hash:
        raise HTTPException(
            status_code=403,
            detail={"error": "FORBIDDEN", "message": "管理者認証に失敗しました"},
        )

    return True


def get_dashboard() -> AdminDashboard:
    """AdminDashboardインスタンスを取得"""
    return AdminDashboard()


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
) -> DashboardSummary:
    """
    ダッシュボード概要を取得

    収益・ユーザー・使用量の概要メトリクスを返します。
    """
    try:
        return dashboard.get_dashboard_summary()
    except Exception as e:
        logger.error(f"ダッシュボード取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue", response_model=RevenueMetrics)
async def get_revenue_metrics(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
) -> RevenueMetrics:
    """収益メトリクスを取得"""
    try:
        return dashboard.get_revenue_metrics()
    except Exception as e:
        logger.error(f"収益メトリクス取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=UserMetrics)
async def get_user_metrics(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
) -> UserMetrics:
    """ユーザーメトリクスを取得"""
    try:
        return dashboard.get_user_metrics()
    except Exception as e:
        logger.error(f"ユーザーメトリクス取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage", response_model=UsageMetrics)
async def get_usage_metrics(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
) -> UsageMetrics:
    """使用量メトリクスを取得"""
    try:
        return dashboard.get_usage_metrics()
    except Exception as e:
        logger.error(f"使用量メトリクス取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans", response_model=PlanDistribution)
async def get_plan_distribution(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
) -> PlanDistribution:
    """プラン分布を取得"""
    try:
        return dashboard.get_plan_distribution()
    except Exception as e:
        logger.error(f"プラン分布取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/list", response_model=UserListResponse)
async def get_user_list(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    plan: Optional[str] = Query(None, description="プランフィルター（free, basic, pro, enterprise）"),
) -> UserListResponse:
    """ユーザー一覧を取得"""
    try:
        result = dashboard.get_user_list(page=page, per_page=per_page, plan_filter=plan)
        return UserListResponse(**result)
    except Exception as e:
        logger.error(f"ユーザー一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/revenue", response_model=list[RevenueChartData])
async def get_revenue_chart(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
    days: int = Query(30, ge=1, le=365, description="過去N日間のデータ"),
) -> list[RevenueChartData]:
    """収益チャートデータを取得"""
    try:
        return dashboard.get_revenue_chart_data(days=days)
    except Exception as e:
        logger.error(f"収益チャート取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/usage", response_model=list[UsageChartData])
async def get_usage_chart(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
    days: int = Query(30, ge=1, le=365, description="過去N日間のデータ"),
) -> list[UsageChartData]:
    """使用量チャートデータを取得"""
    try:
        return dashboard.get_usage_chart_data(days=days)
    except Exception as e:
        logger.error(f"使用量チャート取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
) -> SystemHealth:
    """システムヘルス情報を取得"""
    try:
        return dashboard.get_system_health()
    except Exception as e:
        logger.error(f"システムヘルス取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contacts/stats")
async def get_contact_stats(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
) -> dict:
    """お問い合わせ統計を取得"""
    try:
        return dashboard.get_contact_stats()
    except Exception as e:
        logger.error(f"お問い合わせ統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_dashboard_data(
    _: bool = Depends(verify_admin_auth),
    dashboard: AdminDashboard = Depends(get_dashboard),
    format: str = Query("json", description="エクスポート形式（json）"),
) -> dict:
    """
    ダッシュボードデータをエクスポート

    Args:
        format: エクスポート形式

    Returns:
        全メトリクスを含むデータ
    """
    try:
        summary = dashboard.get_dashboard_summary()
        revenue_chart = dashboard.get_revenue_chart_data(days=30)
        usage_chart = dashboard.get_usage_chart_data(days=30)
        contact_stats = dashboard.get_contact_stats()

        return {
            "exported_at": datetime.now().isoformat(),
            "summary": summary.model_dump(),
            "revenue_chart": [r.model_dump() for r in revenue_chart],
            "usage_chart": [u.model_dump() for u in usage_chart],
            "contact_stats": contact_stats,
        }
    except Exception as e:
        logger.error(f"エクスポートエラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))
