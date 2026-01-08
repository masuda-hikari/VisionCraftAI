# -*- coding: utf-8 -*-
"""
VisionCraftAI - バッチ処理モジュールのテスト
"""

import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.generator.batch_processor import (
    BatchJob,
    BatchProcessor,
    BatchResult,
    RateLimiter,
)
from src.generator.gemini_client import GenerationResult


class TestRateLimiter:
    """RateLimiterのテスト"""

    def test_init(self):
        """初期化テスト"""
        limiter = RateLimiter(max_requests_per_minute=60)
        assert limiter.max_rpm == 60
        assert limiter.interval_seconds == 1.0

    def test_wait_if_needed_first_call(self):
        """最初の呼び出しは待機しない"""
        limiter = RateLimiter(max_requests_per_minute=60)
        wait_time = limiter.wait_if_needed()
        # 最初の呼び出しは待機しないはず
        assert wait_time < 0.1

    def test_wait_if_needed_rapid_calls(self):
        """連続呼び出し時の待機"""
        limiter = RateLimiter(max_requests_per_minute=120)  # 0.5秒間隔
        limiter.wait_if_needed()
        start = time.time()
        limiter.wait_if_needed()
        elapsed = time.time() - start
        # 最小間隔（0.5秒）程度の待機があるはず
        assert elapsed >= 0.4  # マージンを持たせる

    def test_reset(self):
        """リセットテスト"""
        limiter = RateLimiter(max_requests_per_minute=60)
        limiter.wait_if_needed()
        limiter.reset()
        assert limiter._request_count == 0
        assert limiter._last_request_time == 0.0


class TestBatchJob:
    """BatchJobのテスト"""

    def test_create_with_job_id(self):
        """ジョブID指定で作成"""
        job = BatchJob(job_id="test_job", prompts=["prompt1", "prompt2"])
        assert job.job_id == "test_job"
        assert len(job.prompts) == 2

    def test_create_without_job_id(self):
        """ジョブID自動生成"""
        job = BatchJob(job_id="", prompts=["prompt1"])
        assert job.job_id.startswith("batch_")


class TestBatchResult:
    """BatchResultのテスト"""

    def test_success_rate_all_success(self):
        """全成功時の成功率"""
        result = BatchResult(
            job_id="test",
            total_count=10,
            success_count=10,
            failure_count=0,
            results=[],
            total_time_ms=1000,
            average_time_ms=100.0,
        )
        assert result.success_rate == 100.0

    def test_success_rate_partial(self):
        """部分成功時の成功率"""
        result = BatchResult(
            job_id="test",
            total_count=10,
            success_count=7,
            failure_count=3,
            results=[],
            total_time_ms=1000,
            average_time_ms=100.0,
        )
        assert result.success_rate == 70.0

    def test_success_rate_zero_total(self):
        """0件時の成功率"""
        result = BatchResult(
            job_id="test",
            total_count=0,
            success_count=0,
            failure_count=0,
            results=[],
            total_time_ms=0,
            average_time_ms=0.0,
        )
        assert result.success_rate == 0.0


class TestBatchProcessor:
    """BatchProcessorのテスト"""

    @pytest.fixture
    def mock_client(self):
        """モッククライアント"""
        client = MagicMock()
        client.generate_image.return_value = GenerationResult(
            success=True,
            image_data=b"fake_image",
            file_path="/tmp/test.png",
            prompt="test",
            generation_time_ms=100,
            model_used="test-model",
        )
        return client

    @pytest.fixture
    def processor(self, mock_client):
        """プロセッサ"""
        with patch("src.generator.batch_processor.Config") as mock_config_cls:
            mock_config = MagicMock()
            mock_config.gemini.max_requests_per_minute = 60
            mock_config.image.output_format = "png"
            mock_config.ensure_output_dir.return_value = Path("/tmp")
            mock_config_cls.from_env.return_value = mock_config

            processor = BatchProcessor(client=mock_client, config=mock_config)
            return processor

    def test_process_prompts_success(self, processor, mock_client, tmp_path):
        """プロンプト処理成功テスト"""
        prompts = ["prompt1", "prompt2", "prompt3"]

        # rate limiterの待機を最小化
        processor.rate_limiter = RateLimiter(max_requests_per_minute=6000)

        result = processor.process_prompts(
            prompts=prompts,
            job_id="test_job",
            output_dir=tmp_path,
        )

        assert result.total_count == 3
        assert result.success_count == 3
        assert result.failure_count == 0
        assert mock_client.generate_image.call_count == 3

    def test_process_prompts_with_failures(self, processor, mock_client, tmp_path):
        """一部失敗を含む処理テスト"""
        # 2回目の呼び出しで失敗を返す
        mock_client.generate_image.side_effect = [
            GenerationResult(success=True, image_data=b"img", file_path="/tmp/1.png", prompt="p1"),
            GenerationResult(success=False, prompt="p2", error_message="API Error"),
            GenerationResult(success=True, image_data=b"img", file_path="/tmp/3.png", prompt="p3"),
        ]

        processor.rate_limiter = RateLimiter(max_requests_per_minute=6000)

        result = processor.process_prompts(
            prompts=["p1", "p2", "p3"],
            output_dir=tmp_path,
        )

        assert result.total_count == 3
        assert result.success_count == 2
        assert result.failure_count == 1
        assert len(result.errors) == 1

    def test_estimate_time(self, processor):
        """時間見積もりテスト"""
        estimate = processor.estimate_time(prompt_count=60)

        assert estimate["prompt_count"] == 60
        assert "total_estimated_seconds" in estimate
        assert "total_estimated_minutes" in estimate

    def test_progress_callback(self, processor, mock_client, tmp_path):
        """進捗コールバックテスト"""
        callback_calls = []

        def callback(current, total, result):
            callback_calls.append((current, total, result.success))

        processor.set_progress_callback(callback)
        processor.rate_limiter = RateLimiter(max_requests_per_minute=6000)

        processor.process_prompts(
            prompts=["p1", "p2"],
            output_dir=tmp_path,
        )

        assert len(callback_calls) == 2
        assert callback_calls[0] == (1, 2, True)
        assert callback_calls[1] == (2, 2, True)
