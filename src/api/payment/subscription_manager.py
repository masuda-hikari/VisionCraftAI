# -*- coding: utf-8 -*-
"""
VisionCraftAI - サブスクリプション管理

サブスクリプションの作成、更新、キャンセルを管理します。
"""

import json
import logging
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.api.auth.key_manager import get_key_manager
from src.api.auth.models import APIKeyTier
from src.api.payment.models import (
    PlanPrice,
    Subscription,
    SubscriptionStatus,
)
from src.api.payment.stripe_client import StripeClient, get_stripe_client

logger = logging.getLogger(__name__)


# プランIDとAPIKeyTierのマッピング
PLAN_TO_TIER: dict[str, APIKeyTier] = {
    "free": APIKeyTier.FREE,
    "basic": APIKeyTier.BASIC,
    "pro": APIKeyTier.PRO,
    "enterprise": APIKeyTier.ENTERPRISE,
}


class SubscriptionManager:
    """
    サブスクリプション管理クラス

    サブスクリプションのライフサイクルを管理します。
    """

    def __init__(
        self,
        stripe_client: Optional[StripeClient] = None,
        storage_path: Optional[Path] = None,
    ):
        """
        初期化

        Args:
            stripe_client: Stripeクライアント
            storage_path: サブスクリプション保存ファイルパス
        """
        self._stripe = stripe_client or get_stripe_client()
        self._storage_path = storage_path or Path("data/subscriptions.json")
        self._subscriptions: dict[str, Subscription] = {}
        self._user_subscriptions: dict[str, str] = {}  # user_id -> subscription_id
        self._load()

    def _load(self) -> None:
        """ストレージからサブスクリプションを読み込む"""
        if not self._storage_path.exists():
            logger.info(f"サブスクリプションストレージが存在しません: {self._storage_path}")
            return

        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for sub_data in data.get("subscriptions", []):
                subscription = Subscription.from_dict(sub_data)
                self._subscriptions[subscription.subscription_id] = subscription
                if subscription.user_id:
                    self._user_subscriptions[subscription.user_id] = (
                        subscription.subscription_id
                    )

            logger.info(f"{len(self._subscriptions)}個のサブスクリプションを読み込みました")
        except Exception as e:
            logger.error(f"サブスクリプションの読み込みに失敗: {e}")

    def _save(self) -> None:
        """ストレージにサブスクリプションを保存"""
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "subscriptions": [
                    sub.to_dict()
                    for sub in self._subscriptions.values()
                ],
            }

            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"サブスクリプションを保存しました: {self._storage_path}")
        except Exception as e:
            logger.error(f"サブスクリプションの保存に失敗: {e}")
            raise

    def create_subscription(
        self,
        user_id: str,
        email: str,
        plan_id: str = "free",
        billing_interval: str = "monthly",
        api_key_id: str = "",
    ) -> tuple[Subscription, Optional[str]]:
        """
        サブスクリプションを作成

        Args:
            user_id: ユーザーID
            email: メールアドレス
            plan_id: プランID
            billing_interval: 課金間隔（monthly/yearly）
            api_key_id: 関連APIキーID

        Returns:
            tuple[Subscription, Optional[str]]: (サブスクリプション, Checkout URL)
        """
        # 既存のサブスクリプションチェック
        existing_sub_id = self._user_subscriptions.get(user_id)
        if existing_sub_id:
            existing = self._subscriptions.get(existing_sub_id)
            if existing and existing.is_active():
                raise ValueError(f"ユーザー {user_id} は既にアクティブなサブスクリプションを持っています")

        # プラン情報取得
        plans = PlanPrice.get_plans()
        if plan_id not in plans:
            raise ValueError(f"無効なプランID: {plan_id}")

        plan = plans[plan_id]
        subscription_id = f"sub_{secrets.token_hex(12)}"

        # Freeプランの場合はStripe不要
        if plan_id == "free":
            subscription = Subscription(
                subscription_id=subscription_id,
                user_id=user_id,
                api_key_id=api_key_id,
                plan_id=plan_id,
                billing_interval=billing_interval,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=datetime.now().isoformat(),
            )

            self._subscriptions[subscription_id] = subscription
            self._user_subscriptions[user_id] = subscription_id
            self._save()

            # APIキーのプラン更新
            self._update_api_key_tier(api_key_id, plan_id)

            logger.info(f"Freeサブスクリプション作成: {subscription_id}")
            return subscription, None

        # 有料プラン：Stripe顧客作成
        customer = self._stripe.create_customer(
            email=email,
            metadata={"user_id": user_id},
        )

        # Checkout Session作成
        price_id = (
            plan.stripe_price_id_yearly
            if billing_interval == "yearly"
            else plan.stripe_price_id_monthly
        )

        # テストモードでは仮の価格IDを使用
        if not price_id:
            price_id = f"price_{plan_id}_{billing_interval}_test"

        session = self._stripe.create_checkout_session(
            price_id=price_id,
            mode="subscription",
            customer_id=customer["id"],
            success_url="http://localhost:8000/api/v1/payment/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/api/v1/payment/cancel",
            metadata={
                "user_id": user_id,
                "api_key_id": api_key_id,
                "plan_id": plan_id,
            },
        )

        # サブスクリプションをpending状態で作成
        subscription = Subscription(
            subscription_id=subscription_id,
            stripe_customer_id=customer["id"],
            user_id=user_id,
            api_key_id=api_key_id,
            plan_id=plan_id,
            billing_interval=billing_interval,
            status=SubscriptionStatus.INCOMPLETE,
        )

        self._subscriptions[subscription_id] = subscription
        self._user_subscriptions[user_id] = subscription_id
        self._save()

        logger.info(f"有料サブスクリプション作成開始: {subscription_id}")
        return subscription, session.get("url")

    def activate_subscription(
        self,
        subscription_id: str,
        stripe_subscription_id: str,
    ) -> Optional[Subscription]:
        """
        サブスクリプションをアクティベート（Webhook経由で呼び出し）

        Args:
            subscription_id: サブスクリプションID
            stripe_subscription_id: StripeサブスクリプションID

        Returns:
            更新後のサブスクリプション
        """
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            logger.warning(f"サブスクリプションが見つかりません: {subscription_id}")
            return None

        # Stripeサブスクリプション情報取得
        stripe_sub = self._stripe.get_subscription(stripe_subscription_id)
        if not stripe_sub:
            logger.warning(f"Stripeサブスクリプションが見つかりません: {stripe_subscription_id}")
            return None

        # 更新
        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_sub["current_period_start"]
        ).isoformat()
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_sub["current_period_end"]
        ).isoformat()
        subscription.updated_at = datetime.now().isoformat()

        self._save()

        # APIキーのプラン更新
        self._update_api_key_tier(subscription.api_key_id, subscription.plan_id)

        logger.info(f"サブスクリプションアクティベート: {subscription_id}")
        return subscription

    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """
        サブスクリプションを取得

        Args:
            subscription_id: サブスクリプションID

        Returns:
            サブスクリプション（存在しない場合はNone）
        """
        return self._subscriptions.get(subscription_id)

    def get_subscription_by_user(self, user_id: str) -> Optional[Subscription]:
        """
        ユーザーIDでサブスクリプションを取得

        Args:
            user_id: ユーザーID

        Returns:
            サブスクリプション（存在しない場合はNone）
        """
        sub_id = self._user_subscriptions.get(user_id)
        if sub_id:
            return self._subscriptions.get(sub_id)
        return None

    def get_subscription_by_api_key(self, api_key_id: str) -> Optional[Subscription]:
        """
        APIキーIDでサブスクリプションを取得

        Args:
            api_key_id: APIキーID

        Returns:
            サブスクリプション（存在しない場合はNone）
        """
        for subscription in self._subscriptions.values():
            if subscription.api_key_id == api_key_id:
                return subscription
        return None

    def update_subscription_plan(
        self,
        subscription_id: str,
        new_plan_id: str,
    ) -> Optional[Subscription]:
        """
        サブスクリプションプランを変更

        Args:
            subscription_id: サブスクリプションID
            new_plan_id: 新しいプランID

        Returns:
            更新後のサブスクリプション
        """
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None

        plans = PlanPrice.get_plans()
        if new_plan_id not in plans:
            raise ValueError(f"無効なプランID: {new_plan_id}")

        old_plan_id = subscription.plan_id

        # Stripeサブスクリプション更新（有料→有料の場合）
        if subscription.stripe_subscription_id and new_plan_id != "free":
            new_plan = plans[new_plan_id]
            price_id = (
                new_plan.stripe_price_id_yearly
                if subscription.billing_interval == "yearly"
                else new_plan.stripe_price_id_monthly
            )
            if not price_id:
                price_id = f"price_{new_plan_id}_{subscription.billing_interval}_test"

            self._stripe.update_subscription(
                subscription.stripe_subscription_id,
                price_id=price_id,
            )

        subscription.plan_id = new_plan_id
        subscription.updated_at = datetime.now().isoformat()
        self._save()

        # APIキーのプラン更新
        self._update_api_key_tier(subscription.api_key_id, new_plan_id)

        logger.info(f"プラン変更: {subscription_id} ({old_plan_id} -> {new_plan_id})")
        return subscription

    def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False,
    ) -> Optional[Subscription]:
        """
        サブスクリプションをキャンセル

        Args:
            subscription_id: サブスクリプションID
            immediately: 即時キャンセル（False=期間終了時）

        Returns:
            更新後のサブスクリプション
        """
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None

        # Stripeサブスクリプションキャンセル
        if subscription.stripe_subscription_id:
            self._stripe.cancel_subscription(
                subscription.stripe_subscription_id,
                immediately=immediately,
            )

        if immediately:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.now().isoformat()
            # APIキーをFreeにダウングレード
            self._update_api_key_tier(subscription.api_key_id, "free")
        else:
            subscription.cancel_at_period_end = True

        subscription.updated_at = datetime.now().isoformat()
        self._save()

        logger.info(f"サブスクリプションキャンセル: {subscription_id} (immediately={immediately})")
        return subscription

    def handle_subscription_updated(
        self,
        stripe_subscription_id: str,
        status: str,
        current_period_end: int,
    ) -> Optional[Subscription]:
        """
        サブスクリプション更新イベントを処理（Webhook用）

        Args:
            stripe_subscription_id: StripeサブスクリプションID
            status: Stripeステータス
            current_period_end: 現在の期間終了タイムスタンプ

        Returns:
            更新後のサブスクリプション
        """
        # サブスクリプションを検索
        subscription = None
        for sub in self._subscriptions.values():
            if sub.stripe_subscription_id == stripe_subscription_id:
                subscription = sub
                break

        if not subscription:
            logger.warning(f"サブスクリプションが見つかりません: {stripe_subscription_id}")
            return None

        # ステータスマッピング
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "trialing": SubscriptionStatus.TRIALING,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "unpaid": SubscriptionStatus.UNPAID,
            "incomplete": SubscriptionStatus.INCOMPLETE,
        }

        subscription.status = status_map.get(status, SubscriptionStatus.ACTIVE)
        subscription.current_period_end = datetime.fromtimestamp(
            current_period_end
        ).isoformat()
        subscription.updated_at = datetime.now().isoformat()

        # キャンセルの場合はAPIキーをダウングレード
        if subscription.status == SubscriptionStatus.CANCELED:
            subscription.canceled_at = datetime.now().isoformat()
            self._update_api_key_tier(subscription.api_key_id, "free")

        self._save()
        logger.info(f"サブスクリプション更新: {subscription.subscription_id} (status={status})")
        return subscription

    def _update_api_key_tier(self, api_key_id: str, plan_id: str) -> None:
        """APIキーのプラン階層を更新"""
        if not api_key_id:
            return

        tier = PLAN_TO_TIER.get(plan_id, APIKeyTier.FREE)
        key_manager = get_key_manager()
        key_manager.update_key(api_key_id, tier=tier)
        logger.debug(f"APIキー {api_key_id} のプランを {tier.value} に更新")

    def list_subscriptions(
        self,
        user_id: Optional[str] = None,
        status: Optional[SubscriptionStatus] = None,
    ) -> list[Subscription]:
        """
        サブスクリプション一覧を取得

        Args:
            user_id: ユーザーIDでフィルタ
            status: ステータスでフィルタ

        Returns:
            サブスクリプションリスト
        """
        subscriptions = list(self._subscriptions.values())

        if user_id:
            subscriptions = [s for s in subscriptions if s.user_id == user_id]

        if status:
            subscriptions = [s for s in subscriptions if s.status == status]

        return subscriptions


# シングルトンインスタンス
_manager: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    """SubscriptionManagerのシングルトンを取得"""
    global _manager
    if _manager is None:
        _manager = SubscriptionManager()
    return _manager
