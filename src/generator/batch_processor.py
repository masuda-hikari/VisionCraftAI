# -*- coding: utf-8 -*-
"""
VisionCraftAI - バッチ処理モジュール

複数のプロンプトを効率的に処理するバッチ処理機能を提供します。
収益化に向けた大量処理対応の基盤機能です。
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from src.generator.gemini_client import GeminiClient, GenerationResult
from src.utils.config import Config

logger = logging.getLogger(__name__)


@dataclass
class BatchJob:
    """バッチジョブ定義"""
    job_id: str
    prompts: list[str]
    output_dir: Optional[Path] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.job_id:
            self.job_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@dataclass
class BatchResult:
    """バッチ処理結果"""
    job_id: str
    total_count: int
    success_count: int
    failure_count: int
    results: list[GenerationResult]
    total_time_ms: int
    average_time_ms: float
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """成功率を計算"""
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100.0


class RateLimiter:
    """
    レート制限管理

    APIのレート制限を遵守するためのトークンバケット実装。
    収益化においてAPI使用料を最適化するために重要。
    """

    def __init__(self, max_requests_per_minute: int = 60):
        """
        Args:
            max_requests_per_minute: 1分あたりの最大リクエスト数
        """
        self.max_rpm = max_requests_per_minute
        self.interval_seconds = 60.0 / max_requests_per_minute
        self._last_request_time: float = 0.0
        self._request_count = 0
        self._window_start: float = 0.0

    def wait_if_needed(self) -> float:
        """
        必要に応じてレート制限のために待機

        Returns:
            float: 実際に待機した秒数
        """
        current_time = time.time()

        # ウィンドウをリセット（1分経過した場合）
        if current_time - self._window_start >= 60.0:
            self._window_start = current_time
            self._request_count = 0

        # 制限に達している場合は待機
        if self._request_count >= self.max_rpm:
            wait_time = 60.0 - (current_time - self._window_start)
            if wait_time > 0:
                logger.info(f"レート制限: {wait_time:.2f}秒待機")
                time.sleep(wait_time)
                self._window_start = time.time()
                self._request_count = 0
                return wait_time

        # 最小間隔の確保
        elapsed = current_time - self._last_request_time
        if elapsed < self.interval_seconds:
            sleep_time = self.interval_seconds - elapsed
            time.sleep(sleep_time)
            self._last_request_time = time.time()
            self._request_count += 1
            return sleep_time

        self._last_request_time = current_time
        self._request_count += 1
        return 0.0

    def reset(self) -> None:
        """レート制限カウンターをリセット"""
        self._last_request_time = 0.0
        self._request_count = 0
        self._window_start = 0.0


class BatchProcessor:
    """
    バッチ処理プロセッサ

    複数のプロンプトを効率的に処理し、レート制限を遵守しながら
    画像を生成します。収益化における大量処理の基盤。
    """

    def __init__(
        self,
        client: Optional[GeminiClient] = None,
        config: Optional[Config] = None,
    ):
        """
        Args:
            client: Geminiクライアント（省略時は新規作成）
            config: アプリケーション設定
        """
        self.config = config or Config.from_env()
        self.client = client or GeminiClient(self.config)
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=self.config.gemini.max_requests_per_minute
        )
        self._progress_callback: Optional[Callable[[int, int, GenerationResult], None]] = None

    def set_progress_callback(
        self,
        callback: Callable[[int, int, GenerationResult], None]
    ) -> None:
        """
        進捗コールバックを設定

        Args:
            callback: コールバック関数(current, total, result)
        """
        self._progress_callback = callback

    def process_batch(
        self,
        job: BatchJob,
        stop_on_error: bool = False,
    ) -> BatchResult:
        """
        バッチジョブを処理

        Args:
            job: バッチジョブ定義
            stop_on_error: エラー時に停止するか

        Returns:
            BatchResult: バッチ処理結果
        """
        start_time = time.time()
        results: list[GenerationResult] = []
        errors: list[str] = []
        success_count = 0
        failure_count = 0

        # 出力ディレクトリの準備
        output_dir = job.output_dir or self.config.ensure_output_dir()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"バッチ処理開始: {job.job_id} ({len(job.prompts)}件)")

        for idx, prompt in enumerate(job.prompts):
            # レート制限
            self.rate_limiter.wait_if_needed()

            # 出力パスを生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            output_path = str(
                output_dir / f"{job.job_id}_{idx:04d}_{timestamp}.{self.config.image.output_format}"
            )

            # 画像生成
            result = self.client.generate_image(
                prompt=prompt,
                output_path=output_path,
            )
            results.append(result)

            if result.success:
                success_count += 1
                logger.info(f"[{idx + 1}/{len(job.prompts)}] 成功: {output_path}")
            else:
                failure_count += 1
                error_msg = f"[{idx + 1}/{len(job.prompts)}] 失敗: {result.error_message}"
                errors.append(error_msg)
                logger.warning(error_msg)

                if stop_on_error:
                    logger.error("エラーで停止")
                    break

            # 進捗コールバック
            if self._progress_callback:
                self._progress_callback(idx + 1, len(job.prompts), result)

        total_time_ms = int((time.time() - start_time) * 1000)
        processed_count = success_count + failure_count
        average_time = total_time_ms / processed_count if processed_count > 0 else 0.0

        logger.info(
            f"バッチ処理完了: {job.job_id} "
            f"成功={success_count} 失敗={failure_count} "
            f"時間={total_time_ms}ms"
        )

        return BatchResult(
            job_id=job.job_id,
            total_count=len(job.prompts),
            success_count=success_count,
            failure_count=failure_count,
            results=results,
            total_time_ms=total_time_ms,
            average_time_ms=average_time,
            errors=errors,
        )

    def process_prompts(
        self,
        prompts: list[str],
        job_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> BatchResult:
        """
        プロンプトリストを処理（簡易API）

        Args:
            prompts: プロンプトリスト
            job_id: ジョブID（省略時は自動生成）
            output_dir: 出力ディレクトリ

        Returns:
            BatchResult: バッチ処理結果
        """
        job = BatchJob(
            job_id=job_id or "",
            prompts=prompts,
            output_dir=output_dir,
        )
        return self.process_batch(job)

    def estimate_time(self, prompt_count: int) -> dict:
        """
        処理時間を見積もり

        Args:
            prompt_count: プロンプト数

        Returns:
            dict: 見積もり情報
        """
        # レート制限に基づく最小時間
        rate_limit_time = (prompt_count / self.config.gemini.max_requests_per_minute) * 60

        # 平均生成時間を仮定（5秒）
        estimated_generation_time = prompt_count * 5.0

        # 合計見積もり時間（大きい方を採用）
        estimated_seconds = max(rate_limit_time, estimated_generation_time)

        return {
            "prompt_count": prompt_count,
            "rate_limit_time_seconds": rate_limit_time,
            "estimated_generation_seconds": estimated_generation_time,
            "total_estimated_seconds": estimated_seconds,
            "total_estimated_minutes": estimated_seconds / 60,
        }
