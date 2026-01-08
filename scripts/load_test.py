#!/usr/bin/env python3
"""
VisionCraftAI ロードテストスクリプト

本番デプロイ前のパフォーマンス検証用
"""

import argparse
import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median, stdev
from typing import Optional

import aiohttp


@dataclass
class LoadTestConfig:
    """ロードテスト設定"""
    base_url: str
    concurrent_users: int
    requests_per_user: int
    api_key: Optional[str] = None
    timeout: int = 30


@dataclass
class RequestResult:
    """リクエスト結果"""
    success: bool
    status_code: int
    latency_ms: float
    error: Optional[str] = None


@dataclass
class LoadTestReport:
    """ロードテストレポート"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    requests_per_second: float
    duration_seconds: float
    error_rate: float


class LoadTester:
    """ロードテスター"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: list[RequestResult] = []

    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        method: str = "GET",
        data: Optional[dict] = None
    ) -> RequestResult:
        """単一リクエストを実行"""
        url = f"{self.config.base_url}{endpoint}"
        headers = {}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        start_time = time.time()
        try:
            async with session.request(
                method,
                url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                latency_ms = (time.time() - start_time) * 1000
                await response.read()
                return RequestResult(
                    success=response.status < 400,
                    status_code=response.status,
                    latency_ms=latency_ms
                )
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            return RequestResult(
                success=False,
                status_code=0,
                latency_ms=latency_ms,
                error="Timeout"
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return RequestResult(
                success=False,
                status_code=0,
                latency_ms=latency_ms,
                error=str(e)
            )

    async def _user_session(
        self,
        user_id: int,
        endpoint: str,
        method: str = "GET",
        data: Optional[dict] = None
    ) -> list[RequestResult]:
        """1ユーザーのセッションをシミュレート"""
        results = []
        async with aiohttp.ClientSession() as session:
            for _ in range(self.config.requests_per_user):
                result = await self._make_request(session, endpoint, method, data)
                results.append(result)
        return results

    async def run_test(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[dict] = None
    ) -> LoadTestReport:
        """ロードテストを実行"""
        print(f"\n{'=' * 60}")
        print(f"ロードテスト開始: {endpoint}")
        print(f"同時ユーザー数: {self.config.concurrent_users}")
        print(f"ユーザーあたりリクエスト数: {self.config.requests_per_user}")
        print(f"{'=' * 60}\n")

        start_time = time.time()

        # 全ユーザーのタスクを作成
        tasks = [
            self._user_session(i, endpoint, method, data)
            for i in range(self.config.concurrent_users)
        ]

        # 並列実行
        all_results = await asyncio.gather(*tasks)

        # 結果を平坦化
        self.results = [r for user_results in all_results for r in user_results]

        duration = time.time() - start_time

        return self._generate_report(duration)

    def _generate_report(self, duration: float) -> LoadTestReport:
        """テスト結果レポートを生成"""
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        latencies = [r.latency_ms for r in self.results]

        # パーセンタイル計算
        sorted_latencies = sorted(latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p99_idx = int(len(sorted_latencies) * 0.99)

        return LoadTestReport(
            total_requests=len(self.results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            avg_latency_ms=mean(latencies) if latencies else 0,
            median_latency_ms=median(latencies) if latencies else 0,
            p95_latency_ms=sorted_latencies[p95_idx] if sorted_latencies else 0,
            p99_latency_ms=sorted_latencies[p99_idx] if sorted_latencies else 0,
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            requests_per_second=len(self.results) / duration if duration > 0 else 0,
            duration_seconds=duration,
            error_rate=len(failed) / len(self.results) * 100 if self.results else 0
        )


def print_report(report: LoadTestReport, test_name: str):
    """レポートを出力"""
    print(f"\n{'=' * 60}")
    print(f"テスト結果: {test_name}")
    print(f"{'=' * 60}")
    print(f"総リクエスト数:     {report.total_requests}")
    print(f"成功:               {report.successful_requests}")
    print(f"失敗:               {report.failed_requests}")
    print(f"エラー率:           {report.error_rate:.2f}%")
    print(f"{'=' * 60}")
    print(f"レイテンシー（ms）:")
    print(f"  平均:             {report.avg_latency_ms:.2f}")
    print(f"  中央値:           {report.median_latency_ms:.2f}")
    print(f"  P95:              {report.p95_latency_ms:.2f}")
    print(f"  P99:              {report.p99_latency_ms:.2f}")
    print(f"  最小:             {report.min_latency_ms:.2f}")
    print(f"  最大:             {report.max_latency_ms:.2f}")
    print(f"{'=' * 60}")
    print(f"スループット:       {report.requests_per_second:.2f} req/s")
    print(f"テスト時間:         {report.duration_seconds:.2f}秒")
    print(f"{'=' * 60}\n")


async def run_all_tests(config: LoadTestConfig):
    """全テストシナリオを実行"""
    tester = LoadTester(config)
    reports = []

    # テストシナリオ定義
    scenarios = [
        {
            "name": "ヘルスチェック",
            "endpoint": "/api/v1/health",
            "method": "GET",
            "data": None
        },
        {
            "name": "Liveness Probe",
            "endpoint": "/api/v1/monitoring/liveness",
            "method": "GET",
            "data": None
        },
        {
            "name": "Readiness Probe",
            "endpoint": "/api/v1/monitoring/readiness",
            "method": "GET",
            "data": None
        },
        {
            "name": "デモサンプル一覧",
            "endpoint": "/api/v1/demo/samples",
            "method": "GET",
            "data": None
        },
        {
            "name": "デモ画像生成",
            "endpoint": "/api/v1/demo/generate",
            "method": "POST",
            "data": {"prompt": "A beautiful sunset over mountains"}
        },
        {
            "name": "プロンプト検証",
            "endpoint": "/api/v1/prompt/validate",
            "method": "POST",
            "data": {"prompt": "A beautiful landscape"}
        },
        {
            "name": "料金プラン一覧",
            "endpoint": "/api/v1/payment/plans",
            "method": "GET",
            "data": None
        }
    ]

    print(f"\n{'#' * 60}")
    print(f"VisionCraftAI ロードテスト")
    print(f"開始時刻: {datetime.now().isoformat()}")
    print(f"ベースURL: {config.base_url}")
    print(f"{'#' * 60}\n")

    for scenario in scenarios:
        report = await tester.run_test(
            endpoint=scenario["endpoint"],
            method=scenario["method"],
            data=scenario["data"]
        )
        print_report(report, scenario["name"])
        reports.append((scenario["name"], report))

    # サマリー
    print(f"\n{'#' * 60}")
    print("サマリー")
    print(f"{'#' * 60}")
    print(f"{'テスト名':<25} {'成功率':>10} {'平均(ms)':>12} {'P95(ms)':>12}")
    print(f"{'-' * 60}")
    for name, report in reports:
        success_rate = (report.successful_requests / report.total_requests * 100
                       if report.total_requests > 0 else 0)
        print(f"{name:<25} {success_rate:>9.1f}% {report.avg_latency_ms:>12.2f} {report.p95_latency_ms:>12.2f}")
    print(f"{'#' * 60}\n")

    # 全体評価
    all_success = all(r[1].error_rate < 1 for r in reports)
    all_fast = all(r[1].p95_latency_ms < 1000 for r in reports)

    print("評価:")
    if all_success and all_fast:
        print("  ロードテスト合格")
    else:
        print("  ロードテスト要確認")
        if not all_success:
            print("    - エラー率が1%を超えているテストがあります")
        if not all_fast:
            print("    - P95レイテンシーが1000msを超えているテストがあります")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="VisionCraftAI ロードテスト")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="ベースURL（デフォルト: http://localhost:8000）"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=10,
        help="同時ユーザー数（デフォルト: 10）"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=10,
        help="ユーザーあたりリクエスト数（デフォルト: 10）"
    )
    parser.add_argument(
        "--api-key",
        help="APIキー（認証が必要なエンドポイント用）"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="リクエストタイムアウト秒（デフォルト: 30）"
    )

    args = parser.parse_args()

    config = LoadTestConfig(
        base_url=args.url,
        concurrent_users=args.users,
        requests_per_user=args.requests,
        api_key=args.api_key,
        timeout=args.timeout
    )

    asyncio.run(run_all_tests(config))


if __name__ == "__main__":
    main()
