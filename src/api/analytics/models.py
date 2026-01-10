# -*- coding: utf-8 -*-
"""
VisionCraftAI - 分析・A/Bテストモデル

A/Bテストとユーザー行動分析のデータモデルを定義します。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import hashlib
import secrets


class ABTestStatus(str, Enum):
    """A/Bテストの状態"""
    DRAFT = "draft"            # 下書き
    RUNNING = "running"        # 実行中
    PAUSED = "paused"          # 一時停止
    COMPLETED = "completed"    # 完了
    ARCHIVED = "archived"      # アーカイブ


class EventType(str, Enum):
    """イベントタイプ"""
    PAGE_VIEW = "page_view"
    BUTTON_CLICK = "button_click"
    FORM_SUBMIT = "form_submit"
    SIGN_UP = "sign_up"
    LOGIN = "login"
    GENERATE_IMAGE = "generate_image"
    PURCHASE = "purchase"
    SUBSCRIPTION_START = "subscription_start"
    SUBSCRIPTION_CANCEL = "subscription_cancel"
    CREDIT_PURCHASE = "credit_purchase"
    REFERRAL_SENT = "referral_sent"
    REFERRAL_CONVERTED = "referral_converted"
    TRIAL_START = "trial_start"
    TRIAL_CONVERT = "trial_convert"
    SHARE = "share"
    DOWNLOAD = "download"
    CUSTOM = "custom"


class ConversionGoalType(str, Enum):
    """コンバージョンゴールタイプ"""
    SIGN_UP = "sign_up"
    PURCHASE = "purchase"
    SUBSCRIPTION = "subscription"
    ENGAGEMENT = "engagement"
    RETENTION = "retention"
    CUSTOM = "custom"


@dataclass
class ABTestVariant:
    """A/Bテストのバリアント（テストパターン）"""
    id: str
    name: str
    description: str = ""
    weight: float = 50.0  # トラフィック配分（%）
    config: dict = field(default_factory=dict)  # バリアント固有の設定

    # 統計
    impressions: int = 0      # 表示回数
    conversions: int = 0      # コンバージョン数
    revenue: float = 0.0      # 収益

    # 計算プロパティ
    @property
    def conversion_rate(self) -> float:
        """コンバージョン率"""
        if self.impressions == 0:
            return 0.0
        return (self.conversions / self.impressions) * 100.0

    @property
    def revenue_per_impression(self) -> float:
        """表示あたり収益"""
        if self.impressions == 0:
            return 0.0
        return self.revenue / self.impressions

    def to_dict(self) -> dict:
        """辞書に変換"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "config": self.config,
            "impressions": self.impressions,
            "conversions": self.conversions,
            "revenue": self.revenue,
            "conversion_rate": self.conversion_rate,
            "revenue_per_impression": self.revenue_per_impression,
        }


@dataclass
class ABTest:
    """A/Bテスト"""
    id: str
    name: str
    description: str = ""
    status: ABTestStatus = ABTestStatus.DRAFT

    # テスト設定
    variants: list[ABTestVariant] = field(default_factory=list)
    goal_type: ConversionGoalType = ConversionGoalType.SUBSCRIPTION
    goal_event: str = ""  # 目標イベント名

    # 期間
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # メタデータ
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = ""

    # 統計的有意性
    minimum_sample_size: int = 100
    confidence_level: float = 0.95  # 95%信頼区間

    @classmethod
    def create(
        cls,
        name: str,
        description: str = "",
        goal_type: ConversionGoalType = ConversionGoalType.SUBSCRIPTION,
        goal_event: str = "",
        created_by: str = "",
    ) -> "ABTest":
        """新規A/Bテストを作成"""
        test_id = f"abt_{secrets.token_hex(8)}"
        return cls(
            id=test_id,
            name=name,
            description=description,
            goal_type=goal_type,
            goal_event=goal_event,
            created_by=created_by,
        )

    def add_variant(
        self,
        name: str,
        description: str = "",
        weight: float = 50.0,
        config: Optional[dict] = None,
    ) -> ABTestVariant:
        """バリアントを追加"""
        variant_id = f"var_{secrets.token_hex(4)}"
        variant = ABTestVariant(
            id=variant_id,
            name=name,
            description=description,
            weight=weight,
            config=config or {},
        )
        self.variants.append(variant)
        self._normalize_weights()
        return variant

    def _normalize_weights(self):
        """重みを正規化（合計100%）"""
        if not self.variants:
            return
        total_weight = sum(v.weight for v in self.variants)
        if total_weight > 0:
            for v in self.variants:
                v.weight = (v.weight / total_weight) * 100.0

    def start(self):
        """テストを開始"""
        if not self.variants:
            raise ValueError("バリアントが設定されていません")
        if len(self.variants) < 2:
            raise ValueError("最低2つのバリアントが必要です")
        self.status = ABTestStatus.RUNNING
        self.start_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def pause(self):
        """テストを一時停止"""
        self.status = ABTestStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def resume(self):
        """テストを再開"""
        self.status = ABTestStatus.RUNNING
        self.updated_at = datetime.utcnow()

    def complete(self):
        """テストを完了"""
        self.status = ABTestStatus.COMPLETED
        self.end_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def is_active(self) -> bool:
        """テストがアクティブか"""
        return self.status == ABTestStatus.RUNNING

    @property
    def total_impressions(self) -> int:
        """総表示回数"""
        return sum(v.impressions for v in self.variants)

    @property
    def total_conversions(self) -> int:
        """総コンバージョン数"""
        return sum(v.conversions for v in self.variants)

    @property
    def total_revenue(self) -> float:
        """総収益"""
        return sum(v.revenue for v in self.variants)

    @property
    def winner(self) -> Optional[ABTestVariant]:
        """勝者バリアント（最高コンバージョン率）"""
        if not self.variants:
            return None
        # サンプルサイズが足りない場合はNone
        if self.total_impressions < self.minimum_sample_size:
            return None
        return max(self.variants, key=lambda v: v.conversion_rate)

    def to_dict(self) -> dict:
        """辞書に変換"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "variants": [v.to_dict() for v in self.variants],
            "goal_type": self.goal_type.value,
            "goal_event": self.goal_event,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "minimum_sample_size": self.minimum_sample_size,
            "confidence_level": self.confidence_level,
            "total_impressions": self.total_impressions,
            "total_conversions": self.total_conversions,
            "total_revenue": self.total_revenue,
            "winner_id": self.winner.id if self.winner else None,
        }


@dataclass
class ABTestAssignment:
    """ユーザーへのA/Bテスト割り当て"""
    user_id: str
    test_id: str
    variant_id: str
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    converted: bool = False
    converted_at: Optional[datetime] = None
    revenue: float = 0.0

    def to_dict(self) -> dict:
        """辞書に変換"""
        return {
            "user_id": self.user_id,
            "test_id": self.test_id,
            "variant_id": self.variant_id,
            "assigned_at": self.assigned_at.isoformat(),
            "converted": self.converted,
            "converted_at": self.converted_at.isoformat() if self.converted_at else None,
            "revenue": self.revenue,
        }


@dataclass
class AnalyticsEvent:
    """分析イベント"""
    id: str
    event_type: EventType
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # イベントデータ
    event_name: str = ""
    event_data: dict = field(default_factory=dict)

    # ページ情報
    page_url: str = ""
    page_title: str = ""
    referrer: str = ""

    # デバイス情報
    user_agent: str = ""
    device_type: str = ""  # desktop, mobile, tablet
    browser: str = ""
    os: str = ""

    # 地理情報
    country: str = ""
    region: str = ""
    city: str = ""

    # UTMパラメータ
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    utm_term: str = ""
    utm_content: str = ""

    # タイムスタンプ
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # 収益関連
    revenue: float = 0.0
    currency: str = "USD"

    @classmethod
    def create(
        cls,
        event_type: EventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_name: str = "",
        event_data: Optional[dict] = None,
        **kwargs
    ) -> "AnalyticsEvent":
        """イベントを作成"""
        event_id = f"evt_{secrets.token_hex(12)}"
        return cls(
            id=event_id,
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            event_name=event_name,
            event_data=event_data or {},
            **kwargs
        )

    def to_dict(self) -> dict:
        """辞書に変換"""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "event_name": self.event_name,
            "event_data": self.event_data,
            "page_url": self.page_url,
            "page_title": self.page_title,
            "referrer": self.referrer,
            "user_agent": self.user_agent,
            "device_type": self.device_type,
            "browser": self.browser,
            "os": self.os,
            "country": self.country,
            "region": self.region,
            "city": self.city,
            "utm_source": self.utm_source,
            "utm_medium": self.utm_medium,
            "utm_campaign": self.utm_campaign,
            "utm_term": self.utm_term,
            "utm_content": self.utm_content,
            "timestamp": self.timestamp.isoformat(),
            "revenue": self.revenue,
            "currency": self.currency,
        }


@dataclass
class ConversionGoal:
    """コンバージョンゴール"""
    id: str
    name: str
    description: str = ""
    goal_type: ConversionGoalType = ConversionGoalType.SUBSCRIPTION
    event_type: EventType = EventType.SUBSCRIPTION_START

    # 目標値
    target_value: float = 0.0  # 目標金額など
    target_count: int = 0      # 目標件数

    # 期間
    period_days: int = 30  # 集計期間（日数）

    # 統計
    current_value: float = 0.0
    current_count: int = 0

    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def value_progress(self) -> float:
        """目標値の達成率（%）"""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100.0)

    @property
    def count_progress(self) -> float:
        """目標件数の達成率（%）"""
        if self.target_count == 0:
            return 0.0
        return min(100.0, (self.current_count / self.target_count) * 100.0)

    def to_dict(self) -> dict:
        """辞書に変換"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "goal_type": self.goal_type.value,
            "event_type": self.event_type.value,
            "target_value": self.target_value,
            "target_count": self.target_count,
            "period_days": self.period_days,
            "current_value": self.current_value,
            "current_count": self.current_count,
            "value_progress": self.value_progress,
            "count_progress": self.count_progress,
            "created_at": self.created_at.isoformat(),
        }
