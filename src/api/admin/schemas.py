# -*- coding: utf-8 -*-
"""
VisionCraftAI - 管理者APIスキーマ
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RevenueMetrics(BaseModel):
    """収益メトリクス"""
    total_revenue: float = Field(..., description="累計収益（USD）")
    monthly_revenue: float = Field(..., description="今月の収益（USD）")
    daily_revenue: float = Field(..., description="今日の収益（USD）")
    subscription_revenue: float = Field(..., description="サブスクリプション収益（USD）")
    credit_revenue: float = Field(..., description="クレジット収益（USD）")
    mrr: float = Field(..., description="月次経常収益（MRR）")
    arr: float = Field(..., description="年次経常収益（ARR）")


class UserMetrics(BaseModel):
    """ユーザーメトリクス"""
    total_users: int = Field(..., description="総ユーザー数")
    active_users: int = Field(..., description="アクティブユーザー数（30日以内）")
    new_users_today: int = Field(..., description="今日の新規ユーザー数")
    new_users_month: int = Field(..., description="今月の新規ユーザー数")
    paying_users: int = Field(..., description="課金ユーザー数")
    free_users: int = Field(..., description="無料ユーザー数")
    churn_rate: float = Field(..., description="解約率（%）")


class UsageMetrics(BaseModel):
    """使用量メトリクス"""
    total_generations: int = Field(..., description="累計生成回数")
    monthly_generations: int = Field(..., description="今月の生成回数")
    daily_generations: int = Field(..., description="今日の生成回数")
    average_per_user: float = Field(..., description="ユーザーあたり平均生成回数")
    api_calls_today: int = Field(..., description="今日のAPI呼び出し回数")
    error_rate: float = Field(..., description="エラー率（%）")


class PlanDistribution(BaseModel):
    """プラン分布"""
    free: int = Field(..., description="Freeプランユーザー数")
    basic: int = Field(..., description="Basicプランユーザー数")
    pro: int = Field(..., description="Proプランユーザー数")
    enterprise: int = Field(..., description="Enterpriseプランユーザー数")


class DashboardSummary(BaseModel):
    """ダッシュボード概要"""
    revenue: RevenueMetrics
    users: UserMetrics
    usage: UsageMetrics
    plan_distribution: PlanDistribution
    last_updated: datetime = Field(default_factory=datetime.now)


class UserListItem(BaseModel):
    """ユーザー一覧アイテム"""
    user_id: str
    email: Optional[str] = None
    plan: str
    created_at: datetime
    last_active: Optional[datetime] = None
    total_generations: int
    total_spent: float
    is_active: bool


class UserListResponse(BaseModel):
    """ユーザー一覧レスポンス"""
    users: list[UserListItem]
    total: int
    page: int
    per_page: int
    total_pages: int


class RevenueChartData(BaseModel):
    """収益チャートデータ"""
    date: str
    revenue: float
    subscriptions: float
    credits: float


class UsageChartData(BaseModel):
    """使用量チャートデータ"""
    date: str
    generations: int
    api_calls: int
    errors: int


class SystemHealth(BaseModel):
    """システムヘルス"""
    api_status: str = Field(..., description="API状態（healthy/degraded/down）")
    database_status: str = Field(..., description="データベース状態")
    gemini_api_status: str = Field(..., description="Gemini API状態")
    stripe_status: str = Field(..., description="Stripe状態")
    error_count_24h: int = Field(..., description="24時間以内のエラー数")
    avg_response_time_ms: float = Field(..., description="平均レスポンス時間（ms）")
