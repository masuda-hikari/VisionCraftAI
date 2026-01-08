# -*- coding: utf-8 -*-
"""
VisionCraftAI - 使用量トラッキングモジュールのテスト
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.utils.usage_tracker import UsageRecord, UsageSummary, UsageTracker


class TestUsageRecord:
    """UsageRecordのテスト"""

    def test_create_record(self):
        """レコード作成"""
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            operation="generate_image",
            prompt_length=100,
            success=True,
            generation_time_ms=500,
            model="gemini-2.0-flash-exp",
            estimated_cost_usd=0.01,
        )

        assert record.operation == "generate_image"
        assert record.success is True
        assert record.estimated_cost_usd == 0.01

    def test_from_dict(self):
        """辞書からの作成"""
        data = {
            "timestamp": "2025-01-01T00:00:00",
            "operation": "generate_image",
            "prompt_length": 50,
            "success": True,
            "generation_time_ms": 300,
            "model": "test-model",
            "error_message": None,
            "estimated_cost_usd": 0.005,
        }

        record = UsageRecord.from_dict(data)
        assert record.prompt_length == 50
        assert record.generation_time_ms == 300


class TestUsageSummary:
    """UsageSummaryのテスト"""

    def test_success_rate(self):
        """成功率計算"""
        summary = UsageSummary(
            period_start="2025-01-01",
            period_end="2025-01-31",
            total_requests=100,
            successful_requests=85,
            failed_requests=15,
            total_generation_time_ms=50000,
            average_generation_time_ms=500.0,
            total_estimated_cost_usd=1.0,
        )

        assert summary.success_rate == 85.0

    def test_success_rate_zero_requests(self):
        """リクエスト0件時の成功率"""
        summary = UsageSummary(
            period_start="2025-01-01",
            period_end="2025-01-31",
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            total_generation_time_ms=0,
            average_generation_time_ms=0.0,
            total_estimated_cost_usd=0.0,
        )

        assert summary.success_rate == 0.0


class TestUsageTracker:
    """UsageTrackerのテスト"""

    @pytest.fixture
    def tracker(self, tmp_path):
        """テスト用トラッカー"""
        storage_path = tmp_path / "usage_data.json"
        return UsageTracker(storage_path=storage_path, auto_save=True)

    def test_record_usage(self, tracker):
        """使用量記録"""
        record = tracker.record(
            operation="generate_image",
            prompt_length=100,
            success=True,
            generation_time_ms=500,
            model="test-model",
        )

        assert record.operation == "generate_image"
        assert record.success is True
        assert record.estimated_cost_usd > 0

    def test_record_failure(self, tracker):
        """失敗時の記録"""
        record = tracker.record(
            operation="generate_image",
            prompt_length=100,
            success=False,
            generation_time_ms=100,
            model="test-model",
            error_message="API Error",
        )

        assert record.success is False
        assert record.error_message == "API Error"
        # 失敗時はコストが低い（入力コストのみ）
        assert record.estimated_cost_usd < 0.01

    def test_get_summary_empty(self, tracker):
        """空の状態でサマリー取得"""
        summary = tracker.get_summary()

        assert summary.total_requests == 0
        assert summary.success_rate == 0.0

    def test_get_summary_with_records(self, tracker):
        """レコードありでサマリー取得"""
        for i in range(5):
            tracker.record(
                operation="generate_image",
                prompt_length=100,
                success=i < 4,  # 4成功、1失敗
                generation_time_ms=500,
                model="test-model",
            )

        summary = tracker.get_summary()

        assert summary.total_requests == 5
        assert summary.successful_requests == 4
        assert summary.failed_requests == 1
        assert summary.success_rate == 80.0

    def test_get_summary_with_days_filter(self, tracker):
        """日数フィルター付きサマリー"""
        # 現在の記録
        tracker.record(
            operation="generate_image",
            prompt_length=100,
            success=True,
            generation_time_ms=500,
            model="test-model",
        )

        # 1日前のサマリーを取得
        summary = tracker.get_summary(days=1)

        assert summary.total_requests == 1

    def test_get_daily_breakdown(self, tracker):
        """日別集計"""
        for _ in range(3):
            tracker.record(
                operation="generate_image",
                prompt_length=100,
                success=True,
                generation_time_ms=500,
                model="test-model",
            )

        breakdown = tracker.get_daily_breakdown(days=7)

        assert len(breakdown) >= 1
        today = datetime.now().strftime("%Y-%m-%d")
        today_data = next((d for d in breakdown if d["date"] == today), None)
        assert today_data is not None
        assert today_data["requests"] == 3

    def test_export_report(self, tracker, tmp_path):
        """レポートエクスポート"""
        tracker.record(
            operation="generate_image",
            prompt_length=100,
            success=True,
            generation_time_ms=500,
            model="test-model",
        )

        output_path = tmp_path / "report.json"
        result_path = tracker.export_report(output_path=output_path, days=30)

        assert result_path.exists()

    def test_clear_old_records(self, tracker):
        """古いレコードのクリア"""
        # 現在のレコードを追加
        tracker.record(
            operation="generate_image",
            prompt_length=100,
            success=True,
            generation_time_ms=500,
            model="test-model",
        )

        # 現在のレコード数を確認
        summary_before = tracker.get_summary()
        assert summary_before.total_requests == 1

        # 90日より古いレコードを削除（今日のレコードは残るはず）
        deleted = tracker.clear_old_records(days=90)

        # 今日のレコードは削除されない
        assert deleted == 0

        # 1日より古いレコードを削除しても、今日のレコードは残る
        deleted = tracker.clear_old_records(days=1)
        summary_after = tracker.get_summary()
        assert summary_after.total_requests == 1  # 今日のレコードは残る

    def test_persistence(self, tmp_path):
        """永続化テスト"""
        storage_path = tmp_path / "usage_data.json"

        # 最初のトラッカーで記録
        tracker1 = UsageTracker(storage_path=storage_path, auto_save=True)
        tracker1.record(
            operation="generate_image",
            prompt_length=100,
            success=True,
            generation_time_ms=500,
            model="test-model",
        )

        # 新しいトラッカーで読み込み
        tracker2 = UsageTracker(storage_path=storage_path, auto_save=True)
        summary = tracker2.get_summary()

        assert summary.total_requests == 1

    def test_cost_estimation(self, tracker):
        """コスト見積もりテスト"""
        # 成功時は画像生成コストが追加される
        record_success = tracker.record(
            operation="generate_image",
            prompt_length=1000,
            success=True,
            generation_time_ms=500,
            model="test-model",
        )

        # 失敗時は入力コストのみ
        record_failure = tracker.record(
            operation="generate_image",
            prompt_length=1000,
            success=False,
            generation_time_ms=100,
            model="test-model",
            error_message="Failed",
        )

        assert record_success.estimated_cost_usd > record_failure.estimated_cost_usd
