# -*- coding: utf-8 -*-
"""
VisionCraftAI - モニタリングモジュール

本番環境向けのヘルスチェック、メトリクス収集、構造化ロギングを提供します。
"""

import asyncio
import inspect
import logging
import os
import platform
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
import json


class HealthStatus(str, Enum):
    """ヘルスチェックステータス"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """コンポーネントのヘルス状態"""
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: Optional[float] = None
    details: dict = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SystemHealth:
    """システム全体のヘルス状態"""
    status: HealthStatus
    version: str
    environment: str
    uptime_seconds: float
    components: list[ComponentHealth]
    system_info: dict
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """辞書に変換"""
        return {
            "status": self.status.value,
            "version": self.version,
            "environment": self.environment,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "latency_ms": round(c.latency_ms, 2) if c.latency_ms else None,
                    "details": c.details,
                    "checked_at": c.checked_at.isoformat(),
                }
                for c in self.components
            ],
            "system_info": self.system_info,
            "checked_at": self.checked_at.isoformat(),
        }


class HealthChecker:
    """ヘルスチェッカー"""

    def __init__(self, version: str = "0.1.0", environment: str = "development"):
        self.version = version
        self.environment = environment
        self._start_time = time.time()
        self._checks: dict[str, Callable] = {}

    def register_check(self, name: str, check_func: Callable) -> None:
        """ヘルスチェック関数を登録"""
        self._checks[name] = check_func

    async def _run_check(self, name: str, check_func: Callable) -> ComponentHealth:
        """個別チェックを実行"""
        start = time.time()
        try:
            if inspect.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()

            latency = (time.time() - start) * 1000

            if isinstance(result, dict):
                status = result.get("status", HealthStatus.HEALTHY)
                message = result.get("message", "OK")
                details = result.get("details", {})
            else:
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "OK" if result else "Check failed"
                details = {}

            return ComponentHealth(
                name=name,
                status=status,
                message=message,
                latency_ms=latency,
                details=details,
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=latency,
            )

    async def check_all(self) -> SystemHealth:
        """すべてのヘルスチェックを実行"""
        components = []

        # 登録されたチェックを並列実行
        if self._checks:
            results = await asyncio.gather(
                *[self._run_check(name, func) for name, func in self._checks.items()],
                return_exceptions=True,
            )
            for result in results:
                if isinstance(result, ComponentHealth):
                    components.append(result)
                elif isinstance(result, Exception):
                    components.append(
                        ComponentHealth(
                            name="unknown",
                            status=HealthStatus.UNHEALTHY,
                            message=str(result),
                        )
                    )

        # 全体ステータスを決定
        if any(c.status == HealthStatus.UNHEALTHY for c in components):
            overall_status = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in components):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return SystemHealth(
            status=overall_status,
            version=self.version,
            environment=self.environment,
            uptime_seconds=time.time() - self._start_time,
            components=components,
            system_info=self._get_system_info(),
        )

    def _get_system_info(self) -> dict:
        """システム情報を取得"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            cpu_percent = psutil.cpu_percent(interval=0.1)
            return {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "cpu_count": os.cpu_count(),
                "cpu_percent": cpu_percent,
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_percent": memory.percent,
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_percent": round((disk.used / disk.total) * 100, 1),
            }
        except ImportError:
            return {
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "cpu_count": os.cpu_count(),
                "note": "psutil not installed - limited system info",
            }


class MetricsCollector:
    """メトリクス収集"""

    def __init__(self):
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._labels: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def increment(self, name: str, value: int = 1, labels: Optional[dict] = None) -> None:
        """カウンターをインクリメント"""
        key = self._make_key(name, labels)
        async with self._lock:
            self._counters[key] = self._counters.get(key, 0) + value
            if labels:
                self._labels[key] = labels

    async def gauge(self, name: str, value: float, labels: Optional[dict] = None) -> None:
        """ゲージを設定"""
        key = self._make_key(name, labels)
        async with self._lock:
            self._gauges[key] = value
            if labels:
                self._labels[key] = labels

    async def histogram(self, name: str, value: float, labels: Optional[dict] = None) -> None:
        """ヒストグラムに値を追加"""
        key = self._make_key(name, labels)
        async with self._lock:
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
            # メモリ制限: 最新1000件のみ保持
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
            if labels:
                self._labels[key] = labels

    def _make_key(self, name: str, labels: Optional[dict] = None) -> str:
        """メトリクスキーを生成"""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    async def get_metrics(self) -> dict:
        """すべてのメトリクスを取得"""
        async with self._lock:
            result = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {},
            }
            for key, values in self._histograms.items():
                if values:
                    sorted_values = sorted(values)
                    result["histograms"][key] = {
                        "count": len(values),
                        "sum": sum(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "p50": sorted_values[len(values) // 2],
                        "p95": sorted_values[int(len(values) * 0.95)] if len(values) >= 20 else None,
                        "p99": sorted_values[int(len(values) * 0.99)] if len(values) >= 100 else None,
                    }
            return result

    def to_prometheus_format(self) -> str:
        """Prometheus形式でメトリクスをエクスポート"""
        lines = []

        # カウンター
        for key, value in self._counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")

        # ゲージ
        for key, value in self._gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")

        # ヒストグラムサマリー
        for key, values in self._histograms.items():
            if values:
                base_name = key.split("{")[0]
                lines.append(f"# TYPE {base_name} summary")
                lines.append(f"{key}_count {len(values)}")
                lines.append(f"{key}_sum {sum(values)}")

        return "\n".join(lines)


class StructuredLogger:
    """構造化ロガー"""

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self._extra_fields: dict[str, Any] = {}

    def set_context(self, **kwargs) -> None:
        """ログコンテキストを設定"""
        self._extra_fields.update(kwargs)

    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """構造化メッセージをJSON形式で生成"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            **self._extra_fields,
            **kwargs,
        }
        return json.dumps(log_entry, ensure_ascii=False, default=str)

    def info(self, message: str, **kwargs) -> None:
        """INFO レベルでログ出力"""
        self.logger.info(self._format_message("INFO", message, **kwargs))

    def warning(self, message: str, **kwargs) -> None:
        """WARNING レベルでログ出力"""
        self.logger.warning(self._format_message("WARNING", message, **kwargs))

    def error(self, message: str, **kwargs) -> None:
        """ERROR レベルでログ出力"""
        self.logger.error(self._format_message("ERROR", message, **kwargs))

    def debug(self, message: str, **kwargs) -> None:
        """DEBUG レベルでログ出力"""
        self.logger.debug(self._format_message("DEBUG", message, **kwargs))

    def critical(self, message: str, **kwargs) -> None:
        """CRITICAL レベルでログ出力"""
        self.logger.critical(self._format_message("CRITICAL", message, **kwargs))


# シングルトンインスタンス
_health_checker: Optional[HealthChecker] = None
_metrics_collector: Optional[MetricsCollector] = None


def get_health_checker(version: str = "0.1.0", environment: str = "development") -> HealthChecker:
    """ヘルスチェッカーのシングルトンインスタンスを取得"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(version=version, environment=environment)
    return _health_checker


def get_metrics_collector() -> MetricsCollector:
    """メトリクスコレクターのシングルトンインスタンスを取得"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def create_logger(name: str, level: str = "INFO") -> StructuredLogger:
    """構造化ロガーを作成"""
    return StructuredLogger(name, level)
