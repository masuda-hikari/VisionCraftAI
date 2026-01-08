# -*- coding: utf-8 -*-
"""
VisionCraftAI - リトライユーティリティ

API呼び出しのリトライ機能を提供します。
収益化において安定したサービス提供のために必須の機能です。
"""

import functools
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryStrategy(Enum):
    """リトライ戦略"""
    FIXED = "fixed"  # 固定間隔
    EXPONENTIAL = "exponential"  # 指数バックオフ
    LINEAR = "linear"  # 線形増加


@dataclass
class RetryConfig:
    """リトライ設定"""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True  # ランダムな揺らぎを追加
    jitter_factor: float = 0.1  # 揺らぎの係数

    # リトライ対象の例外タイプ
    retryable_exceptions: tuple[Type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
    )

    # リトライしない例外タイプ
    non_retryable_exceptions: tuple[Type[Exception], ...] = (
        ValueError,
        TypeError,
    )


class RetryError(Exception):
    """リトライ失敗時の例外"""

    def __init__(
        self,
        message: str,
        attempts: int,
        last_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


def calculate_delay(
    attempt: int,
    config: RetryConfig,
) -> float:
    """
    リトライ遅延時間を計算

    Args:
        attempt: 現在の試行回数（0始まり）
        config: リトライ設定

    Returns:
        float: 遅延秒数
    """
    if config.strategy == RetryStrategy.FIXED:
        delay = config.base_delay_seconds
    elif config.strategy == RetryStrategy.EXPONENTIAL:
        delay = config.base_delay_seconds * (2 ** attempt)
    elif config.strategy == RetryStrategy.LINEAR:
        delay = config.base_delay_seconds * (attempt + 1)
    else:
        delay = config.base_delay_seconds

    # 最大遅延を適用
    delay = min(delay, config.max_delay_seconds)

    # ジッターを追加
    if config.jitter:
        jitter = delay * config.jitter_factor * random.random()
        delay += jitter

    return delay


def should_retry(
    exception: Exception,
    config: RetryConfig,
) -> bool:
    """
    リトライすべきかを判定

    Args:
        exception: 発生した例外
        config: リトライ設定

    Returns:
        bool: リトライすべきならTrue
    """
    # 明示的に除外された例外
    if isinstance(exception, config.non_retryable_exceptions):
        return False

    # 明示的にリトライ対象の例外
    if isinstance(exception, config.retryable_exceptions):
        return True

    # API関連のエラーメッセージを確認
    error_msg = str(exception).lower()
    retryable_messages = [
        "rate limit",
        "timeout",
        "connection",
        "temporary",
        "unavailable",
        "500",
        "502",
        "503",
        "504",
    ]

    return any(msg in error_msg for msg in retryable_messages)


def retry_with_backoff(
    func: Optional[Callable[..., T]] = None,
    *,
    config: Optional[RetryConfig] = None,
    max_retries: Optional[int] = None,
    base_delay: Optional[float] = None,
) -> Callable[..., T]:
    """
    リトライデコレーター

    指定された関数をリトライ機能で包みます。

    Args:
        func: デコレート対象の関数
        config: リトライ設定
        max_retries: 最大リトライ回数（configより優先）
        base_delay: 基本遅延秒数（configより優先）

    Returns:
        デコレートされた関数

    Examples:
        @retry_with_backoff(max_retries=5)
        def api_call():
            ...

        @retry_with_backoff(config=RetryConfig(strategy=RetryStrategy.LINEAR))
        def another_call():
            ...
    """
    retry_config = config or RetryConfig()
    if max_retries is not None:
        retry_config.max_retries = max_retries
    if base_delay is not None:
        retry_config.base_delay_seconds = base_delay

    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(retry_config.max_retries + 1):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # リトライすべきか判定
                    if not should_retry(e, retry_config):
                        logger.warning(
                            f"リトライ不可の例外: {type(e).__name__}: {e}"
                        )
                        raise

                    # 最後の試行なら例外を投げる
                    if attempt >= retry_config.max_retries:
                        logger.error(
                            f"リトライ上限に達しました: {attempt + 1}回試行"
                        )
                        raise RetryError(
                            f"リトライ上限({retry_config.max_retries}回)に達しました",
                            attempts=attempt + 1,
                            last_exception=last_exception,
                        ) from e

                    # 遅延時間を計算して待機
                    delay = calculate_delay(attempt, retry_config)
                    logger.warning(
                        f"リトライ {attempt + 1}/{retry_config.max_retries}: "
                        f"{type(e).__name__}: {e} "
                        f"({delay:.2f}秒後に再試行)"
                    )
                    time.sleep(delay)

            # ここには到達しないはず
            raise RetryError(
                "予期しないリトライループ終了",
                attempts=retry_config.max_retries + 1,
                last_exception=last_exception,
            )

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


class RetryContext:
    """
    リトライコンテキストマネージャー

    with文でリトライを制御するためのコンテキストマネージャー。

    Examples:
        with RetryContext(max_retries=3) as ctx:
            while ctx.should_continue:
                try:
                    result = api_call()
                    ctx.success()
                    break
                except Exception as e:
                    ctx.failed(e)
    """

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        max_retries: Optional[int] = None,
    ):
        self.config = config or RetryConfig()
        if max_retries is not None:
            self.config.max_retries = max_retries

        self._attempt = 0
        self._succeeded = False
        self._last_exception: Optional[Exception] = None

    def __enter__(self) -> "RetryContext":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[Exception]],
        exc_val: Optional[Exception],
        exc_tb: Any,
    ) -> bool:
        # 例外を抑制しない
        return False

    @property
    def should_continue(self) -> bool:
        """リトライを続けるべきか"""
        return not self._succeeded and self._attempt <= self.config.max_retries

    @property
    def attempt(self) -> int:
        """現在の試行回数"""
        return self._attempt

    def success(self) -> None:
        """成功をマーク"""
        self._succeeded = True

    def failed(self, exception: Exception) -> None:
        """
        失敗をマークし、必要に応じて待機

        Args:
            exception: 発生した例外
        """
        self._last_exception = exception
        self._attempt += 1

        if not should_retry(exception, self.config):
            raise exception

        if self._attempt > self.config.max_retries:
            raise RetryError(
                f"リトライ上限({self.config.max_retries}回)に達しました",
                attempts=self._attempt,
                last_exception=exception,
            ) from exception

        delay = calculate_delay(self._attempt - 1, self.config)
        logger.warning(
            f"リトライ {self._attempt}/{self.config.max_retries}: "
            f"{type(exception).__name__}: {exception} "
            f"({delay:.2f}秒後に再試行)"
        )
        time.sleep(delay)
