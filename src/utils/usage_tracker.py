# -*- coding: utf-8 -*-
"""
VisionCraftAI - 使用量トラッキングモジュール

API使用量とコストを追跡します。
収益化においてコスト管理は最重要事項です。
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """使用量レコード"""
    timestamp: str
    operation: str  # "generate_image", "check_connection", etc.
    prompt_length: int
    success: bool
    generation_time_ms: int
    model: str
    error_message: Optional[str] = None
    estimated_cost_usd: float = 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "UsageRecord":
        """辞書から作成"""
        return cls(**data)


@dataclass
class UsageSummary:
    """使用量サマリー"""
    period_start: str
    period_end: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_generation_time_ms: int
    average_generation_time_ms: float
    total_estimated_cost_usd: float
    operations_breakdown: dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """成功率を計算"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100.0


class UsageTracker:
    """
    使用量トラッカー

    API使用量を追跡し、コスト管理を支援します。
    収益化において適切なコスト管理は利益率に直結します。
    """

    # コスト見積もり（USD）- Gemini API概算
    # 実際の料金はGoogle Cloud Pricingを参照
    ESTIMATED_COST_PER_IMAGE = 0.01  # 画像生成1回あたり
    ESTIMATED_COST_PER_1K_CHARS = 0.0001  # 入力1000文字あたり

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        auto_save: bool = True,
    ):
        """
        Args:
            storage_path: 使用量データの保存先
            auto_save: 自動保存を有効化
        """
        self.storage_path = storage_path or Path("logs/usage_data.json")
        self.auto_save = auto_save
        self._records: list[UsageRecord] = []
        self._load()

    def _load(self) -> None:
        """保存データを読み込み"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._records = [
                        UsageRecord.from_dict(r) for r in data.get("records", [])
                    ]
                logger.info(f"使用量データ読み込み完了: {len(self._records)}件")
            except Exception as e:
                logger.warning(f"使用量データ読み込み失敗: {e}")
                self._records = []

    def _save(self) -> None:
        """データを保存"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                data = {
                    "last_updated": datetime.now().isoformat(),
                    "record_count": len(self._records),
                    "records": [asdict(r) for r in self._records],
                }
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"使用量データ保存完了: {len(self._records)}件")
        except Exception as e:
            logger.error(f"使用量データ保存失敗: {e}")

    def record(
        self,
        operation: str,
        prompt_length: int,
        success: bool,
        generation_time_ms: int,
        model: str,
        error_message: Optional[str] = None,
    ) -> UsageRecord:
        """
        使用量を記録

        Args:
            operation: 操作タイプ
            prompt_length: プロンプト長
            success: 成功したか
            generation_time_ms: 生成時間（ミリ秒）
            model: 使用モデル
            error_message: エラーメッセージ

        Returns:
            UsageRecord: 記録されたレコード
        """
        # コスト見積もり
        estimated_cost = self._estimate_cost(operation, prompt_length, success)

        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            operation=operation,
            prompt_length=prompt_length,
            success=success,
            generation_time_ms=generation_time_ms,
            model=model,
            error_message=error_message,
            estimated_cost_usd=estimated_cost,
        )

        self._records.append(record)

        if self.auto_save:
            self._save()

        return record

    def _estimate_cost(
        self,
        operation: str,
        prompt_length: int,
        success: bool,
    ) -> float:
        """
        コストを見積もり

        Args:
            operation: 操作タイプ
            prompt_length: プロンプト長
            success: 成功したか

        Returns:
            float: 見積もりコスト（USD）
        """
        if not success:
            # 失敗時は入力コストのみ
            return (prompt_length / 1000) * self.ESTIMATED_COST_PER_1K_CHARS

        cost = (prompt_length / 1000) * self.ESTIMATED_COST_PER_1K_CHARS

        if operation == "generate_image":
            cost += self.ESTIMATED_COST_PER_IMAGE

        return round(cost, 6)

    def get_summary(
        self,
        days: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> UsageSummary:
        """
        使用量サマリーを取得

        Args:
            days: 過去N日間（省略時は全期間）
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            UsageSummary: サマリー
        """
        # 期間フィルタリング
        if days is not None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

        filtered_records = self._records
        if start_date:
            filtered_records = [
                r for r in filtered_records
                if datetime.fromisoformat(r.timestamp) >= start_date
            ]
        if end_date:
            filtered_records = [
                r for r in filtered_records
                if datetime.fromisoformat(r.timestamp) <= end_date
            ]

        # 集計
        total_requests = len(filtered_records)
        successful_requests = sum(1 for r in filtered_records if r.success)
        failed_requests = total_requests - successful_requests
        total_time_ms = sum(r.generation_time_ms for r in filtered_records)
        total_cost = sum(r.estimated_cost_usd for r in filtered_records)

        # 操作別集計
        operations_breakdown: dict[str, int] = {}
        for record in filtered_records:
            operations_breakdown[record.operation] = (
                operations_breakdown.get(record.operation, 0) + 1
            )

        # 期間
        if filtered_records:
            timestamps = [
                datetime.fromisoformat(r.timestamp) for r in filtered_records
            ]
            period_start = min(timestamps).isoformat()
            period_end = max(timestamps).isoformat()
        else:
            now = datetime.now()
            period_start = now.isoformat()
            period_end = now.isoformat()

        return UsageSummary(
            period_start=period_start,
            period_end=period_end,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_generation_time_ms=total_time_ms,
            average_generation_time_ms=(
                total_time_ms / total_requests if total_requests > 0 else 0.0
            ),
            total_estimated_cost_usd=round(total_cost, 4),
            operations_breakdown=operations_breakdown,
        )

    def get_daily_breakdown(
        self,
        days: int = 30,
    ) -> list[dict]:
        """
        日別の使用量を取得

        Args:
            days: 過去N日間

        Returns:
            list[dict]: 日別データ
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 日別に集計
        daily_data: dict[str, dict] = {}

        for record in self._records:
            record_date = datetime.fromisoformat(record.timestamp)
            if record_date < start_date or record_date > end_date:
                continue

            date_key = record_date.strftime("%Y-%m-%d")
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "date": date_key,
                    "requests": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_time_ms": 0,
                    "estimated_cost_usd": 0.0,
                }

            daily_data[date_key]["requests"] += 1
            if record.success:
                daily_data[date_key]["successful"] += 1
            else:
                daily_data[date_key]["failed"] += 1
            daily_data[date_key]["total_time_ms"] += record.generation_time_ms
            daily_data[date_key]["estimated_cost_usd"] += record.estimated_cost_usd

        # 日付順にソート
        return sorted(daily_data.values(), key=lambda x: x["date"])

    def export_report(
        self,
        output_path: Optional[Path] = None,
        days: int = 30,
    ) -> Path:
        """
        使用量レポートをエクスポート

        Args:
            output_path: 出力先パス
            days: 過去N日間

        Returns:
            Path: 出力ファイルパス
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"logs/usage_report_{timestamp}.json")

        summary = self.get_summary(days=days)
        daily = self.get_daily_breakdown(days=days)

        report = {
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "summary": asdict(summary),
            "daily_breakdown": daily,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"使用量レポート出力: {output_path}")
        return output_path

    def clear_old_records(self, days: int = 90) -> int:
        """
        古いレコードを削除

        Args:
            days: N日より古いレコードを削除

        Returns:
            int: 削除されたレコード数
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        original_count = len(self._records)

        self._records = [
            r for r in self._records
            if datetime.fromisoformat(r.timestamp) >= cutoff_date
        ]

        deleted_count = original_count - len(self._records)

        if deleted_count > 0:
            self._save()
            logger.info(f"古いレコードを削除: {deleted_count}件")

        return deleted_count
