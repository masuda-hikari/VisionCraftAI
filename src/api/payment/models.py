# -*- coding: utf-8 -*-
"""
VisionCraftAI - 決済モデル定義

サブスクリプション、クレジット、取引のデータモデルを定義します。
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    """決済ステータス"""
    PENDING = "pending"          # 処理中
    SUCCEEDED = "succeeded"      # 成功
    FAILED = "failed"            # 失敗
    CANCELED = "canceled"        # キャンセル
    REFUNDED = "refunded"        # 返金済み


class SubscriptionStatus(str, Enum):
    """サブスクリプションステータス"""
    ACTIVE = "active"            # アクティブ
    TRIALING = "trialing"        # トライアル中
    PAST_DUE = "past_due"        # 支払い遅延
    CANCELED = "canceled"        # キャンセル
    UNPAID = "unpaid"            # 未払い
    INCOMPLETE = "incomplete"    # 不完全


class TransactionType(str, Enum):
    """取引タイプ"""
    SUBSCRIPTION = "subscription"    # サブスクリプション支払い
    CREDIT_PURCHASE = "credit_purchase"  # クレジット購入
    CREDIT_USAGE = "credit_usage"    # クレジット使用
    CREDIT_REFUND = "credit_refund"  # クレジット返金
    CREDIT_BONUS = "credit_bonus"    # ボーナスクレジット


@dataclass
class PlanPrice:
    """プラン価格設定"""
    plan_id: str                     # プランID (free, basic, pro, enterprise)
    name: str                        # プラン名
    description: str                 # 説明
    price_monthly: Decimal           # 月額価格（USD）
    price_yearly: Decimal            # 年額価格（USD）
    stripe_price_id_monthly: str = ""  # Stripe月額価格ID
    stripe_price_id_yearly: str = ""   # Stripe年額価格ID
    credits_included: int = 0        # 含まれるクレジット数
    features: list[str] = field(default_factory=list)  # 機能リスト

    @classmethod
    def get_plans(cls) -> dict[str, "PlanPrice"]:
        """全プラン価格を取得"""
        return {
            "free": cls(
                plan_id="free",
                name="Free",
                description="無料プラン - 月5枚まで",
                price_monthly=Decimal("0"),
                price_yearly=Decimal("0"),
                credits_included=5,
                features=[
                    "月5枚の画像生成",
                    "最大512x512解像度",
                    "標準処理速度",
                ],
            ),
            "basic": cls(
                plan_id="basic",
                name="Basic",
                description="ベーシックプラン - 月100枚",
                price_monthly=Decimal("9.99"),
                price_yearly=Decimal("99.99"),  # 2ヶ月分お得
                credits_included=100,
                features=[
                    "月100枚の画像生成",
                    "最大1024x1024解像度",
                    "バッチ処理（10枚まで）",
                    "メールサポート",
                ],
            ),
            "pro": cls(
                plan_id="pro",
                name="Pro",
                description="プロプラン - 月500枚、優先処理",
                price_monthly=Decimal("29.99"),
                price_yearly=Decimal("299.99"),  # 2ヶ月分お得
                credits_included=500,
                features=[
                    "月500枚の画像生成",
                    "最大2048x2048解像度",
                    "バッチ処理（50枚まで）",
                    "優先処理",
                    "優先サポート",
                ],
            ),
            "enterprise": cls(
                plan_id="enterprise",
                name="Enterprise",
                description="エンタープライズ - 無制限、カスタム",
                price_monthly=Decimal("99.99"),
                price_yearly=Decimal("999.99"),
                credits_included=10000,  # 無制限相当
                features=[
                    "無制限の画像生成",
                    "最大4096x4096解像度",
                    "バッチ処理（100枚まで）",
                    "最優先処理",
                    "専用サポート",
                    "SLA保証",
                    "カスタム統合",
                ],
            ),
        }


@dataclass
class Subscription:
    """サブスクリプション"""
    subscription_id: str             # 内部サブスクリプションID
    stripe_subscription_id: str = "" # StripeサブスクリプションID
    stripe_customer_id: str = ""     # Stripe顧客ID

    # ユーザー情報
    user_id: str = ""                # ユーザーID
    api_key_id: str = ""             # 関連APIキーID

    # プラン情報
    plan_id: str = "free"            # プランID
    billing_interval: str = "monthly"  # monthly or yearly

    # ステータス
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE

    # 期間
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False

    # 日時
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    canceled_at: Optional[str] = None

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "subscription_id": self.subscription_id,
            "stripe_subscription_id": self.stripe_subscription_id,
            "stripe_customer_id": self.stripe_customer_id,
            "user_id": self.user_id,
            "api_key_id": self.api_key_id,
            "plan_id": self.plan_id,
            "billing_interval": self.billing_interval,
            "status": self.status.value,
            "current_period_start": self.current_period_start,
            "current_period_end": self.current_period_end,
            "cancel_at_period_end": self.cancel_at_period_end,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "canceled_at": self.canceled_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Subscription":
        """辞書からインスタンスを作成"""
        return cls(
            subscription_id=data["subscription_id"],
            stripe_subscription_id=data.get("stripe_subscription_id", ""),
            stripe_customer_id=data.get("stripe_customer_id", ""),
            user_id=data.get("user_id", ""),
            api_key_id=data.get("api_key_id", ""),
            plan_id=data.get("plan_id", "free"),
            billing_interval=data.get("billing_interval", "monthly"),
            status=SubscriptionStatus(data.get("status", "active")),
            current_period_start=data.get("current_period_start"),
            current_period_end=data.get("current_period_end"),
            cancel_at_period_end=data.get("cancel_at_period_end", False),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            canceled_at=data.get("canceled_at"),
        )

    def is_active(self) -> bool:
        """アクティブな状態かチェック"""
        return self.status in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        )


@dataclass
class CreditBalance:
    """クレジット残高"""
    user_id: str                     # ユーザーID
    api_key_id: str = ""             # 関連APIキーID

    # 残高
    balance: int = 0                 # 現在の残高（クレジット数）
    bonus_balance: int = 0           # ボーナス残高

    # 累計
    total_purchased: int = 0         # 累計購入数
    total_used: int = 0              # 累計使用数
    total_bonus_received: int = 0    # 累計ボーナス受取数

    # 有効期限（ボーナスのみ）
    bonus_expires_at: Optional[str] = None

    # 日時
    updated_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def get_total_balance(self) -> int:
        """総残高を取得（通常 + ボーナス）"""
        # ボーナス有効期限チェック
        if self.bonus_expires_at:
            if datetime.fromisoformat(self.bonus_expires_at) < datetime.now():
                return self.balance
        return self.balance + self.bonus_balance

    def can_use(self, amount: int) -> bool:
        """使用可能かチェック"""
        return self.get_total_balance() >= amount

    def use_credits(self, amount: int) -> bool:
        """
        クレジットを使用

        ボーナス残高を優先的に消費
        """
        if not self.can_use(amount):
            return False

        # ボーナスから優先消費
        if self.bonus_balance > 0:
            bonus_use = min(self.bonus_balance, amount)
            self.bonus_balance -= bonus_use
            amount -= bonus_use

        # 残りは通常残高から
        if amount > 0:
            self.balance -= amount

        self.total_used += amount
        self.updated_at = datetime.now().isoformat()
        return True

    def add_credits(self, amount: int, is_bonus: bool = False) -> None:
        """クレジットを追加"""
        if is_bonus:
            self.bonus_balance += amount
            self.total_bonus_received += amount
        else:
            self.balance += amount
            self.total_purchased += amount
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "user_id": self.user_id,
            "api_key_id": self.api_key_id,
            "balance": self.balance,
            "bonus_balance": self.bonus_balance,
            "total_balance": self.get_total_balance(),
            "total_purchased": self.total_purchased,
            "total_used": self.total_used,
            "total_bonus_received": self.total_bonus_received,
            "bonus_expires_at": self.bonus_expires_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CreditBalance":
        """辞書からインスタンスを作成"""
        return cls(
            user_id=data["user_id"],
            api_key_id=data.get("api_key_id", ""),
            balance=data.get("balance", 0),
            bonus_balance=data.get("bonus_balance", 0),
            total_purchased=data.get("total_purchased", 0),
            total_used=data.get("total_used", 0),
            total_bonus_received=data.get("total_bonus_received", 0),
            bonus_expires_at=data.get("bonus_expires_at"),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )


@dataclass
class CreditTransaction:
    """クレジット取引"""
    transaction_id: str              # 取引ID
    user_id: str                     # ユーザーID

    # 取引内容
    transaction_type: TransactionType
    amount: int                      # クレジット数（正: 追加、負: 消費）
    balance_after: int               # 取引後残高

    # 決済情報（購入時）
    stripe_payment_intent_id: str = ""
    price_usd: Decimal = Decimal("0")

    # 参照
    reference_id: str = ""           # 参照ID（画像生成ID等）
    description: str = ""            # 説明

    # 日時
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "transaction_type": self.transaction_type.value,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "price_usd": str(self.price_usd),
            "reference_id": self.reference_id,
            "description": self.description,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CreditTransaction":
        """辞書からインスタンスを作成"""
        return cls(
            transaction_id=data["transaction_id"],
            user_id=data["user_id"],
            transaction_type=TransactionType(data["transaction_type"]),
            amount=data["amount"],
            balance_after=data["balance_after"],
            stripe_payment_intent_id=data.get("stripe_payment_intent_id", ""),
            price_usd=Decimal(data.get("price_usd", "0")),
            reference_id=data.get("reference_id", ""),
            description=data.get("description", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


# クレジット価格設定
CREDIT_PACKAGES = {
    "credits_10": {
        "credits": 10,
        "price_usd": Decimal("4.99"),
        "bonus_credits": 0,
        "description": "10クレジット",
    },
    "credits_50": {
        "credits": 50,
        "price_usd": Decimal("19.99"),
        "bonus_credits": 5,  # 10%ボーナス
        "description": "50クレジット（+5ボーナス）",
    },
    "credits_100": {
        "credits": 100,
        "price_usd": Decimal("34.99"),
        "bonus_credits": 15,  # 15%ボーナス
        "description": "100クレジット（+15ボーナス）",
    },
    "credits_500": {
        "credits": 500,
        "price_usd": Decimal("149.99"),
        "bonus_credits": 100,  # 20%ボーナス
        "description": "500クレジット（+100ボーナス）",
    },
}
