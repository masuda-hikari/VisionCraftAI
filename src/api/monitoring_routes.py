# -*- coding: utf-8 -*-
"""
VisionCraftAI - モニタリングAPIルーター

本番環境向けのヘルスチェック・メトリクス・モニタリングエンドポイント。
収益監視と安定運用に必須。
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from src.utils.config import Config
from src.utils.monitoring import (
    HealthChecker,
    HealthStatus,
    MetricsCollector,
    get_health_checker,
    get_metrics_collector,
)

logger = logging.getLogger(__name__)

# ルーター初期化
router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# ======================
# スキーマ定義
# ======================

class ComponentHealthSchema(BaseModel):
    """コンポーネントヘルス状態"""
    name: str = Field(..., description="コンポーネント名")
    status: str = Field(..., description="ステータス (healthy/degraded/unhealthy)")
    message: str = Field("", description="メッセージ")
    latency_ms: Optional[float] = Field(None, description="レイテンシ (ms)")
    details: dict = Field(default_factory=dict, description="詳細情報")
    checked_at: str = Field(..., description="チェック日時")


class SystemHealthSchema(BaseModel):
    """システム全体ヘルス状態"""
    status: str = Field(..., description="全体ステータス")
    version: str = Field(..., description="バージョン")
    environment: str = Field(..., description="環境")
    uptime_seconds: float = Field(..., description="稼働時間 (秒)")
    components: list[ComponentHealthSchema] = Field(..., description="コンポーネント状態")
    system_info: dict = Field(..., description="システム情報")
    checked_at: str = Field(..., description="チェック日時")


class LivenessSchema(BaseModel):
    """Liveness probe応答"""
    status: str = Field(..., description="ステータス")
    timestamp: str = Field(..., description="タイムスタンプ")


class ReadinessSchema(BaseModel):
    """Readiness probe応答"""
    status: str = Field(..., description="ステータス")
    ready: bool = Field(..., description="準備完了フラグ")
    checks: dict = Field(..., description="チェック結果")
    timestamp: str = Field(..., description="タイムスタンプ")


class MetricsSchema(BaseModel):
    """メトリクス応答"""
    counters: dict = Field(..., description="カウンター")
    gauges: dict = Field(..., description="ゲージ")
    histograms: dict = Field(..., description="ヒストグラム")
    timestamp: str = Field(..., description="タイムスタンプ")


# ======================
# ヘルスチェック関数
# ======================

async def check_database() -> dict:
    """データベース接続チェック（将来のDB実装用）"""
    # 現在はメモリストレージのため常に正常
    return {
        "status": HealthStatus.HEALTHY,
        "message": "メモリストレージ正常",
        "details": {"type": "memory"},
    }


async def check_gemini_api() -> dict:
    """Gemini API接続チェック"""
    try:
        from src.generator.gemini_client import GeminiClient
        from src.utils.config import Config

        config = Config.from_env()
        client = GeminiClient(config)
        connected, message = client.check_connection()

        if connected:
            return {
                "status": HealthStatus.HEALTHY,
                "message": message,
            }
        else:
            return {
                "status": HealthStatus.DEGRADED,
                "message": f"API接続不可: {message}",
            }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": str(e),
        }


async def check_stripe() -> dict:
    """Stripe接続チェック"""
    try:
        from src.api.payment.stripe_client import StripeClient

        client = StripeClient()
        if client._stripe_secret_key:
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Stripe設定済み",
                "details": {"test_mode": client._test_mode},
            }
        else:
            return {
                "status": HealthStatus.DEGRADED,
                "message": "Stripe未設定",
            }
    except Exception as e:
        return {
            "status": HealthStatus.DEGRADED,
            "message": f"Stripe確認エラー: {str(e)}",
        }


async def check_disk_space() -> dict:
    """ディスク空き容量チェック"""
    try:
        import psutil
        disk = psutil.disk_usage("/")
        percent_used = (disk.used / disk.total) * 100

        if percent_used > 95:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"ディスク使用率: {percent_used:.1f}%（危険）",
                "details": {"percent_used": percent_used},
            }
        elif percent_used > 85:
            return {
                "status": HealthStatus.DEGRADED,
                "message": f"ディスク使用率: {percent_used:.1f}%（警告）",
                "details": {"percent_used": percent_used},
            }
        else:
            return {
                "status": HealthStatus.HEALTHY,
                "message": f"ディスク使用率: {percent_used:.1f}%",
                "details": {"percent_used": percent_used},
            }
    except ImportError:
        return {
            "status": HealthStatus.HEALTHY,
            "message": "ディスクチェックスキップ（psutil未インストール）",
        }


async def check_memory() -> dict:
    """メモリ使用量チェック"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        percent_used = memory.percent

        if percent_used > 95:
            return {
                "status": HealthStatus.UNHEALTHY,
                "message": f"メモリ使用率: {percent_used:.1f}%（危険）",
                "details": {"percent_used": percent_used},
            }
        elif percent_used > 85:
            return {
                "status": HealthStatus.DEGRADED,
                "message": f"メモリ使用率: {percent_used:.1f}%（警告）",
                "details": {"percent_used": percent_used},
            }
        else:
            return {
                "status": HealthStatus.HEALTHY,
                "message": f"メモリ使用率: {percent_used:.1f}%",
                "details": {"percent_used": percent_used},
            }
    except ImportError:
        return {
            "status": HealthStatus.HEALTHY,
            "message": "メモリチェックスキップ（psutil未インストール）",
        }


# ヘルスチェッカー初期化
def get_initialized_health_checker() -> HealthChecker:
    """初期化済みヘルスチェッカーを取得"""
    config = Config.from_env()
    checker = get_health_checker(version="0.1.0", environment=config.environment)

    # チェック関数を登録（初回のみ）
    if not checker._checks:
        checker.register_check("database", check_database)
        checker.register_check("gemini_api", check_gemini_api)
        checker.register_check("stripe", check_stripe)
        checker.register_check("disk", check_disk_space)
        checker.register_check("memory", check_memory)

    return checker


# ======================
# Kubernetes プローブ
# ======================

@router.get(
    "/liveness",
    response_model=LivenessSchema,
    summary="Liveness Probe",
    description="Kubernetesのliveness probe用エンドポイント。プロセスが生存しているか確認。",
)
async def liveness_probe() -> LivenessSchema:
    """
    Liveness Probe

    プロセスが正常に動作しているかを確認します。
    このチェックが失敗すると、コンテナが再起動されます。
    """
    return LivenessSchema(
        status="alive",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/readiness",
    response_model=ReadinessSchema,
    summary="Readiness Probe",
    description="Kubernetesのreadiness probe用エンドポイント。トラフィックを受け入れ可能か確認。",
)
async def readiness_probe() -> ReadinessSchema:
    """
    Readiness Probe

    サービスがリクエストを処理可能な状態かを確認します。
    このチェックが失敗すると、サービスはロードバランサーから除外されます。
    """
    checks = {}

    # 基本チェック
    try:
        # 設定読み込み確認
        config = Config.from_env()
        checks["config"] = True
    except Exception:
        checks["config"] = False

    # 全チェックがパスしているか
    ready = all(checks.values())

    return ReadinessSchema(
        status="ready" if ready else "not_ready",
        ready=ready,
        checks=checks,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ======================
# 詳細ヘルスチェック
# ======================

@router.get(
    "/health",
    response_model=SystemHealthSchema,
    summary="詳細ヘルスチェック",
    description="すべてのコンポーネントの詳細なヘルスチェックを実行します。",
)
async def detailed_health_check(
    include_system_info: bool = Query(True, description="システム情報を含めるか"),
) -> SystemHealthSchema:
    """
    詳細ヘルスチェック

    - 全コンポーネントの状態を確認
    - 問題があれば詳細情報を提供
    - 本番環境の監視・アラートに使用
    """
    checker = get_initialized_health_checker()
    health = await checker.check_all()
    data = health.to_dict()

    if not include_system_info:
        data["system_info"] = {}

    return SystemHealthSchema(**data)


# ======================
# メトリクス
# ======================

@router.get(
    "/metrics",
    response_model=MetricsSchema,
    summary="アプリケーションメトリクス",
    description="収集されたアプリケーションメトリクスを取得します。",
)
async def get_metrics() -> MetricsSchema:
    """
    アプリケーションメトリクス

    - カウンター（リクエスト数、エラー数など）
    - ゲージ（現在値）
    - ヒストグラム（レイテンシ分布など）
    """
    collector = get_metrics_collector()
    metrics = await collector.get_metrics()

    return MetricsSchema(
        **metrics,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/metrics/prometheus",
    response_class=PlainTextResponse,
    summary="Prometheusメトリクス",
    description="Prometheus形式でメトリクスをエクスポートします。",
)
async def get_prometheus_metrics() -> str:
    """
    Prometheusメトリクス

    Prometheus形式でメトリクスを出力します。
    Prometheusサーバーからのスクレイピングに使用。
    """
    collector = get_metrics_collector()
    return collector.to_prometheus_format()


# ======================
# メトリクス記録ヘルパー
# ======================

async def record_request_metrics(
    endpoint: str,
    method: str,
    status_code: int,
    latency_ms: float,
    api_key_tier: Optional[str] = None,
) -> None:
    """リクエストメトリクスを記録"""
    collector = get_metrics_collector()

    # リクエストカウント
    await collector.increment(
        "http_requests_total",
        labels={
            "endpoint": endpoint,
            "method": method,
            "status": str(status_code),
        },
    )

    # レイテンシ
    await collector.histogram(
        "http_request_duration_ms",
        latency_ms,
        labels={"endpoint": endpoint, "method": method},
    )

    # プラン別カウント
    if api_key_tier:
        await collector.increment(
            "api_requests_by_tier",
            labels={"tier": api_key_tier},
        )


async def record_generation_metrics(
    success: bool,
    latency_ms: float,
    tier: str,
) -> None:
    """画像生成メトリクスを記録"""
    collector = get_metrics_collector()

    status = "success" if success else "failure"
    await collector.increment(
        "image_generations_total",
        labels={"status": status, "tier": tier},
    )

    if success:
        await collector.histogram(
            "image_generation_duration_ms",
            latency_ms,
            labels={"tier": tier},
        )


async def record_payment_metrics(
    event_type: str,
    amount_usd: float,
    plan: Optional[str] = None,
) -> None:
    """決済メトリクスを記録"""
    collector = get_metrics_collector()

    await collector.increment(
        "payment_events_total",
        labels={"event_type": event_type},
    )

    if amount_usd > 0:
        await collector.increment(
            "revenue_usd_total",
            int(amount_usd * 100),  # セント単位
        )

        if plan:
            await collector.increment(
                "revenue_by_plan_usd",
                int(amount_usd * 100),
                labels={"plan": plan},
            )
