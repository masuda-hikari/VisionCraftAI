# -*- coding: utf-8 -*-
"""
VisionCraftAI - リトライモジュールのテスト
"""

import time
from unittest.mock import patch

import pytest

from src.utils.retry import (
    RetryConfig,
    RetryContext,
    RetryError,
    RetryStrategy,
    calculate_delay,
    retry_with_backoff,
    should_retry,
)


class TestCalculateDelay:
    """calculate_delay関数のテスト"""

    def test_fixed_strategy(self):
        """固定間隔戦略"""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED,
            base_delay_seconds=2.0,
            jitter=False,
        )
        assert calculate_delay(0, config) == 2.0
        assert calculate_delay(1, config) == 2.0
        assert calculate_delay(5, config) == 2.0

    def test_exponential_strategy(self):
        """指数バックオフ戦略"""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay_seconds=1.0,
            jitter=False,
        )
        assert calculate_delay(0, config) == 1.0  # 1 * 2^0
        assert calculate_delay(1, config) == 2.0  # 1 * 2^1
        assert calculate_delay(2, config) == 4.0  # 1 * 2^2

    def test_linear_strategy(self):
        """線形増加戦略"""
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR,
            base_delay_seconds=1.0,
            jitter=False,
        )
        assert calculate_delay(0, config) == 1.0  # 1 * 1
        assert calculate_delay(1, config) == 2.0  # 1 * 2
        assert calculate_delay(2, config) == 3.0  # 1 * 3

    def test_max_delay(self):
        """最大遅延の適用"""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            base_delay_seconds=10.0,
            max_delay_seconds=30.0,
            jitter=False,
        )
        # 10 * 2^3 = 80 > 30 なので30に制限
        assert calculate_delay(3, config) == 30.0

    def test_jitter(self):
        """ジッター追加"""
        config = RetryConfig(
            strategy=RetryStrategy.FIXED,
            base_delay_seconds=10.0,
            jitter=True,
            jitter_factor=0.1,
        )
        delay = calculate_delay(0, config)
        # 10.0 + (0 to 1.0) の範囲
        assert 10.0 <= delay <= 11.0


class TestShouldRetry:
    """should_retry関数のテスト"""

    def test_retryable_connection_error(self):
        """ConnectionErrorはリトライ可能"""
        config = RetryConfig()
        assert should_retry(ConnectionError("Connection refused"), config) is True

    def test_retryable_timeout_error(self):
        """TimeoutErrorはリトライ可能"""
        config = RetryConfig()
        assert should_retry(TimeoutError("Request timed out"), config) is True

    def test_non_retryable_value_error(self):
        """ValueErrorはリトライ不可"""
        config = RetryConfig()
        assert should_retry(ValueError("Invalid value"), config) is False

    def test_rate_limit_message(self):
        """レート制限メッセージはリトライ可能"""
        config = RetryConfig()
        assert should_retry(Exception("Rate limit exceeded"), config) is True

    def test_500_error_message(self):
        """500エラーメッセージはリトライ可能"""
        config = RetryConfig()
        assert should_retry(Exception("Server returned 500"), config) is True


class TestRetryWithBackoff:
    """retry_with_backoffデコレーターのテスト"""

    def test_success_first_try(self):
        """最初の試行で成功"""
        @retry_with_backoff(max_retries=3)
        def always_succeeds():
            return "success"

        assert always_succeeds() == "success"

    def test_retry_then_success(self):
        """リトライ後に成功"""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def fails_then_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary failure")
            return "success"

        result = fails_then_succeeds()
        assert result == "success"
        assert call_count == 2

    def test_max_retries_exceeded(self):
        """最大リトライ回数超過"""
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fails():
            raise ConnectionError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            always_fails()

        assert exc_info.value.attempts == 3  # 初回 + 2リトライ

    def test_non_retryable_exception(self):
        """リトライ不可の例外は即座に再スロー"""
        @retry_with_backoff(max_retries=3)
        def raises_value_error():
            raise ValueError("Invalid value")

        with pytest.raises(ValueError):
            raises_value_error()


class TestRetryContext:
    """RetryContextのテスト"""

    def test_success_first_try(self):
        """最初の試行で成功"""
        with RetryContext(max_retries=3) as ctx:
            assert ctx.should_continue is True
            ctx.success()
            assert ctx.should_continue is False

    def test_retry_loop(self):
        """リトライループ"""
        attempts = 0

        with RetryContext(config=RetryConfig(base_delay_seconds=0.01, max_retries=2)) as ctx:
            while ctx.should_continue:
                try:
                    attempts += 1
                    if attempts < 2:
                        raise ConnectionError("Fail")
                    ctx.success()
                    break
                except Exception as e:
                    ctx.failed(e)

        assert attempts == 2
        assert ctx.attempt == 1

    def test_max_retries_in_context(self):
        """コンテキスト内でのリトライ上限"""
        with RetryContext(config=RetryConfig(base_delay_seconds=0.01, max_retries=1)) as ctx:
            while ctx.should_continue:
                try:
                    raise ConnectionError("Always fail")
                except Exception as e:
                    if ctx.attempt >= ctx.config.max_retries:
                        with pytest.raises(RetryError):
                            ctx.failed(e)
                        break
                    ctx.failed(e)


class TestRetryError:
    """RetryErrorのテスト"""

    def test_retry_error_attributes(self):
        """RetryErrorの属性"""
        original = ValueError("Original error")
        error = RetryError("Retry failed", attempts=3, last_exception=original)

        assert error.attempts == 3
        assert error.last_exception is original
        assert "Retry failed" in str(error)
