# -*- coding: utf-8 -*-
"""
VisionCraftAI - 分析・A/BテストAPIスキーマ

A/Bテストと分析APIのリクエスト/レスポンススキーマを定義します。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.api.analytics.models import ABTestStatus, ConversionGoalType, EventType


# ==================== A/Bテスト関連 ====================


class VariantCreate(BaseModel):
    """バリアント作成リクエスト"""

    name: str = Field(..., description="バリアント名", min_length=1, max_length=100)
    description: str = Field("", description="説明", max_length=500)
    weight: float = Field(50.0, description="トラフィック配分（%）", ge=0, le=100)
    config: dict = Field(default_factory=dict, description="バリアント固有の設定")


class VariantResponse(BaseModel):
    """バリアントレスポンス"""

    id: str
    name: str
    description: str
    weight: float
    config: dict
    impressions: int
    conversions: int
    revenue: float
    conversion_rate: float
    revenue_per_impression: float


class ABTestCreate(BaseModel):
    """A/Bテスト作成リクエスト"""

    name: str = Field(..., description="テスト名", min_length=1, max_length=200)
    description: str = Field("", description="説明", max_length=1000)
    goal_type: ConversionGoalType = Field(
        ConversionGoalType.SUBSCRIPTION,
        description="目標タイプ",
    )
    goal_event: str = Field("", description="目標イベント名", max_length=100)
    variants: list[VariantCreate] = Field(
        default_factory=list,
        description="バリアントリスト（省略時は後から追加）",
    )


class ABTestResponse(BaseModel):
    """A/Bテストレスポンス"""

    id: str
    name: str
    description: str
    status: str
    variants: list[VariantResponse]
    goal_type: str
    goal_event: str
    start_date: Optional[str]
    end_date: Optional[str]
    created_at: str
    updated_at: str
    created_by: str
    minimum_sample_size: int
    confidence_level: float
    total_impressions: int
    total_conversions: int
    total_revenue: float
    winner_id: Optional[str]


class ABTestResultResponse(BaseModel):
    """A/Bテスト結果レスポンス"""

    id: str
    name: str
    status: str
    variants: list[VariantResponse]
    total_impressions: int
    total_conversions: int
    total_revenue: float
    winner_id: Optional[str]
    has_sufficient_sample: bool
    improvement_percent: Optional[float] = None


class ABTestAssignmentResponse(BaseModel):
    """バリアント割り当てレスポンス"""

    user_id: str
    test_id: str
    variant_id: str
    assigned_at: str
    converted: bool
    converted_at: Optional[str]
    revenue: float


class RecordConversionRequest(BaseModel):
    """コンバージョン記録リクエスト"""

    user_id: str = Field(..., description="ユーザーID")
    revenue: float = Field(0.0, description="収益", ge=0)


class ABTestListResponse(BaseModel):
    """A/Bテスト一覧レスポンス"""

    tests: list[ABTestResponse]
    total: int


# ==================== 分析イベント関連 ====================


class TrackEventRequest(BaseModel):
    """イベント記録リクエスト"""

    event_type: EventType = Field(..., description="イベントタイプ")
    user_id: Optional[str] = Field(None, description="ユーザーID")
    session_id: Optional[str] = Field(None, description="セッションID")
    event_name: str = Field("", description="イベント名", max_length=100)
    event_data: dict = Field(default_factory=dict, description="イベントデータ")

    # ページ情報
    page_url: str = Field("", description="ページURL", max_length=500)
    page_title: str = Field("", description="ページタイトル", max_length=200)
    referrer: str = Field("", description="リファラー", max_length=500)

    # UTMパラメータ
    utm_source: str = Field("", description="UTMソース", max_length=100)
    utm_medium: str = Field("", description="UTMメディア", max_length=100)
    utm_campaign: str = Field("", description="UTMキャンペーン", max_length=100)
    utm_term: str = Field("", description="UTM検索ワード", max_length=100)
    utm_content: str = Field("", description="UTMコンテンツ", max_length=100)

    # 収益
    revenue: float = Field(0.0, description="収益", ge=0)
    currency: str = Field("USD", description="通貨", max_length=3)


class EventResponse(BaseModel):
    """イベントレスポンス"""

    id: str
    event_type: str
    user_id: Optional[str]
    session_id: Optional[str]
    event_name: str
    event_data: dict
    page_url: str
    page_title: str
    referrer: str
    utm_source: str
    utm_medium: str
    utm_campaign: str
    timestamp: str
    revenue: float
    currency: str


class DailyStatsResponse(BaseModel):
    """日次統計レスポンス"""

    date: str
    total_events: int
    unique_users: int
    unique_sessions: int
    event_counts: dict[str, int]
    revenue: float


class SummaryResponse(BaseModel):
    """サマリー統計レスポンス"""

    period_days: int
    start_date: str
    end_date: str
    total_events: int
    unique_users: int
    unique_sessions: int
    event_counts: dict[str, int]
    total_revenue: float


# ==================== ファネル・リテンション ====================


class FunnelStepResponse(BaseModel):
    """ファネルステップレスポンス"""

    step: int
    event_type: str
    user_count: int
    conversion_rate: float
    drop_off: int


class FunnelResponse(BaseModel):
    """ファネル分析レスポンス"""

    steps: list[FunnelStepResponse]
    overall_conversion: float
    period: dict[str, str]


class FunnelRequest(BaseModel):
    """ファネル分析リクエスト"""

    steps: list[EventType] = Field(
        ...,
        description="ファネルステップ（イベントタイプのリスト）",
        min_length=2,
        max_length=10,
    )
    start_date: Optional[datetime] = Field(None, description="開始日")
    end_date: Optional[datetime] = Field(None, description="終了日")


class RetentionDayResponse(BaseModel):
    """リテンション日次レスポンス"""

    day: int
    date: str
    retained_users: int
    retention_rate: float


class RetentionResponse(BaseModel):
    """リテンション分析レスポンス"""

    cohort_date: str
    cohort_size: int
    retention: list[RetentionDayResponse]


class RetentionRequest(BaseModel):
    """リテンション分析リクエスト"""

    cohort_date: datetime = Field(..., description="コホート日")
    periods: int = Field(7, description="分析期間（日数）", ge=1, le=90)


# ==================== ゴール関連 ====================


class GoalCreate(BaseModel):
    """ゴール作成リクエスト"""

    name: str = Field(..., description="ゴール名", min_length=1, max_length=100)
    description: str = Field("", description="説明", max_length=500)
    goal_type: ConversionGoalType = Field(
        ConversionGoalType.SUBSCRIPTION,
        description="ゴールタイプ",
    )
    event_type: EventType = Field(
        EventType.SUBSCRIPTION_START,
        description="トラッキングするイベントタイプ",
    )
    target_value: float = Field(0.0, description="目標金額", ge=0)
    target_count: int = Field(0, description="目標件数", ge=0)
    period_days: int = Field(30, description="集計期間（日数）", ge=1, le=365)


class GoalResponse(BaseModel):
    """ゴールレスポンス"""

    id: str
    name: str
    description: str
    goal_type: str
    event_type: str
    target_value: float
    target_count: int
    period_days: int
    current_value: float
    current_count: int
    value_progress: float
    count_progress: float
    created_at: str


class GoalListResponse(BaseModel):
    """ゴール一覧レスポンス"""

    goals: list[GoalResponse]
    total: int
