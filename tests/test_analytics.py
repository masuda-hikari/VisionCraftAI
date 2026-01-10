# -*- coding: utf-8 -*-
"""
VisionCraftAI - 分析・A/Bテストモジュールテスト

A/Bテストと分析機能のテストを行います。
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.api.analytics.manager import (
    ABTestManager,
    AnalyticsTracker,
    get_ab_test_manager,
    get_analytics_tracker,
)
from src.api.analytics.models import (
    ABTest,
    ABTestAssignment,
    ABTestStatus,
    ABTestVariant,
    AnalyticsEvent,
    ConversionGoal,
    ConversionGoalType,
    EventType,
)
from src.api.app import app

client = TestClient(app)


# ==================== モデルテスト ====================


class TestABTestVariant:
    """ABTestVariantモデルのテスト"""

    def test_create_variant(self):
        """バリアント作成テスト"""
        variant = ABTestVariant(
            id="var_test",
            name="Control",
            description="コントロールグループ",
            weight=50.0,
        )
        assert variant.id == "var_test"
        assert variant.name == "Control"
        assert variant.weight == 50.0
        assert variant.impressions == 0
        assert variant.conversions == 0

    def test_conversion_rate(self):
        """コンバージョン率計算テスト"""
        variant = ABTestVariant(id="var_1", name="Test")
        variant.impressions = 100
        variant.conversions = 25
        assert variant.conversion_rate == 25.0

    def test_conversion_rate_zero_impressions(self):
        """表示0の場合のコンバージョン率テスト"""
        variant = ABTestVariant(id="var_1", name="Test")
        assert variant.conversion_rate == 0.0

    def test_revenue_per_impression(self):
        """表示あたり収益テスト"""
        variant = ABTestVariant(id="var_1", name="Test")
        variant.impressions = 100
        variant.revenue = 500.0
        assert variant.revenue_per_impression == 5.0

    def test_to_dict(self):
        """辞書変換テスト"""
        variant = ABTestVariant(id="var_1", name="Test", weight=60.0)
        data = variant.to_dict()
        assert data["id"] == "var_1"
        assert data["name"] == "Test"
        assert data["weight"] == 60.0


class TestABTest:
    """ABTestモデルのテスト"""

    def test_create_ab_test(self):
        """A/Bテスト作成テスト"""
        test = ABTest.create(
            name="価格テスト",
            description="価格表示のA/Bテスト",
            goal_type=ConversionGoalType.PURCHASE,
        )
        assert test.id.startswith("abt_")
        assert test.name == "価格テスト"
        assert test.status == ABTestStatus.DRAFT
        assert test.goal_type == ConversionGoalType.PURCHASE

    def test_add_variant(self):
        """バリアント追加テスト"""
        test = ABTest.create(name="テスト")
        variant = test.add_variant(name="Control", weight=50.0)
        assert len(test.variants) == 1
        assert variant.name == "Control"

    def test_normalize_weights(self):
        """重み正規化テスト"""
        test = ABTest.create(name="テスト")
        test.add_variant(name="A", weight=30.0)
        test.add_variant(name="B", weight=30.0)
        # 合計60 → 100%に正規化
        total_weight = sum(v.weight for v in test.variants)
        assert abs(total_weight - 100.0) < 0.01

    def test_start_test(self):
        """テスト開始テスト"""
        test = ABTest.create(name="テスト")
        test.add_variant(name="Control", weight=50.0)
        test.add_variant(name="Treatment", weight=50.0)
        test.start()
        assert test.status == ABTestStatus.RUNNING
        assert test.start_date is not None

    def test_start_test_without_variants(self):
        """バリアントなしでの開始エラーテスト"""
        test = ABTest.create(name="テスト")
        with pytest.raises(ValueError):
            test.start()

    def test_start_test_with_one_variant(self):
        """バリアント1つでの開始エラーテスト"""
        test = ABTest.create(name="テスト")
        test.add_variant(name="Control", weight=100.0)
        with pytest.raises(ValueError):
            test.start()

    def test_pause_resume_complete(self):
        """一時停止・再開・完了テスト"""
        test = ABTest.create(name="テスト")
        test.add_variant(name="A", weight=50.0)
        test.add_variant(name="B", weight=50.0)
        test.start()

        test.pause()
        assert test.status == ABTestStatus.PAUSED

        test.resume()
        assert test.status == ABTestStatus.RUNNING

        test.complete()
        assert test.status == ABTestStatus.COMPLETED
        assert test.end_date is not None

    def test_is_active(self):
        """アクティブ判定テスト"""
        test = ABTest.create(name="テスト")
        test.add_variant(name="A", weight=50.0)
        test.add_variant(name="B", weight=50.0)

        assert not test.is_active

        test.start()
        assert test.is_active

        test.pause()
        assert not test.is_active

    def test_total_impressions_conversions_revenue(self):
        """合計統計テスト"""
        test = ABTest.create(name="テスト")
        v1 = test.add_variant(name="A", weight=50.0)
        v2 = test.add_variant(name="B", weight=50.0)

        v1.impressions = 100
        v1.conversions = 10
        v1.revenue = 500.0

        v2.impressions = 100
        v2.conversions = 20
        v2.revenue = 1000.0

        assert test.total_impressions == 200
        assert test.total_conversions == 30
        assert test.total_revenue == 1500.0

    def test_winner(self):
        """勝者判定テスト"""
        test = ABTest.create(name="テスト")
        test.minimum_sample_size = 50

        v1 = test.add_variant(name="A", weight=50.0)
        v2 = test.add_variant(name="B", weight=50.0)

        v1.impressions = 50
        v1.conversions = 5  # 10%

        v2.impressions = 50
        v2.conversions = 15  # 30%

        assert test.winner == v2

    def test_winner_insufficient_sample(self):
        """サンプル不足時の勝者判定テスト"""
        test = ABTest.create(name="テスト")
        test.minimum_sample_size = 100

        v1 = test.add_variant(name="A", weight=50.0)
        v2 = test.add_variant(name="B", weight=50.0)

        v1.impressions = 25
        v2.impressions = 25

        assert test.winner is None


class TestAnalyticsEvent:
    """AnalyticsEventモデルのテスト"""

    def test_create_event(self):
        """イベント作成テスト"""
        event = AnalyticsEvent.create(
            event_type=EventType.PAGE_VIEW,
            user_id="user_123",
            session_id="session_456",
            event_name="home_page",
        )
        assert event.id.startswith("evt_")
        assert event.event_type == EventType.PAGE_VIEW
        assert event.user_id == "user_123"
        assert event.session_id == "session_456"

    def test_event_with_utm(self):
        """UTMパラメータ付きイベントテスト"""
        event = AnalyticsEvent.create(
            event_type=EventType.PAGE_VIEW,
            utm_source="google",
            utm_medium="cpc",
            utm_campaign="spring_sale",
        )
        assert event.utm_source == "google"
        assert event.utm_medium == "cpc"
        assert event.utm_campaign == "spring_sale"

    def test_to_dict(self):
        """辞書変換テスト"""
        event = AnalyticsEvent.create(
            event_type=EventType.PURCHASE,
            user_id="user_123",
            revenue=29.99,
        )
        data = event.to_dict()
        assert data["event_type"] == "purchase"
        assert data["user_id"] == "user_123"
        assert data["revenue"] == 29.99


class TestConversionGoal:
    """ConversionGoalモデルのテスト"""

    def test_create_goal(self):
        """ゴール作成テスト"""
        goal = ConversionGoal(
            id="goal_test",
            name="月間売上目標",
            target_value=10000.0,
            target_count=100,
        )
        assert goal.id == "goal_test"
        assert goal.name == "月間売上目標"
        assert goal.target_value == 10000.0

    def test_value_progress(self):
        """目標値達成率テスト"""
        goal = ConversionGoal(
            id="goal_1",
            name="売上目標",
            target_value=10000.0,
        )
        goal.current_value = 5000.0
        assert goal.value_progress == 50.0

    def test_count_progress(self):
        """目標件数達成率テスト"""
        goal = ConversionGoal(
            id="goal_1",
            name="件数目標",
            target_count=100,
        )
        goal.current_count = 75
        assert goal.count_progress == 75.0

    def test_progress_capped_at_100(self):
        """達成率100%上限テスト"""
        goal = ConversionGoal(
            id="goal_1",
            name="テスト",
            target_value=100.0,
            target_count=10,
        )
        goal.current_value = 150.0
        goal.current_count = 15
        assert goal.value_progress == 100.0
        assert goal.count_progress == 100.0


# ==================== マネージャーテスト ====================


class TestABTestManager:
    """ABTestManagerのテスト"""

    @pytest.fixture
    def manager(self):
        """新しいマネージャーインスタンスを作成"""
        return ABTestManager()

    def test_create_test(self, manager):
        """テスト作成テスト"""
        test = manager.create_test(
            name="価格テスト",
            description="価格表示のA/Bテスト",
        )
        assert test.id in manager._tests
        assert test.name == "価格テスト"

    def test_get_test(self, manager):
        """テスト取得テスト"""
        test = manager.create_test(name="テスト")
        retrieved = manager.get_test(test.id)
        assert retrieved == test

    def test_get_test_not_found(self, manager):
        """存在しないテスト取得テスト"""
        result = manager.get_test("nonexistent")
        assert result is None

    def test_list_tests(self, manager):
        """テスト一覧取得テスト"""
        manager.create_test(name="テスト1")
        manager.create_test(name="テスト2")
        tests = manager.list_tests()
        assert len(tests) == 2

    def test_list_tests_by_status(self, manager):
        """ステータスでフィルタしたテスト一覧テスト"""
        test1 = manager.create_test(name="テスト1")
        test2 = manager.create_test(name="テスト2")

        # テスト2を開始
        manager.add_variant(test2.id, name="A", weight=50.0)
        manager.add_variant(test2.id, name="B", weight=50.0)
        manager.start_test(test2.id)

        running = manager.list_tests(status=ABTestStatus.RUNNING)
        draft = manager.list_tests(status=ABTestStatus.DRAFT)

        assert len(running) == 1
        assert len(draft) == 1

    def test_add_variant(self, manager):
        """バリアント追加テスト"""
        test = manager.create_test(name="テスト")
        variant = manager.add_variant(
            test_id=test.id,
            name="Control",
            weight=50.0,
            config={"color": "blue"},
        )
        assert variant is not None
        assert variant.name == "Control"
        assert variant.config["color"] == "blue"

    def test_add_variant_to_nonexistent_test(self, manager):
        """存在しないテストへのバリアント追加テスト"""
        result = manager.add_variant(test_id="nonexistent", name="A")
        assert result is None

    def test_add_variant_to_running_test(self, manager):
        """実行中テストへのバリアント追加エラーテスト"""
        test = manager.create_test(name="テスト")
        manager.add_variant(test.id, name="A", weight=50.0)
        manager.add_variant(test.id, name="B", weight=50.0)
        manager.start_test(test.id)

        with pytest.raises(ValueError):
            manager.add_variant(test.id, name="C")

    def test_start_test(self, manager):
        """テスト開始テスト"""
        test = manager.create_test(name="テスト")
        manager.add_variant(test.id, name="A", weight=50.0)
        manager.add_variant(test.id, name="B", weight=50.0)

        result = manager.start_test(test.id)
        assert result is True
        assert test.status == ABTestStatus.RUNNING

    def test_pause_resume_complete_test(self, manager):
        """一時停止・再開・完了テスト"""
        test = manager.create_test(name="テスト")
        manager.add_variant(test.id, name="A", weight=50.0)
        manager.add_variant(test.id, name="B", weight=50.0)
        manager.start_test(test.id)

        assert manager.pause_test(test.id)
        assert test.status == ABTestStatus.PAUSED

        assert manager.resume_test(test.id)
        assert test.status == ABTestStatus.RUNNING

        assert manager.complete_test(test.id)
        assert test.status == ABTestStatus.COMPLETED

    def test_assign_variant(self, manager):
        """バリアント割り当てテスト"""
        test = manager.create_test(name="テスト")
        manager.add_variant(test.id, name="A", weight=50.0)
        manager.add_variant(test.id, name="B", weight=50.0)
        manager.start_test(test.id)

        assignment = manager.assign_variant(test.id, user_id="user_123")
        assert assignment is not None
        assert assignment.user_id == "user_123"
        assert assignment.variant_id in [v.id for v in test.variants]

    def test_assign_variant_consistent(self, manager):
        """同一ユーザーへの一貫した割り当てテスト"""
        test = manager.create_test(name="テスト")
        manager.add_variant(test.id, name="A", weight=50.0)
        manager.add_variant(test.id, name="B", weight=50.0)
        manager.start_test(test.id)

        assignment1 = manager.assign_variant(test.id, user_id="user_123")
        assignment2 = manager.assign_variant(test.id, user_id="user_123")

        assert assignment1.variant_id == assignment2.variant_id

    def test_assign_variant_force(self, manager):
        """強制バリアント割り当てテスト"""
        test = manager.create_test(name="テスト")
        v1 = manager.add_variant(test.id, name="A", weight=50.0)
        manager.add_variant(test.id, name="B", weight=50.0)
        manager.start_test(test.id)

        assignment = manager.assign_variant(
            test.id,
            user_id="user_123",
            force_variant_id=v1.id,
        )
        assert assignment.variant_id == v1.id

    def test_record_conversion(self, manager):
        """コンバージョン記録テスト"""
        test = manager.create_test(name="テスト")
        manager.add_variant(test.id, name="A", weight=50.0)
        manager.add_variant(test.id, name="B", weight=50.0)
        manager.start_test(test.id)

        assignment = manager.assign_variant(test.id, user_id="user_123")
        result = manager.record_conversion(test.id, "user_123", revenue=29.99)

        assert result is True
        assert assignment.converted is True
        assert assignment.revenue == 29.99

    def test_get_test_results(self, manager):
        """テスト結果取得テスト"""
        test = manager.create_test(name="テスト")
        manager.add_variant(test.id, name="A", weight=50.0)
        manager.add_variant(test.id, name="B", weight=50.0)
        manager.start_test(test.id)

        results = manager.get_test_results(test.id)
        assert results is not None
        assert "has_sufficient_sample" in results
        assert "variants" in results

    def test_delete_test(self, manager):
        """テスト削除テスト"""
        test = manager.create_test(name="テスト")
        result = manager.delete_test(test.id)
        assert result is True
        assert manager.get_test(test.id) is None


class TestAnalyticsTracker:
    """AnalyticsTrackerのテスト"""

    @pytest.fixture
    def tracker(self):
        """新しいトラッカーインスタンスを作成"""
        return AnalyticsTracker()

    def test_track_event(self, tracker):
        """イベント記録テスト"""
        event = tracker.track_event(
            event_type=EventType.PAGE_VIEW,
            user_id="user_123",
            session_id="session_456",
        )
        assert event.id.startswith("evt_")
        assert len(tracker._events) == 1

    def test_track_event_with_revenue(self, tracker):
        """収益付きイベント記録テスト"""
        event = tracker.track_event(
            event_type=EventType.PURCHASE,
            user_id="user_123",
            revenue=99.99,
        )
        assert event.revenue == 99.99

    def test_get_events(self, tracker):
        """イベント取得テスト"""
        tracker.track_event(EventType.PAGE_VIEW, user_id="user_1")
        tracker.track_event(EventType.PAGE_VIEW, user_id="user_2")
        tracker.track_event(EventType.PURCHASE, user_id="user_1")

        all_events = tracker.get_events()
        assert len(all_events) == 3

        user1_events = tracker.get_events(user_id="user_1")
        assert len(user1_events) == 2

        purchases = tracker.get_events(event_type=EventType.PURCHASE)
        assert len(purchases) == 1

    def test_get_daily_stats(self, tracker):
        """日次統計取得テスト"""
        tracker.track_event(EventType.PAGE_VIEW, user_id="user_1")
        tracker.track_event(EventType.PAGE_VIEW, user_id="user_2")

        stats = tracker.get_daily_stats()
        assert len(stats) > 0

    def test_get_summary(self, tracker):
        """サマリー統計取得テスト"""
        tracker.track_event(EventType.PAGE_VIEW, user_id="user_1")
        tracker.track_event(EventType.PURCHASE, user_id="user_1", revenue=29.99)

        summary = tracker.get_summary(days=30)
        assert summary["total_events"] == 2
        assert summary["unique_users"] == 1
        assert summary["total_revenue"] == 29.99

    def test_create_goal(self, tracker):
        """ゴール作成テスト"""
        goal = tracker.create_goal(
            name="月間売上目標",
            target_value=10000.0,
            target_count=100,
        )
        assert goal.id.startswith("goal_")
        assert goal.name == "月間売上目標"

    def test_goal_updated_on_event(self, tracker):
        """イベント時のゴール更新テスト"""
        goal = tracker.create_goal(
            name="購入目標",
            event_type=EventType.PURCHASE,
            target_count=10,
        )

        tracker.track_event(EventType.PURCHASE, user_id="user_1", revenue=29.99)
        assert goal.current_count == 1
        assert goal.current_value == 29.99

    def test_get_funnel(self, tracker):
        """ファネル分析テスト"""
        # ユーザー1: ページビュー → サインアップ → 購入
        tracker.track_event(EventType.PAGE_VIEW, user_id="user_1")
        tracker.track_event(EventType.SIGN_UP, user_id="user_1")
        tracker.track_event(EventType.PURCHASE, user_id="user_1")

        # ユーザー2: ページビュー → サインアップ（購入なし）
        tracker.track_event(EventType.PAGE_VIEW, user_id="user_2")
        tracker.track_event(EventType.SIGN_UP, user_id="user_2")

        # ユーザー3: ページビューのみ
        tracker.track_event(EventType.PAGE_VIEW, user_id="user_3")

        funnel = tracker.get_funnel(
            steps=[EventType.PAGE_VIEW, EventType.SIGN_UP, EventType.PURCHASE]
        )

        assert len(funnel["steps"]) == 3
        assert funnel["steps"][0]["user_count"] == 3  # ページビュー
        assert funnel["steps"][1]["user_count"] == 2  # サインアップ
        assert funnel["steps"][2]["user_count"] == 1  # 購入

    def test_get_retention(self, tracker):
        """リテンション分析テスト"""
        today = datetime.utcnow()

        # 今日イベントがあったユーザー
        event1 = tracker.track_event(EventType.PAGE_VIEW, user_id="user_1")
        event1.timestamp = today

        retention = tracker.get_retention(cohort_date=today, periods=3)
        assert retention["cohort_size"] >= 0

    def test_delete_events(self, tracker):
        """イベント削除テスト"""
        tracker.track_event(EventType.PAGE_VIEW, user_id="user_1")
        tracker.track_event(EventType.PAGE_VIEW, user_id="user_2")

        deleted = tracker.delete_events(user_id="user_1")
        assert deleted == 1
        assert len(tracker._events) == 1


# ==================== APIエンドポイントテスト ====================


class TestAnalyticsAPI:
    """分析APIエンドポイントのテスト"""

    def test_list_event_types(self):
        """イベントタイプ一覧取得テスト"""
        response = client.get("/api/v1/analytics/event-types")
        assert response.status_code == 200
        data = response.json()
        assert "event_types" in data
        assert len(data["event_types"]) > 0

    def test_track_event(self):
        """イベント記録APIテスト"""
        response = client.post(
            "/api/v1/analytics/events",
            json={
                "event_type": "page_view",
                "user_id": "test_user_123",
                "session_id": "session_456",
                "event_name": "home_page",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["event_type"] == "page_view"
        assert data["user_id"] == "test_user_123"

    def test_list_events(self):
        """イベント一覧取得APIテスト"""
        response = client.get("/api/v1/analytics/events")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_daily_stats(self):
        """日次統計取得APIテスト"""
        response = client.get("/api/v1/analytics/stats/daily")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_summary(self):
        """サマリー統計取得APIテスト"""
        response = client.get("/api/v1/analytics/stats/summary?days=7")
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert data["period_days"] == 7

    def test_analyze_funnel(self):
        """ファネル分析APIテスト"""
        response = client.post(
            "/api/v1/analytics/funnel",
            json={
                "steps": ["page_view", "sign_up", "purchase"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data
        assert "overall_conversion" in data

    def test_analyze_retention(self):
        """リテンション分析APIテスト"""
        response = client.post(
            "/api/v1/analytics/retention",
            json={
                "cohort_date": datetime.utcnow().isoformat(),
                "periods": 7,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "cohort_date" in data
        assert "retention" in data


class TestABTestAPI:
    """A/Bテストエンドポイントのテスト"""

    def test_create_ab_test(self):
        """A/Bテスト作成APIテスト"""
        response = client.post(
            "/api/v1/analytics/ab-tests",
            json={
                "name": "価格テスト",
                "description": "価格表示のA/Bテスト",
                "goal_type": "subscription",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "価格テスト"
        assert data["status"] == "draft"

    def test_create_ab_test_with_variants(self):
        """バリアント付きA/Bテスト作成APIテスト"""
        response = client.post(
            "/api/v1/analytics/ab-tests",
            json={
                "name": "CTA色テスト",
                "variants": [
                    {"name": "青", "weight": 50.0, "config": {"color": "blue"}},
                    {"name": "緑", "weight": 50.0, "config": {"color": "green"}},
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["variants"]) == 2

    def test_list_ab_tests(self):
        """A/Bテスト一覧取得APIテスト"""
        response = client.get("/api/v1/analytics/ab-tests")
        assert response.status_code == 200
        data = response.json()
        assert "tests" in data
        assert "total" in data

    def test_add_variant_to_test(self):
        """バリアント追加APIテスト"""
        # テスト作成
        create_response = client.post(
            "/api/v1/analytics/ab-tests",
            json={"name": "テスト"},
        )
        test_id = create_response.json()["id"]

        # バリアント追加
        response = client.post(
            f"/api/v1/analytics/ab-tests/{test_id}/variants",
            json={"name": "Control", "weight": 50.0},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Control"

    def test_start_test(self):
        """テスト開始APIテスト"""
        # テスト作成
        create_response = client.post(
            "/api/v1/analytics/ab-tests",
            json={
                "name": "テスト",
                "variants": [
                    {"name": "A", "weight": 50.0},
                    {"name": "B", "weight": 50.0},
                ],
            },
        )
        test_id = create_response.json()["id"]

        # 開始
        response = client.post(f"/api/v1/analytics/ab-tests/{test_id}/start")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_assign_variant(self):
        """バリアント割り当てAPIテスト"""
        # テスト作成・開始
        create_response = client.post(
            "/api/v1/analytics/ab-tests",
            json={
                "name": "テスト",
                "variants": [
                    {"name": "A", "weight": 50.0},
                    {"name": "B", "weight": 50.0},
                ],
            },
        )
        test_id = create_response.json()["id"]
        client.post(f"/api/v1/analytics/ab-tests/{test_id}/start")

        # 割り当て
        response = client.post(
            f"/api/v1/analytics/ab-tests/{test_id}/assign?user_id=api_test_user"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "api_test_user"
        assert "variant_id" in data

    def test_record_conversion(self):
        """コンバージョン記録APIテスト"""
        # テスト作成・開始
        create_response = client.post(
            "/api/v1/analytics/ab-tests",
            json={
                "name": "テスト",
                "variants": [
                    {"name": "A", "weight": 50.0},
                    {"name": "B", "weight": 50.0},
                ],
            },
        )
        test_id = create_response.json()["id"]
        client.post(f"/api/v1/analytics/ab-tests/{test_id}/start")

        # 割り当て
        client.post(
            f"/api/v1/analytics/ab-tests/{test_id}/assign?user_id=conv_test_user"
        )

        # コンバージョン記録
        response = client.post(
            f"/api/v1/analytics/ab-tests/{test_id}/conversion",
            json={"user_id": "conv_test_user", "revenue": 29.99},
        )
        assert response.status_code == 200

    def test_get_test_results(self):
        """テスト結果取得APIテスト"""
        # テスト作成・開始
        create_response = client.post(
            "/api/v1/analytics/ab-tests",
            json={
                "name": "テスト",
                "variants": [
                    {"name": "A", "weight": 50.0},
                    {"name": "B", "weight": 50.0},
                ],
            },
        )
        test_id = create_response.json()["id"]
        client.post(f"/api/v1/analytics/ab-tests/{test_id}/start")

        # 結果取得
        response = client.get(f"/api/v1/analytics/ab-tests/{test_id}/results")
        assert response.status_code == 200
        data = response.json()
        assert "has_sufficient_sample" in data


class TestGoalAPI:
    """ゴールAPIエンドポイントのテスト"""

    def test_create_goal(self):
        """ゴール作成APIテスト"""
        response = client.post(
            "/api/v1/analytics/goals",
            json={
                "name": "月間売上目標",
                "goal_type": "subscription",
                "event_type": "subscription_start",
                "target_value": 10000.0,
                "target_count": 100,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "月間売上目標"
        assert data["target_value"] == 10000.0

    def test_list_goals(self):
        """ゴール一覧取得APIテスト"""
        response = client.get("/api/v1/analytics/goals")
        assert response.status_code == 200
        data = response.json()
        assert "goals" in data
        assert "total" in data
