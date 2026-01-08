# -*- coding: utf-8 -*-
"""
VisionCraftAI - レート制限

スライディングウィンドウ方式のレート制限を実装します。
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """レート制限設定"""
    # デフォルト制限（1分あたり）
    default_limit: int = 60

    # ウィンドウサイズ（秒）
    window_seconds: int = 60

    # バースト許容数
    burst_allowance: int = 10

    # クリーンアップ間隔（秒）
    cleanup_interval: int = 300


@dataclass
class RateLimitEntry:
    """レート制限エントリ"""
    # リクエストタイムスタンプリスト
    timestamps: list[float] = field(default_factory=list)

    # 制限値
    limit: int = 60

    # 最終クリーンアップ時刻
    last_cleanup: float = field(default_factory=time.time)


class RateLimiter:
    """
    スライディングウィンドウ方式のレート制限

    メモリベースの実装。分散環境ではRedis等に移行推奨。
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        初期化

        Args:
            config: レート制限設定
        """
        self._config = config or RateLimitConfig()
        self._entries: dict[str, RateLimitEntry] = defaultdict(
            lambda: RateLimitEntry(limit=self._config.default_limit)
        )
        self._lock = Lock()
        self._last_global_cleanup = time.time()

    def check(self, key: str, limit: Optional[int] = None) -> tuple[bool, dict]:
        """
        レート制限をチェック

        Args:
            key: 識別キー（key_id, IPアドレス等）
            limit: カスタム制限値

        Returns:
            tuple[bool, dict]: (許可するか, 状態情報)
        """
        with self._lock:
            now = time.time()
            window_start = now - self._config.window_seconds

            # 定期クリーンアップ
            if now - self._last_global_cleanup > self._config.cleanup_interval:
                self._cleanup_old_entries(now)
                self._last_global_cleanup = now

            # エントリ取得
            entry = self._entries[key]
            if limit is not None:
                entry.limit = limit

            # 古いタイムスタンプを削除
            entry.timestamps = [ts for ts in entry.timestamps if ts > window_start]

            # カウント
            current_count = len(entry.timestamps)
            effective_limit = entry.limit + self._config.burst_allowance

            # 状態情報
            status = {
                "key": key,
                "current_count": current_count,
                "limit": entry.limit,
                "effective_limit": effective_limit,
                "window_seconds": self._config.window_seconds,
                "remaining": max(0, effective_limit - current_count),
                "reset_at": window_start + self._config.window_seconds,
            }

            # 制限チェック
            if current_count >= effective_limit:
                logger.warning(f"レート制限超過: {key} ({current_count}/{effective_limit})")
                status["retry_after"] = self._calculate_retry_after(
                    entry.timestamps, window_start, effective_limit
                )
                return False, status

            return True, status

    def record(self, key: str) -> None:
        """
        リクエストを記録

        Args:
            key: 識別キー
        """
        with self._lock:
            now = time.time()
            self._entries[key].timestamps.append(now)

    def check_and_record(self, key: str, limit: Optional[int] = None) -> tuple[bool, dict]:
        """
        レート制限をチェックし、許可された場合に記録

        Args:
            key: 識別キー
            limit: カスタム制限値

        Returns:
            tuple[bool, dict]: (許可するか, 状態情報)
        """
        allowed, status = self.check(key, limit)
        if allowed:
            self.record(key)
            # 記録後の残数を更新
            status["remaining"] = max(0, status["remaining"] - 1)
        return allowed, status

    def get_status(self, key: str) -> dict:
        """
        現在の状態を取得

        Args:
            key: 識別キー

        Returns:
            状態情報
        """
        _, status = self.check(key)
        return status

    def reset(self, key: str) -> None:
        """
        特定キーのレート制限をリセット

        Args:
            key: 識別キー
        """
        with self._lock:
            if key in self._entries:
                self._entries[key].timestamps = []
                logger.info(f"レート制限をリセット: {key}")

    def set_limit(self, key: str, limit: int) -> None:
        """
        特定キーの制限値を設定

        Args:
            key: 識別キー
            limit: 制限値
        """
        with self._lock:
            self._entries[key].limit = limit

    def _calculate_retry_after(
        self,
        timestamps: list[float],
        window_start: float,
        limit: int,
    ) -> float:
        """
        リトライまでの待機時間を計算

        Args:
            timestamps: リクエストタイムスタンプリスト
            window_start: ウィンドウ開始時刻
            limit: 制限値

        Returns:
            待機時間（秒）
        """
        if len(timestamps) < limit:
            return 0.0

        # 最も古いリクエストがウィンドウから出るまでの時間
        sorted_timestamps = sorted(timestamps)
        oldest_in_window = sorted_timestamps[0]
        retry_after = (oldest_in_window + self._config.window_seconds) - time.time()
        return max(0.0, retry_after)

    def _cleanup_old_entries(self, now: float) -> None:
        """
        古いエントリをクリーンアップ

        Args:
            now: 現在時刻
        """
        window_start = now - self._config.window_seconds
        keys_to_remove = []

        for key, entry in self._entries.items():
            # 空のエントリを削除
            entry.timestamps = [ts for ts in entry.timestamps if ts > window_start]
            if not entry.timestamps and now - entry.last_cleanup > self._config.cleanup_interval * 2:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._entries[key]

        if keys_to_remove:
            logger.debug(f"{len(keys_to_remove)}個の古いエントリを削除")


# シングルトンインスタンス
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """RateLimiterのシングルトンを取得"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
