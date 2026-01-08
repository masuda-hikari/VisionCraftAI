# -*- coding: utf-8 -*-
"""
VisionCraftAI - 決済スキーマ定義

決済関連のPydanticスキーマを定義します。
"""

from typing import Optional

from pydantic import BaseModel, Field


# ========== サブスクリプション ==========


class SubscriptionCreateRequest(BaseModel):
    """サブスクリプション作成リクエスト"""
    email: str = Field(..., description="メールアドレス")
    plan_id: str = Field(default="free", description="プランID (free/basic/pro/enterprise)")
    billing_interval: str = Field(default="monthly", description="課金間隔 (monthly/yearly)")


class SubscriptionUpdateRequest(BaseModel):
    """サブスクリプション更新リクエスト"""
    plan_id: str = Field(..., description="新しいプランID")


class SubscriptionCancelRequest(BaseModel):
    """サブスクリプションキャンセルリクエスト"""
    immediately: bool = Field(default=False, description="即時キャンセル")


class SubscriptionResponse(BaseModel):
    """サブスクリプションレスポンス"""
    subscription_id: str
    plan_id: str
    billing_interval: str
    status: str
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    checkout_url: Optional[str] = None


class SubscriptionStatusResponse(BaseModel):
    """サブスクリプションステータスレスポンス"""
    subscription_id: str
    plan_id: str
    plan_name: str
    status: str
    is_active: bool
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    credits_included: int


# ========== クレジット ==========


class CreditPackage(BaseModel):
    """クレジットパッケージ"""
    package_id: str
    credits: int
    bonus_credits: int
    total_credits: int
    price_usd: str
    description: str


class CreditPackagesResponse(BaseModel):
    """クレジットパッケージ一覧レスポンス"""
    packages: dict[str, CreditPackage]


class CreditPurchaseRequest(BaseModel):
    """クレジット購入リクエスト"""
    package_id: str = Field(..., description="パッケージID")


class CreditPurchaseResponse(BaseModel):
    """クレジット購入レスポンス"""
    payment_intent_id: str
    client_secret: str
    amount_usd: str
    credits: int
    bonus_credits: int
    total_credits: int


class CreditBalanceResponse(BaseModel):
    """クレジット残高レスポンス"""
    balance: int
    bonus_balance: int
    total_balance: int
    total_purchased: int
    total_used: int


class CreditTransactionResponse(BaseModel):
    """クレジット取引レスポンス"""
    transaction_id: str
    transaction_type: str
    amount: int
    balance_after: int
    price_usd: Optional[str] = None
    description: str
    created_at: str


class CreditTransactionsResponse(BaseModel):
    """クレジット取引一覧レスポンス"""
    transactions: list[CreditTransactionResponse]
    total: int


# ========== Webhook ==========


class WebhookResponse(BaseModel):
    """Webhookレスポンス"""
    received: bool = True
    message: str = ""


# ========== プラン ==========


class PlanInfo(BaseModel):
    """プラン情報"""
    plan_id: str
    name: str
    description: str
    price_monthly: str
    price_yearly: str
    credits_included: int
    features: list[str]


class PlansResponse(BaseModel):
    """プラン一覧レスポンス"""
    plans: list[PlanInfo]


# ========== 共通 ==========


class PaymentErrorResponse(BaseModel):
    """決済エラーレスポンス"""
    error: str
    code: str
    detail: Optional[str] = None
