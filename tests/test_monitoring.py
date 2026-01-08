# -*- coding: utf-8 -*-
"""
VisionCraftAI - モニタリングモジュールテスト

ヘルスチェック、メトリクス収集、構造化ロギングのテスト。
"""

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient

from src.api.app import app
from src.utils.monitoring import (
    HealthChecker,
    HealthStatus,
    ComponentHealth,
    SystemHealth,
    MetricsCollector,
    StructuredLogger,
    get_health_checker,
    get_metrics_collector,
    create_logger,
)


client = TestClient(app)


# ======================
# HealthChecker テスト
# ======================

class TestHealthChecker:
    """HealthChecker クラスのテスト"""

    def test_init(self):
        """初期化テスト"""
        checker = HealthChecker(version="1.0.0", environment="test")
        assert checker.version == "1.0.0"
        assert checker.environment == "test"
        assert checker._checks == {}

    def test_register_check(self):
        """チェック関数登録テスト"""
        checker = HealthChecker()

        def dummy_check():
            return True

        checker.register_check("test", dummy_check)
        assert "test" in checker._checks

    @pytest.mark.asyncio
    async def test_run_check_success(self):
        """チェック実行成功テスト"""
        checker = HealthChecker()

        async def success_check():
            return {"status": HealthStatus.HEALTHY, "message": "OK"}

        result = await checker._run_check("test", success_check)
        assert result.name == "test"
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "OK"
        assert result.latency_ms is not None

    @pytest.mark.asyncio
    async def test_run_check_failure(self):
        """チェック実行失敗テスト"""
        checker = HealthChecker()

        async def failure_check():
            raise ValueError("エラー発生")

        result = await checker._run_check("test", failure_check)
        assert result.name == "test"
        assert result.status == HealthStatus.UNHEALTHY
        assert "エラー発生" in result.message

    @pytest.mark.asyncio
    async def test_check_all(self):
        """全チェック実行テスト"""
        checker = HealthChecker(version="1.0.0", environment="test")

        async def healthy_check():
            return {"status": HealthStatus.HEALTHY, "message": "OK"}

        async def degraded_check():
            return {"status": HealthStatus.DEGRADED, "message": "Warning"}

        checker.register_check("healthy", healthy_check)
        checker.register_check("degraded", degraded_check)

        health = await checker.check_all()
        assert health.status == HealthStatus.DEGRADED  # 1つでもdegradedがあれば全体もdegraded
        assert len(health.components) == 2
        assert health.version == "1.0.0"
        assert health.environment == "test"

    @pytest.mark.asyncio
    async def test_check_all_unhealthy(self):
        """全チェック実行（異常あり）テスト"""
        checker = HealthChecker()

        async def unhealthy_check():
            return {"status": HealthStatus.UNHEALTHY, "message": "Critical"}

        checker.register_check("critical", unhealthy_check)

        health = await checker.check_all()
        assert health.status == HealthStatus.UNHEALTHY

    def test_get_system_info(self):
        """システム情報取得テスト"""
        checker = HealthChecker()
        info = checker._get_system_info()

        assert "python_version" in info
        assert "platform" in info
        assert "cpu_count" in info


class TestSystemHealth:
    """SystemHealth クラスのテスト"""

    def test_to_dict(self):
        """辞書変換テスト"""
        component = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
            latency_ms=10.5,
        )
        health = SystemHealth(
            status=HealthStatus.HEALTHY,
            version="1.0.0",
            environment="test",
            uptime_seconds=100.0,
            components=[component],
            system_info={"python_version": "3.12"},
        )

        data = health.to_dict()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert len(data["components"]) == 1
        assert data["components"][0]["latency_ms"] == 10.5


# ======================
# MetricsCollector テスト
# ======================

class TestMetricsCollector:
    """MetricsCollector クラスのテスト"""

    @pytest.mark.asyncio
    async def test_increment(self):
        """カウンターインクリメントテスト"""
        collector = MetricsCollector()
        await collector.increment("test_counter")
        await collector.increment("test_counter", 5)

        metrics = await collector.get_metrics()
        assert metrics["counters"]["test_counter"] == 6

    @pytest.mark.asyncio
    async def test_increment_with_labels(self):
        """ラベル付きカウンターテスト"""
        collector = MetricsCollector()
        await collector.increment("requests", labels={"endpoint": "/api"})
        await collector.increment("requests", labels={"endpoint": "/api"})
        await collector.increment("requests", labels={"endpoint": "/health"})

        metrics = await collector.get_metrics()
        assert metrics["counters"]['requests{endpoint="/api"}'] == 2
        assert metrics["counters"]['requests{endpoint="/health"}'] == 1

    @pytest.mark.asyncio
    async def test_gauge(self):
        """ゲージテスト"""
        collector = MetricsCollector()
        await collector.gauge("memory_usage", 75.5)
        await collector.gauge("memory_usage", 80.0)

        metrics = await collector.get_metrics()
        assert metrics["gauges"]["memory_usage"] == 80.0

    @pytest.mark.asyncio
    async def test_histogram(self):
        """ヒストグラムテスト"""
        collector = MetricsCollector()
        for i in range(100):
            await collector.histogram("latency", float(i))

        metrics = await collector.get_metrics()
        hist = metrics["histograms"]["latency"]

        assert hist["count"] == 100
        assert hist["min"] == 0.0
        assert hist["max"] == 99.0
        assert hist["avg"] == 49.5
        assert hist["p50"] is not None
        assert hist["p95"] is not None

    @pytest.mark.asyncio
    async def test_prometheus_format(self):
        """Prometheus形式エクスポートテスト"""
        collector = MetricsCollector()
        await collector.increment("http_requests_total")
        await collector.gauge("active_connections", 10)

        output = collector.to_prometheus_format()
        assert "http_requests_total" in output
        assert "active_connections" in output


# ======================
# StructuredLogger テスト
# ======================

class TestStructuredLogger:
    """StructuredLogger クラスのテスト"""

    def test_init(self):
        """初期化テスト"""
        logger = StructuredLogger("test", "DEBUG")
        assert logger.logger.name == "test"

    def test_set_context(self):
        """コンテキスト設定テスト"""
        logger = StructuredLogger("test")
        logger.set_context(user_id="123", request_id="abc")

        assert logger._extra_fields["user_id"] == "123"
        assert logger._extra_fields["request_id"] == "abc"

    def test_format_message(self):
        """メッセージフォーマットテスト"""
        logger = StructuredLogger("test")
        logger.set_context(service="api")

        message = logger._format_message("INFO", "テストメッセージ", extra="data")

        import json
        data = json.loads(message)

        assert data["level"] == "INFO"
        assert data["message"] == "テストメッセージ"
        assert data["service"] == "api"
        assert data["extra"] == "data"
        assert "timestamp" in data


# ======================
# シングルトンテスト
# ======================

class TestSingletons:
    """シングルトン関数のテスト"""

    def test_get_health_checker(self):
        """ヘルスチェッカーシングルトンテスト"""
        checker1 = get_health_checker()
        checker2 = get_health_checker()
        # 同じインスタンスを返す
        assert checker1 is checker2

    def test_get_metrics_collector(self):
        """メトリクスコレクターシングルトンテスト"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        assert collector1 is collector2

    def test_create_logger(self):
        """ロガー作成テスト"""
        logger1 = create_logger("test1")
        logger2 = create_logger("test2")
        # 異なるインスタンス
        assert logger1 is not logger2
        assert logger1.logger.name == "test1"
        assert logger2.logger.name == "test2"


# ======================
# APIエンドポイントテスト
# ======================

class TestMonitoringEndpoints:
    """モニタリングAPIエンドポイントのテスト"""

    def test_liveness_probe(self):
        """Liveness probeテスト"""
        response = client.get("/api/v1/monitoring/liveness")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_readiness_probe(self):
        """Readiness probeテスト"""
        response = client.get("/api/v1/monitoring/readiness")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "ready" in data
        assert "checks" in data
        assert "timestamp" in data

    def test_detailed_health_check(self):
        """詳細ヘルスチェックテスト"""
        response = client.get("/api/v1/monitoring/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "uptime_seconds" in data
        assert "components" in data
        assert "system_info" in data

    def test_detailed_health_check_no_system_info(self):
        """システム情報なしヘルスチェックテスト"""
        response = client.get("/api/v1/monitoring/health?include_system_info=false")
        assert response.status_code == 200

        data = response.json()
        assert data["system_info"] == {}

    def test_get_metrics(self):
        """メトリクス取得テスト"""
        response = client.get("/api/v1/monitoring/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "counters" in data
        assert "gauges" in data
        assert "histograms" in data
        assert "timestamp" in data

    def test_get_prometheus_metrics(self):
        """Prometheusメトリクス取得テスト"""
        response = client.get("/api/v1/monitoring/metrics/prometheus")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"


# ======================
# 統合テスト
# ======================

class TestMonitoringIntegration:
    """モニタリング統合テスト"""

    @pytest.mark.asyncio
    async def test_health_check_with_multiple_components(self):
        """複数コンポーネントヘルスチェックテスト"""
        checker = HealthChecker(version="1.0.0", environment="test")

        async def db_check():
            return {"status": HealthStatus.HEALTHY, "message": "DB OK"}

        async def cache_check():
            return {"status": HealthStatus.HEALTHY, "message": "Cache OK"}

        async def api_check():
            return {"status": HealthStatus.DEGRADED, "message": "API slow"}

        checker.register_check("database", db_check)
        checker.register_check("cache", cache_check)
        checker.register_check("external_api", api_check)

        health = await checker.check_all()

        assert health.status == HealthStatus.DEGRADED
        assert len(health.components) == 3

        # コンポーネント別ステータス確認
        statuses = {c.name: c.status for c in health.components}
        assert statuses["database"] == HealthStatus.HEALTHY
        assert statuses["cache"] == HealthStatus.HEALTHY
        assert statuses["external_api"] == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_metrics_concurrent_access(self):
        """メトリクス並行アクセステスト"""
        collector = MetricsCollector()

        async def increment_many():
            for _ in range(100):
                await collector.increment("concurrent_counter")

        # 10並列でインクリメント
        await asyncio.gather(*[increment_many() for _ in range(10)])

        metrics = await collector.get_metrics()
        assert metrics["counters"]["concurrent_counter"] == 1000

    def test_full_monitoring_flow(self):
        """完全モニタリングフローテスト"""
        # 1. Liveness check
        liveness = client.get("/api/v1/monitoring/liveness")
        assert liveness.status_code == 200

        # 2. Readiness check
        readiness = client.get("/api/v1/monitoring/readiness")
        assert readiness.status_code == 200

        # 3. Detailed health
        health = client.get("/api/v1/monitoring/health")
        assert health.status_code == 200

        # 4. Metrics
        metrics = client.get("/api/v1/monitoring/metrics")
        assert metrics.status_code == 200

        # 5. Prometheus metrics
        prom = client.get("/api/v1/monitoring/metrics/prometheus")
        assert prom.status_code == 200
