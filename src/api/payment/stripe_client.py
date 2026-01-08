# -*- coding: utf-8 -*-
"""
VisionCraftAI - Stripeクライアント

Stripe API統合を提供します。
"""

import hashlib
import hmac
import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from src.api.payment.models import (
    CREDIT_PACKAGES,
    PaymentStatus,
    PlanPrice,
    SubscriptionStatus,
)

logger = logging.getLogger(__name__)


class StripeError(Exception):
    """Stripe関連エラー"""
    pass


class StripeClient:
    """
    Stripeクライアント

    Stripe APIとの通信を管理します。
    テストモード対応で、実際のStripeライブラリなしでもモック動作可能。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        test_mode: bool = True,
    ):
        """
        初期化

        Args:
            api_key: Stripe APIキー（環境変数から取得可能）
            webhook_secret: Webhook署名シークレット
            test_mode: テストモード（実際のStripe APIを呼ばない）
        """
        self._api_key = api_key or os.environ.get("STRIPE_API_KEY", "")
        self._webhook_secret = webhook_secret or os.environ.get(
            "STRIPE_WEBHOOK_SECRET", ""
        )
        self._test_mode = test_mode

        # テストモード用のモックデータ
        self._mock_customers: dict[str, dict] = {}
        self._mock_subscriptions: dict[str, dict] = {}
        self._mock_payment_intents: dict[str, dict] = {}

        # Stripe SDK（利用可能な場合）
        self._stripe = None
        if not test_mode and self._api_key:
            try:
                import stripe
                stripe.api_key = self._api_key
                self._stripe = stripe
                logger.info("Stripe SDK初期化完了")
            except ImportError:
                logger.warning("Stripe SDKがインストールされていません")
                self._test_mode = True

    @property
    def is_configured(self) -> bool:
        """Stripeが設定済みかチェック"""
        return bool(self._api_key) or self._test_mode

    def _generate_mock_id(self, prefix: str) -> str:
        """モックID生成"""
        import secrets
        return f"{prefix}_{secrets.token_hex(12)}"

    # ========== 顧客管理 ==========

    def create_customer(
        self,
        email: str,
        name: str = "",
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Stripe顧客を作成

        Args:
            email: メールアドレス
            name: 名前
            metadata: メタデータ

        Returns:
            顧客情報
        """
        if self._test_mode:
            customer_id = self._generate_mock_id("cus_test")
            customer = {
                "id": customer_id,
                "email": email,
                "name": name,
                "metadata": metadata or {},
                "created": int(datetime.now().timestamp()),
            }
            self._mock_customers[customer_id] = customer
            logger.info(f"[MOCK] 顧客作成: {customer_id}")
            return customer

        # 実際のStripe API
        if self._stripe:
            customer = self._stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
            )
            return dict(customer)

        raise StripeError("Stripe APIが設定されていません")

    def get_customer(self, customer_id: str) -> Optional[dict]:
        """
        顧客情報を取得

        Args:
            customer_id: Stripe顧客ID

        Returns:
            顧客情報（存在しない場合はNone）
        """
        if self._test_mode:
            return self._mock_customers.get(customer_id)

        if self._stripe:
            try:
                customer = self._stripe.Customer.retrieve(customer_id)
                return dict(customer)
            except self._stripe.error.InvalidRequestError:
                return None

        raise StripeError("Stripe APIが設定されていません")

    def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        顧客情報を更新

        Args:
            customer_id: Stripe顧客ID
            email: メールアドレス
            name: 名前
            metadata: メタデータ

        Returns:
            更新後の顧客情報
        """
        if self._test_mode:
            customer = self._mock_customers.get(customer_id)
            if not customer:
                return None
            if email:
                customer["email"] = email
            if name:
                customer["name"] = name
            if metadata:
                customer["metadata"].update(metadata)
            return customer

        if self._stripe:
            params: dict[str, Any] = {}
            if email:
                params["email"] = email
            if name:
                params["name"] = name
            if metadata:
                params["metadata"] = metadata
            customer = self._stripe.Customer.modify(customer_id, **params)
            return dict(customer)

        raise StripeError("Stripe APIが設定されていません")

    # ========== サブスクリプション管理 ==========

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        サブスクリプションを作成

        Args:
            customer_id: Stripe顧客ID
            price_id: Stripe価格ID
            metadata: メタデータ

        Returns:
            サブスクリプション情報
        """
        if self._test_mode:
            sub_id = self._generate_mock_id("sub_test")
            now = datetime.now()
            subscription = {
                "id": sub_id,
                "customer": customer_id,
                "status": "active",
                "current_period_start": int(now.timestamp()),
                "current_period_end": int(now.timestamp()) + 30 * 24 * 3600,
                "cancel_at_period_end": False,
                "metadata": metadata or {},
                "items": {
                    "data": [{"price": {"id": price_id}}]
                },
            }
            self._mock_subscriptions[sub_id] = subscription
            logger.info(f"[MOCK] サブスクリプション作成: {sub_id}")
            return subscription

        if self._stripe:
            subscription = self._stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                metadata=metadata or {},
            )
            return dict(subscription)

        raise StripeError("Stripe APIが設定されていません")

    def get_subscription(self, subscription_id: str) -> Optional[dict]:
        """
        サブスクリプション情報を取得

        Args:
            subscription_id: StripeサブスクリプションID

        Returns:
            サブスクリプション情報（存在しない場合はNone）
        """
        if self._test_mode:
            return self._mock_subscriptions.get(subscription_id)

        if self._stripe:
            try:
                subscription = self._stripe.Subscription.retrieve(subscription_id)
                return dict(subscription)
            except self._stripe.error.InvalidRequestError:
                return None

        raise StripeError("Stripe APIが設定されていません")

    def update_subscription(
        self,
        subscription_id: str,
        price_id: Optional[str] = None,
        cancel_at_period_end: Optional[bool] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        サブスクリプションを更新

        Args:
            subscription_id: StripeサブスクリプションID
            price_id: 新しい価格ID（プラン変更時）
            cancel_at_period_end: 期間終了時にキャンセル
            metadata: メタデータ

        Returns:
            更新後のサブスクリプション情報
        """
        if self._test_mode:
            subscription = self._mock_subscriptions.get(subscription_id)
            if not subscription:
                return None
            if price_id:
                subscription["items"]["data"][0]["price"]["id"] = price_id
            if cancel_at_period_end is not None:
                subscription["cancel_at_period_end"] = cancel_at_period_end
            if metadata:
                subscription["metadata"].update(metadata)
            return subscription

        if self._stripe:
            params: dict[str, Any] = {}
            if price_id:
                # 既存アイテムを更新
                subscription = self._stripe.Subscription.retrieve(subscription_id)
                params["items"] = [{
                    "id": subscription["items"]["data"][0].id,
                    "price": price_id,
                }]
            if cancel_at_period_end is not None:
                params["cancel_at_period_end"] = cancel_at_period_end
            if metadata:
                params["metadata"] = metadata
            subscription = self._stripe.Subscription.modify(
                subscription_id, **params
            )
            return dict(subscription)

        raise StripeError("Stripe APIが設定されていません")

    def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False,
    ) -> Optional[dict]:
        """
        サブスクリプションをキャンセル

        Args:
            subscription_id: StripeサブスクリプションID
            immediately: 即時キャンセル（False=期間終了時）

        Returns:
            更新後のサブスクリプション情報
        """
        if self._test_mode:
            subscription = self._mock_subscriptions.get(subscription_id)
            if not subscription:
                return None
            if immediately:
                subscription["status"] = "canceled"
            else:
                subscription["cancel_at_period_end"] = True
            logger.info(f"[MOCK] サブスクリプションキャンセル: {subscription_id}")
            return subscription

        if self._stripe:
            if immediately:
                subscription = self._stripe.Subscription.delete(subscription_id)
            else:
                subscription = self._stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            return dict(subscription)

        raise StripeError("Stripe APIが設定されていません")

    # ========== 支払い処理 ==========

    def create_payment_intent(
        self,
        amount_cents: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        支払いIntentを作成（クレジット購入用）

        Args:
            amount_cents: 金額（セント単位）
            currency: 通貨コード
            customer_id: Stripe顧客ID
            metadata: メタデータ

        Returns:
            PaymentIntent情報
        """
        if self._test_mode:
            intent_id = self._generate_mock_id("pi_test")
            intent = {
                "id": intent_id,
                "amount": amount_cents,
                "currency": currency,
                "customer": customer_id,
                "status": "requires_payment_method",
                "client_secret": f"{intent_id}_secret_{self._generate_mock_id('')}",
                "metadata": metadata or {},
            }
            self._mock_payment_intents[intent_id] = intent
            logger.info(f"[MOCK] PaymentIntent作成: {intent_id}")
            return intent

        if self._stripe:
            params: dict[str, Any] = {
                "amount": amount_cents,
                "currency": currency,
                "metadata": metadata or {},
            }
            if customer_id:
                params["customer"] = customer_id
            intent = self._stripe.PaymentIntent.create(**params)
            return dict(intent)

        raise StripeError("Stripe APIが設定されていません")

    def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method: str = "pm_card_visa",
    ) -> dict:
        """
        支払いIntentを確認（テスト用）

        Args:
            payment_intent_id: PaymentIntent ID
            payment_method: 支払い方法ID

        Returns:
            更新後のPaymentIntent情報
        """
        if self._test_mode:
            intent = self._mock_payment_intents.get(payment_intent_id)
            if not intent:
                raise StripeError(f"PaymentIntent not found: {payment_intent_id}")
            intent["status"] = "succeeded"
            logger.info(f"[MOCK] PaymentIntent確認: {payment_intent_id}")
            return intent

        if self._stripe:
            intent = self._stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method=payment_method,
            )
            return dict(intent)

        raise StripeError("Stripe APIが設定されていません")

    def get_payment_intent(self, payment_intent_id: str) -> Optional[dict]:
        """
        PaymentIntent情報を取得

        Args:
            payment_intent_id: PaymentIntent ID

        Returns:
            PaymentIntent情報（存在しない場合はNone）
        """
        if self._test_mode:
            return self._mock_payment_intents.get(payment_intent_id)

        if self._stripe:
            try:
                intent = self._stripe.PaymentIntent.retrieve(payment_intent_id)
                return dict(intent)
            except self._stripe.error.InvalidRequestError:
                return None

        raise StripeError("Stripe APIが設定されていません")

    # ========== Checkout Session ==========

    def create_checkout_session(
        self,
        price_id: str,
        mode: str = "subscription",
        success_url: str = "",
        cancel_url: str = "",
        customer_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Checkout Sessionを作成

        Args:
            price_id: Stripe価格ID
            mode: モード（subscription/payment）
            success_url: 成功時リダイレクトURL
            cancel_url: キャンセル時リダイレクトURL
            customer_id: Stripe顧客ID
            metadata: メタデータ

        Returns:
            CheckoutSession情報
        """
        if self._test_mode:
            session_id = self._generate_mock_id("cs_test")
            session = {
                "id": session_id,
                "url": f"https://checkout.stripe.com/test/{session_id}",
                "mode": mode,
                "customer": customer_id,
                "metadata": metadata or {},
            }
            logger.info(f"[MOCK] CheckoutSession作成: {session_id}")
            return session

        if self._stripe:
            params: dict[str, Any] = {
                "line_items": [{"price": price_id, "quantity": 1}],
                "mode": mode,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": metadata or {},
            }
            if customer_id:
                params["customer"] = customer_id
            session = self._stripe.checkout.Session.create(**params)
            return dict(session)

        raise StripeError("Stripe APIが設定されていません")

    # ========== Webhook処理 ==========

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Webhook署名を検証

        Args:
            payload: リクエストボディ
            signature: Stripe-Signatureヘッダー

        Returns:
            検証成功かどうか
        """
        if self._test_mode:
            return True  # テストモードではスキップ

        if not self._webhook_secret:
            logger.warning("Webhookシークレットが設定されていません")
            return False

        if self._stripe:
            try:
                self._stripe.Webhook.construct_event(
                    payload, signature, self._webhook_secret
                )
                return True
            except (
                self._stripe.error.SignatureVerificationError,
                ValueError,
            ):
                return False

        # 手動検証（Stripeライブラリなし）
        return self._manual_verify_signature(payload, signature)

    def _manual_verify_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """手動で署名を検証"""
        try:
            # 署名ヘッダーをパース
            elements = dict(
                item.split("=", 1)
                for item in signature.split(",")
                if "=" in item
            )
            timestamp = elements.get("t")
            signatures = [
                v for k, v in elements.items()
                if k.startswith("v1")
            ]

            if not timestamp or not signatures:
                return False

            # 署名を計算
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_sig = hmac.new(
                self._webhook_secret.encode("utf-8"),
                signed_payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            return any(
                hmac.compare_digest(expected_sig, sig)
                for sig in signatures
            )
        except Exception as e:
            logger.error(f"署名検証エラー: {e}")
            return False

    def parse_webhook_event(self, payload: bytes) -> dict:
        """
        Webhookイベントをパース

        Args:
            payload: リクエストボディ

        Returns:
            イベントデータ
        """
        import json
        return json.loads(payload)


# シングルトンインスタンス
_client: Optional[StripeClient] = None


def get_stripe_client(test_mode: bool = True) -> StripeClient:
    """StripeClientのシングルトンを取得"""
    global _client
    if _client is None:
        _client = StripeClient(test_mode=test_mode)
    return _client
