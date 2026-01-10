# -*- coding: utf-8 -*-
"""
VisionCraftAI - 分析・A/BテストAPIルート

A/Bテストと分析のAPIエンドポイントを定義します。
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.analytics.manager import (
    ABTestManager,
    AnalyticsTracker,
    get_ab_test_manager,
    get_analytics_tracker,
)
from src.api.analytics.models import ABTestStatus, EventType
from src.api.analytics.schemas import (
    ABTestCreate,
    ABTestListResponse,
    ABTestResponse,
    ABTestResultResponse,
    ABTestAssignmentResponse,
    DailyStatsResponse,
    EventResponse,
    FunnelRequest,
    FunnelResponse,
    GoalCreate,
    GoalListResponse,
    GoalResponse,
    RecordConversionRequest,
    RetentionRequest,
    RetentionResponse,
    SummaryResponse,
    TrackEventRequest,
    VariantCreate,
    VariantResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ==================== A/Bテストエンドポイント ====================


@router.post(
    "/ab-tests",
    response_model=ABTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="A/Bテスト作成",
    description="新しいA/Bテストを作成します。",
)
async def create_ab_test(
    request: ABTestCreate,
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """A/Bテストを作成"""
    test = manager.create_test(
        name=request.name,
        description=request.description,
        goal_type=request.goal_type,
        goal_event=request.goal_event,
    )

    # バリアントを追加
    for variant_data in request.variants:
        manager.add_variant(
            test_id=test.id,
            name=variant_data.name,
            description=variant_data.description,
            weight=variant_data.weight,
            config=variant_data.config,
        )

    return test.to_dict()


@router.get(
    "/ab-tests",
    response_model=ABTestListResponse,
    summary="A/Bテスト一覧",
    description="A/Bテストの一覧を取得します。",
)
async def list_ab_tests(
    status: Optional[ABTestStatus] = Query(None, description="ステータスでフィルタ"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """A/Bテスト一覧を取得"""
    tests = manager.list_tests(status=status, limit=limit, offset=offset)
    return {
        "tests": [t.to_dict() for t in tests],
        "total": len(tests),
    }


@router.get(
    "/ab-tests/{test_id}",
    response_model=ABTestResponse,
    summary="A/Bテスト取得",
    description="指定したA/Bテストの詳細を取得します。",
)
async def get_ab_test(
    test_id: str,
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """A/Bテストを取得"""
    test = manager.get_test(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/Bテストが見つかりません",
        )
    return test.to_dict()


@router.post(
    "/ab-tests/{test_id}/variants",
    response_model=VariantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="バリアント追加",
    description="A/Bテストにバリアントを追加します。",
)
async def add_variant(
    test_id: str,
    request: VariantCreate,
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """バリアントを追加"""
    try:
        variant = manager.add_variant(
            test_id=test_id,
            name=request.name,
            description=request.description,
            weight=request.weight,
            config=request.config,
        )
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A/Bテストが見つかりません",
            )
        return variant.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/ab-tests/{test_id}/start",
    response_model=ABTestResponse,
    summary="テスト開始",
    description="A/Bテストを開始します。",
)
async def start_ab_test(
    test_id: str,
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """A/Bテストを開始"""
    if not manager.start_test(test_id):
        test = manager.get_test(test_id)
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A/Bテストが見つかりません",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="テストを開始できません。バリアントが2つ以上必要です。",
        )
    return manager.get_test(test_id).to_dict()


@router.post(
    "/ab-tests/{test_id}/pause",
    response_model=ABTestResponse,
    summary="テスト一時停止",
    description="A/Bテストを一時停止します。",
)
async def pause_ab_test(
    test_id: str,
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """A/Bテストを一時停止"""
    if not manager.pause_test(test_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/Bテストが見つかりません",
        )
    return manager.get_test(test_id).to_dict()


@router.post(
    "/ab-tests/{test_id}/resume",
    response_model=ABTestResponse,
    summary="テスト再開",
    description="一時停止中のA/Bテストを再開します。",
)
async def resume_ab_test(
    test_id: str,
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """A/Bテストを再開"""
    if not manager.resume_test(test_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/Bテストが見つかりません",
        )
    return manager.get_test(test_id).to_dict()


@router.post(
    "/ab-tests/{test_id}/complete",
    response_model=ABTestResponse,
    summary="テスト完了",
    description="A/Bテストを完了状態にします。",
)
async def complete_ab_test(
    test_id: str,
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """A/Bテストを完了"""
    if not manager.complete_test(test_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/Bテストが見つかりません",
        )
    return manager.get_test(test_id).to_dict()


@router.get(
    "/ab-tests/{test_id}/results",
    response_model=ABTestResultResponse,
    summary="テスト結果取得",
    description="A/Bテストの結果と統計を取得します。",
)
async def get_ab_test_results(
    test_id: str,
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """A/Bテスト結果を取得"""
    results = manager.get_test_results(test_id)
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/Bテストが見つかりません",
        )
    return results


@router.post(
    "/ab-tests/{test_id}/assign",
    response_model=ABTestAssignmentResponse,
    summary="バリアント割り当て",
    description="ユーザーにバリアントを割り当てます。",
)
async def assign_variant(
    test_id: str,
    user_id: str = Query(..., description="ユーザーID"),
    force_variant_id: Optional[str] = Query(None, description="強制バリアントID（デバッグ用）"),
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """バリアントを割り当て"""
    assignment = manager.assign_variant(
        test_id=test_id,
        user_id=user_id,
        force_variant_id=force_variant_id,
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/Bテストが見つからないか、アクティブではありません",
        )
    return assignment.to_dict()


@router.get(
    "/ab-tests/{test_id}/assignment",
    response_model=ABTestAssignmentResponse,
    summary="割り当て取得",
    description="ユーザーのバリアント割り当てを取得します。",
)
async def get_assignment(
    test_id: str,
    user_id: str = Query(..., description="ユーザーID"),
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """割り当てを取得"""
    assignment = manager.get_assignment(test_id=test_id, user_id=user_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="割り当てが見つかりません",
        )
    return assignment.to_dict()


@router.post(
    "/ab-tests/{test_id}/conversion",
    status_code=status.HTTP_200_OK,
    summary="コンバージョン記録",
    description="コンバージョンを記録します。",
)
async def record_conversion(
    test_id: str,
    request: RecordConversionRequest,
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """コンバージョンを記録"""
    if not manager.record_conversion(
        test_id=test_id,
        user_id=request.user_id,
        revenue=request.revenue,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="割り当てが見つかりません",
        )
    return {"message": "コンバージョンを記録しました"}


@router.delete(
    "/ab-tests/{test_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="テスト削除",
    description="A/Bテストを削除します。",
)
async def delete_ab_test(
    test_id: str,
    manager: ABTestManager = Depends(get_ab_test_manager),
):
    """A/Bテストを削除"""
    if not manager.delete_test(test_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A/Bテストが見つかりません",
        )
    return None


# ==================== 分析イベントエンドポイント ====================


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="イベント記録",
    description="分析イベントを記録します。",
)
async def track_event(
    request: TrackEventRequest,
    tracker: AnalyticsTracker = Depends(get_analytics_tracker),
):
    """イベントを記録"""
    event = tracker.track_event(
        event_type=request.event_type,
        user_id=request.user_id,
        session_id=request.session_id,
        event_name=request.event_name,
        event_data=request.event_data,
        page_url=request.page_url,
        page_title=request.page_title,
        referrer=request.referrer,
        utm_source=request.utm_source,
        utm_medium=request.utm_medium,
        utm_campaign=request.utm_campaign,
        utm_term=request.utm_term,
        utm_content=request.utm_content,
        revenue=request.revenue,
        currency=request.currency,
    )
    return event.to_dict()


@router.get(
    "/events",
    response_model=list[EventResponse],
    summary="イベント一覧",
    description="記録されたイベントを取得します。",
)
async def list_events(
    user_id: Optional[str] = Query(None, description="ユーザーIDでフィルタ"),
    session_id: Optional[str] = Query(None, description="セッションIDでフィルタ"),
    event_type: Optional[EventType] = Query(None, description="イベントタイプでフィルタ"),
    start_date: Optional[datetime] = Query(None, description="開始日時"),
    end_date: Optional[datetime] = Query(None, description="終了日時"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    tracker: AnalyticsTracker = Depends(get_analytics_tracker),
):
    """イベント一覧を取得"""
    events = tracker.get_events(
        user_id=user_id,
        session_id=session_id,
        event_type=event_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return [e.to_dict() for e in events]


@router.get(
    "/stats/daily",
    response_model=list[DailyStatsResponse],
    summary="日次統計",
    description="日次の分析統計を取得します。",
)
async def get_daily_stats(
    start_date: Optional[datetime] = Query(None, description="開始日時"),
    end_date: Optional[datetime] = Query(None, description="終了日時"),
    tracker: AnalyticsTracker = Depends(get_analytics_tracker),
):
    """日次統計を取得"""
    return tracker.get_daily_stats(start_date=start_date, end_date=end_date)


@router.get(
    "/stats/summary",
    response_model=SummaryResponse,
    summary="サマリー統計",
    description="期間内の集計統計を取得します。",
)
async def get_summary(
    days: int = Query(30, ge=1, le=365, description="集計期間（日数）"),
    tracker: AnalyticsTracker = Depends(get_analytics_tracker),
):
    """サマリー統計を取得"""
    return tracker.get_summary(days=days)


@router.post(
    "/funnel",
    response_model=FunnelResponse,
    summary="ファネル分析",
    description="ファネル分析を実行します。",
)
async def analyze_funnel(
    request: FunnelRequest,
    tracker: AnalyticsTracker = Depends(get_analytics_tracker),
):
    """ファネル分析を実行"""
    return tracker.get_funnel(
        steps=request.steps,
        start_date=request.start_date,
        end_date=request.end_date,
    )


@router.post(
    "/retention",
    response_model=RetentionResponse,
    summary="リテンション分析",
    description="コホートリテンション分析を実行します。",
)
async def analyze_retention(
    request: RetentionRequest,
    tracker: AnalyticsTracker = Depends(get_analytics_tracker),
):
    """リテンション分析を実行"""
    return tracker.get_retention(
        cohort_date=request.cohort_date,
        periods=request.periods,
    )


# ==================== ゴールエンドポイント ====================


@router.post(
    "/goals",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ゴール作成",
    description="コンバージョンゴールを作成します。",
)
async def create_goal(
    request: GoalCreate,
    tracker: AnalyticsTracker = Depends(get_analytics_tracker),
):
    """ゴールを作成"""
    goal = tracker.create_goal(
        name=request.name,
        description=request.description,
        goal_type=request.goal_type,
        event_type=request.event_type,
        target_value=request.target_value,
        target_count=request.target_count,
        period_days=request.period_days,
    )
    return goal.to_dict()


@router.get(
    "/goals",
    response_model=GoalListResponse,
    summary="ゴール一覧",
    description="コンバージョンゴールの一覧を取得します。",
)
async def list_goals(
    tracker: AnalyticsTracker = Depends(get_analytics_tracker),
):
    """ゴール一覧を取得"""
    goals = tracker.list_goals()
    return {
        "goals": [g.to_dict() for g in goals],
        "total": len(goals),
    }


@router.get(
    "/goals/{goal_id}",
    response_model=GoalResponse,
    summary="ゴール取得",
    description="指定したコンバージョンゴールを取得します。",
)
async def get_goal(
    goal_id: str,
    tracker: AnalyticsTracker = Depends(get_analytics_tracker),
):
    """ゴールを取得"""
    goal = tracker.get_goal(goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ゴールが見つかりません",
        )
    return goal.to_dict()


# ==================== ユーティリティ ====================


@router.get(
    "/event-types",
    summary="イベントタイプ一覧",
    description="利用可能なイベントタイプの一覧を取得します。",
)
async def list_event_types():
    """イベントタイプ一覧を取得"""
    return {
        "event_types": [
            {"value": t.value, "name": t.name}
            for t in EventType
        ]
    }
