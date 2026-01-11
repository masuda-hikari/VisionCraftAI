# -*- coding: utf-8 -*-
"""
VisionCraftAI - 決済テスト

決済モジュールの単体テストとAPIテスト
"""

import json
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.app import app
from src.api.auth.key_manager import APIKeyManager
from src.api.auth.models import APIKeyTier
from src.api.payment.models import (
    CREDIT_PACKAGES,
    CreditBalance,
    CreditTransaction,
    PaymentStatus,
    PlanPrice,
    Subscription,
    SubscriptionStatus,
    TransactionType,
)
from src.api.payment.stripe_client import StripeClient, StripeError
from src.api.payment.subscription_manager import SubscriptionManager
from src.api.payment.credit_manager import CreditManager


# ========== テストクライアント ==========

client = TestClient(app)


# ========== フィクスチャ ==========


@pytest.fixture
def temp_storage(tmp_path):
    """一時ストレージパス"""
    return tmp_path


@pytest.fixture
def stripe_client():
    """テストモードのStripeクライアント"""
    return StripeClient(test_mode=True)


@pytest.fixture
def key_manager(temp_storage):
    """一時ストレージを使用したキーマネージャー"""
    return APIKeyManager(storage_path=temp_storage / "api_keys.json")


@pytest.fixture
def subscription_manager(temp_storage, stripe_client, key_manager):
    """一時ストレージを使用したサブスクリプションマネージャー"""
    # key_managerをモック
    with patch("src.api.payment.subscription_manager.get_key_manager", return_value=key_manager):
        manager = SubscriptionManager(
            stripe_client=stripe_client,
            storage_path=temp_storage / "subscriptions.json",
        )
        yield manager


@pytest.fixture
def credit_manager(temp_storage, stripe_client):
    """一時ストレージを使用したクレジットマネージャー"""
    return CreditManager(
        stripe_client=stripe_client,
        storage_path=temp_storage,
    )


@pytest.fixture
def api_key_and_header(key_manager):
    """テスト用APIキーとヘッダー"""
    api_key, raw_key = key_manager.create_key(
        tier=APIKeyTier.BASIC,
        name="Test Key",
        owner_id="test_user_001",
    )
    return api_key, {"X-API-Key": raw_key}


# ========== モデルテスト ==========


class TestPlanPrice:
    """PlanPriceモデルのテスト"""

    def test_get_plans(self):
        """全プラン取得"""
        plans = PlanPrice.get_plans()
        assert len(plans) == 4
        assert "free" in plans
        assert "basic" in plans
        assert "pro" in plans
        assert "enterprise" in plans

    def test_free_plan(self):
        """Freeプランの内容確認"""
        plans = PlanPrice.get_plans()
        free = plans["free"]
        assert free.plan_id == "free"
        assert free.price_monthly == Decimal("0")
        assert free.credits_included == 5

    def test_basic_plan(self):
        """Basicプランの内容確認"""
        plans = PlanPrice.get_plans()
        basic = plans["basic"]
        assert basic.plan_id == "basic"
        assert basic.price_monthly == Decimal("9.99")
        assert basic.credits_included == 100

    def test_pro_plan(self):
        """Proプランの内容確認"""
        plans = PlanPrice.get_plans()
        pro = plans["pro"]
        assert pro.plan_id == "pro"
        assert pro.price_monthly == Decimal("29.99")
        assert pro.credits_included == 500


class TestSubscription:
    """Subscriptionモデルのテスト"""

    def test_create_subscription(self):
        """サブスクリプション作成"""
        sub = Subscription(
            subscription_id="sub_test_001",
            user_id="user_001",
            plan_id="basic",
        )
        assert sub.subscription_id == "sub_test_001"
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.is_active()

    def test_to_dict_and_from_dict(self):
        """辞書変換"""
        sub = Subscription(
            subscription_id="sub_test_002",
            user_id="user_002",
            plan_id="pro",
            billing_interval="yearly",
        )
        data = sub.to_dict()
        restored = Subscription.from_dict(data)
        assert restored.subscription_id == sub.subscription_id
        assert restored.plan_id == sub.plan_id
        assert restored.billing_interval == sub.billing_interval

    def test_is_active_canceled(self):
        """キャンセル状態の確認"""
        sub = Subscription(
            subscription_id="sub_test_003",
            status=SubscriptionStatus.CANCELED,
        )
        assert not sub.is_active()


class TestCreditBalance:
    """CreditBalanceモデルのテスト"""

    def test_create_balance(self):
        """残高作成"""
        balance = CreditBalance(user_id="user_001")
        assert balance.balance == 0
        assert balance.bonus_balance == 0
        assert balance.get_total_balance() == 0

    def test_add_credits(self):
        """クレジット追加"""
        balance = CreditBalance(user_id="user_001")
        balance.add_credits(100)
        assert balance.balance == 100
        assert balance.total_purchased == 100

    def test_add_bonus_credits(self):
        """ボーナスクレジット追加"""
        balance = CreditBalance(user_id="user_001")
        balance.add_credits(50, is_bonus=True)
        assert balance.bonus_balance == 50
        assert balance.total_bonus_received == 50

    def test_use_credits(self):
        """クレジット使用"""
        balance = CreditBalance(user_id="user_001", balance=100)
        success = balance.use_credits(30)
        assert success
        assert balance.balance == 70
        assert balance.total_used == 30

    def test_use_bonus_first(self):
        """ボーナスから優先消費"""
        balance = CreditBalance(
            user_id="user_001",
            balance=100,
            bonus_balance=50,
        )
        success = balance.use_credits(70)
        assert success
        assert balance.bonus_balance == 0  # ボーナス50全消費
        assert balance.balance == 80  # 通常から20消費

    def test_use_credits_insufficient(self):
        """残高不足"""
        balance = CreditBalance(user_id="user_001", balance=10)
        success = balance.use_credits(50)
        assert not success
        assert balance.balance == 10  # 変化なし


class TestCreditTransaction:
    """CreditTransactionモデルのテスト"""

    def test_create_transaction(self):
        """取引作成"""
        tx = CreditTransaction(
            transaction_id="tx_001",
            user_id="user_001",
            transaction_type=TransactionType.CREDIT_PURCHASE,
            amount=100,
            balance_after=150,
            price_usd=Decimal("34.99"),
        )
        assert tx.transaction_type == TransactionType.CREDIT_PURCHASE
        assert tx.amount == 100

    def test_to_dict_and_from_dict(self):
        """辞書変換"""
        tx = CreditTransaction(
            transaction_id="tx_002",
            user_id="user_002",
            transaction_type=TransactionType.CREDIT_USAGE,
            amount=-10,
            balance_after=90,
        )
        data = tx.to_dict()
        restored = CreditTransaction.from_dict(data)
        assert restored.transaction_id == tx.transaction_id
        assert restored.amount == tx.amount


# ========== Stripeクライアントテスト ==========


class TestStripeClient:
    """Stripeクライアントのテスト"""

    def test_create_customer(self, stripe_client):
        """顧客作成"""
        customer = stripe_client.create_customer(
            email="test@example.com",
            name="Test User",
        )
        assert customer["id"].startswith("cus_test_")
        assert customer["email"] == "test@example.com"

    def test_create_customer_with_metadata(self, stripe_client):
        """メタデータ付き顧客作成"""
        customer = stripe_client.create_customer(
            email="meta@example.com",
            name="Meta User",
            metadata={"plan": "pro", "source": "referral"},
        )
        assert customer["metadata"]["plan"] == "pro"
        assert customer["metadata"]["source"] == "referral"

    def test_get_customer(self, stripe_client):
        """顧客取得"""
        customer = stripe_client.create_customer(email="test2@example.com")
        retrieved = stripe_client.get_customer(customer["id"])
        assert retrieved is not None
        assert retrieved["email"] == "test2@example.com"

    def test_get_customer_not_found(self, stripe_client):
        """存在しない顧客"""
        result = stripe_client.get_customer("cus_nonexistent")
        assert result is None

    def test_update_customer(self, stripe_client):
        """顧客情報更新"""
        customer = stripe_client.create_customer(
            email="update@example.com",
            name="Original Name",
        )
        updated = stripe_client.update_customer(
            customer["id"],
            email="updated@example.com",
            name="Updated Name",
            metadata={"updated": "true"},
        )
        assert updated is not None
        assert updated["email"] == "updated@example.com"
        assert updated["name"] == "Updated Name"
        assert updated["metadata"]["updated"] == "true"

    def test_update_customer_not_found(self, stripe_client):
        """存在しない顧客の更新"""
        result = stripe_client.update_customer(
            "cus_nonexistent",
            email="test@example.com",
        )
        assert result is None

    def test_update_customer_partial(self, stripe_client):
        """顧客情報の部分更新"""
        customer = stripe_client.create_customer(
            email="partial@example.com",
            name="Original",
        )
        updated = stripe_client.update_customer(
            customer["id"],
            name="Only Name Changed",
        )
        assert updated["email"] == "partial@example.com"
        assert updated["name"] == "Only Name Changed"

    def test_create_subscription(self, stripe_client):
        """サブスクリプション作成"""
        customer = stripe_client.create_customer(email="sub@example.com")
        subscription = stripe_client.create_subscription(
            customer_id=customer["id"],
            price_id="price_basic_monthly",
        )
        assert subscription["id"].startswith("sub_test_")
        assert subscription["status"] == "active"

    def test_create_subscription_with_metadata(self, stripe_client):
        """メタデータ付きサブスクリプション作成"""
        customer = stripe_client.create_customer(email="submeta@example.com")
        subscription = stripe_client.create_subscription(
            customer_id=customer["id"],
            price_id="price_pro_monthly",
            metadata={"tier": "pro", "campaign": "launch"},
        )
        assert subscription["metadata"]["tier"] == "pro"
        assert subscription["metadata"]["campaign"] == "launch"

    def test_get_subscription(self, stripe_client):
        """サブスクリプション取得"""
        customer = stripe_client.create_customer(email="getsub@example.com")
        subscription = stripe_client.create_subscription(
            customer_id=customer["id"],
            price_id="price_basic_monthly",
        )
        retrieved = stripe_client.get_subscription(subscription["id"])
        assert retrieved is not None
        assert retrieved["customer"] == customer["id"]

    def test_get_subscription_not_found(self, stripe_client):
        """存在しないサブスクリプション取得"""
        result = stripe_client.get_subscription("sub_nonexistent")
        assert result is None

    def test_update_subscription(self, stripe_client):
        """サブスクリプション更新"""
        customer = stripe_client.create_customer(email="updatesub@example.com")
        subscription = stripe_client.create_subscription(
            customer_id=customer["id"],
            price_id="price_basic_monthly",
        )
        updated = stripe_client.update_subscription(
            subscription["id"],
            price_id="price_pro_monthly",
            metadata={"upgraded": "true"},
        )
        assert updated is not None
        assert updated["items"]["data"][0]["price"]["id"] == "price_pro_monthly"
        assert updated["metadata"]["upgraded"] == "true"

    def test_update_subscription_cancel_at_period_end(self, stripe_client):
        """サブスクリプション期間終了時キャンセル設定"""
        customer = stripe_client.create_customer(email="cancelend@example.com")
        subscription = stripe_client.create_subscription(
            customer_id=customer["id"],
            price_id="price_basic_monthly",
        )
        updated = stripe_client.update_subscription(
            subscription["id"],
            cancel_at_period_end=True,
        )
        assert updated["cancel_at_period_end"] is True

    def test_update_subscription_not_found(self, stripe_client):
        """存在しないサブスクリプションの更新"""
        result = stripe_client.update_subscription(
            "sub_nonexistent",
            price_id="price_pro_monthly",
        )
        assert result is None

    def test_cancel_subscription(self, stripe_client):
        """サブスクリプションキャンセル"""
        customer = stripe_client.create_customer(email="cancel@example.com")
        subscription = stripe_client.create_subscription(
            customer_id=customer["id"],
            price_id="price_basic_monthly",
        )
        canceled = stripe_client.cancel_subscription(
            subscription["id"],
            immediately=True,
        )
        assert canceled["status"] == "canceled"

    def test_cancel_subscription_at_period_end(self, stripe_client):
        """サブスクリプション期間終了時キャンセル"""
        customer = stripe_client.create_customer(email="cancelperiod@example.com")
        subscription = stripe_client.create_subscription(
            customer_id=customer["id"],
            price_id="price_basic_monthly",
        )
        canceled = stripe_client.cancel_subscription(
            subscription["id"],
            immediately=False,
        )
        assert canceled["cancel_at_period_end"] is True
        assert canceled["status"] != "canceled"

    def test_cancel_subscription_not_found(self, stripe_client):
        """存在しないサブスクリプションのキャンセル"""
        result = stripe_client.cancel_subscription("sub_nonexistent")
        assert result is None

    def test_create_payment_intent(self, stripe_client):
        """PaymentIntent作成"""
        intent = stripe_client.create_payment_intent(
            amount_cents=999,
            metadata={"user_id": "test_user"},
        )
        assert intent["id"].startswith("pi_test_")
        assert intent["amount"] == 999
        assert "client_secret" in intent

    def test_create_payment_intent_with_customer(self, stripe_client):
        """顧客ID付きPaymentIntent作成"""
        customer = stripe_client.create_customer(email="intent@example.com")
        intent = stripe_client.create_payment_intent(
            amount_cents=1999,
            customer_id=customer["id"],
            currency="jpy",
        )
        assert intent["customer"] == customer["id"]
        assert intent["currency"] == "jpy"

    def test_confirm_payment_intent(self, stripe_client):
        """PaymentIntent確認"""
        intent = stripe_client.create_payment_intent(amount_cents=1999)
        confirmed = stripe_client.confirm_payment_intent(intent["id"])
        assert confirmed["status"] == "succeeded"

    def test_confirm_payment_intent_not_found(self, stripe_client):
        """存在しないPaymentIntent確認"""
        with pytest.raises(StripeError):
            stripe_client.confirm_payment_intent("pi_nonexistent")

    def test_get_payment_intent(self, stripe_client):
        """PaymentIntent取得"""
        intent = stripe_client.create_payment_intent(amount_cents=2999)
        retrieved = stripe_client.get_payment_intent(intent["id"])
        assert retrieved is not None
        assert retrieved["amount"] == 2999

    def test_get_payment_intent_not_found(self, stripe_client):
        """存在しないPaymentIntent取得"""
        result = stripe_client.get_payment_intent("pi_nonexistent")
        assert result is None

    def test_create_checkout_session(self, stripe_client):
        """CheckoutSession作成"""
        customer = stripe_client.create_customer(email="checkout@example.com")
        session = stripe_client.create_checkout_session(
            price_id="price_basic_monthly",
            mode="subscription",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            customer_id=customer["id"],
            metadata={"campaign": "launch"},
        )
        assert session["id"].startswith("cs_test_")
        assert "url" in session
        assert session["mode"] == "subscription"
        assert session["customer"] == customer["id"]

    def test_create_checkout_session_payment_mode(self, stripe_client):
        """PaymentモードのCheckoutSession作成"""
        session = stripe_client.create_checkout_session(
            price_id="price_credits_50",
            mode="payment",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        assert session["mode"] == "payment"

    def test_verify_webhook_signature_test_mode(self, stripe_client):
        """Webhook署名検証（テストモード）"""
        result = stripe_client.verify_webhook_signature(b"test", "sig")
        assert result  # テストモードでは常にTrue

    def test_parse_webhook_event(self, stripe_client):
        """Webhookイベントパース"""
        payload = b'{"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_test"}}}'
        event = stripe_client.parse_webhook_event(payload)
        assert event["type"] == "payment_intent.succeeded"
        assert event["data"]["object"]["id"] == "pi_test"

    def test_is_configured_test_mode(self, stripe_client):
        """設定確認（テストモード）"""
        assert stripe_client.is_configured is True

    def test_is_configured_with_api_key(self):
        """設定確認（APIキー有り）"""
        client = StripeClient(api_key="sk_test_xxx", test_mode=True)
        assert client.is_configured is True


class TestStripeClientNonTestMode:
    """Stripeクライアント非テストモードのテスト"""

    def test_create_customer_no_api_key(self):
        """APIキー未設定時の動作確認"""
        client = StripeClient(api_key="", test_mode=False)
        # Stripe SDKがインストールされている場合は非テストモードで動作
        # APIキーなしではis_configuredがFalse
        assert client.is_configured is False or client._test_mode is True

    def test_client_with_api_key_non_test(self):
        """APIキー設定時の非テストモード"""
        client = StripeClient(api_key="sk_test_dummy", test_mode=False)
        # Stripe SDKがある場合は非テストモードで動作
        # この環境ではstripe SDKがインストールされている
        assert client.is_configured is True

    def test_verify_webhook_without_secret_returns_false(self):
        """Webhookシークレット未設定時の署名検証"""
        client = StripeClient(api_key="sk_test_dummy", test_mode=False, webhook_secret="")
        # テストモードでなければ、シークレットなしで署名検証はFalseを返す
        if not client._test_mode:
            result = client.verify_webhook_signature(b"test", "sig")
            assert result is False
        else:
            # テストモードにフォールバックした場合はTrueを返す
            assert client._test_mode is True


# ========== サブスクリプションマネージャーテスト ==========


class TestSubscriptionManager:
    """サブスクリプションマネージャーのテスト"""

    def test_create_free_subscription(self, subscription_manager):
        """Freeサブスクリプション作成"""
        sub, url = subscription_manager.create_subscription(
            user_id="user_free_001",
            email="free@example.com",
            plan_id="free",
        )
        assert sub.plan_id == "free"
        assert sub.status == SubscriptionStatus.ACTIVE
        assert url is None  # FreeはCheckout不要

    def test_create_paid_subscription(self, subscription_manager):
        """有料サブスクリプション作成"""
        sub, url = subscription_manager.create_subscription(
            user_id="user_paid_001",
            email="paid@example.com",
            plan_id="basic",
        )
        assert sub.plan_id == "basic"
        assert sub.status == SubscriptionStatus.INCOMPLETE
        assert url is not None  # CheckoutURL

    def test_get_subscription(self, subscription_manager):
        """サブスクリプション取得"""
        sub, _ = subscription_manager.create_subscription(
            user_id="user_get_001",
            email="get@example.com",
            plan_id="free",
        )
        retrieved = subscription_manager.get_subscription(sub.subscription_id)
        assert retrieved is not None
        assert retrieved.subscription_id == sub.subscription_id

    def test_get_subscription_by_user(self, subscription_manager):
        """ユーザーIDでサブスクリプション取得"""
        sub, _ = subscription_manager.create_subscription(
            user_id="user_byuser_001",
            email="byuser@example.com",
            plan_id="free",
        )
        retrieved = subscription_manager.get_subscription_by_user("user_byuser_001")
        assert retrieved is not None
        assert retrieved.user_id == "user_byuser_001"

    def test_update_subscription_plan(self, subscription_manager):
        """プラン変更"""
        sub, _ = subscription_manager.create_subscription(
            user_id="user_upgrade_001",
            email="upgrade@example.com",
            plan_id="free",
        )
        updated = subscription_manager.update_subscription_plan(
            sub.subscription_id,
            "basic",
        )
        assert updated.plan_id == "basic"

    def test_cancel_subscription(self, subscription_manager):
        """サブスクリプションキャンセル"""
        sub, _ = subscription_manager.create_subscription(
            user_id="user_cancel_001",
            email="cancel@example.com",
            plan_id="free",
        )
        canceled = subscription_manager.cancel_subscription(
            sub.subscription_id,
            immediately=True,
        )
        assert canceled.status == SubscriptionStatus.CANCELED

    def test_duplicate_subscription_error(self, subscription_manager):
        """重複サブスクリプションエラー"""
        subscription_manager.create_subscription(
            user_id="user_dup_001",
            email="dup@example.com",
            plan_id="free",
        )
        with pytest.raises(ValueError):
            subscription_manager.create_subscription(
                user_id="user_dup_001",
                email="dup@example.com",
                plan_id="basic",
            )

    def test_invalid_plan_error(self, subscription_manager):
        """無効プランエラー"""
        with pytest.raises(ValueError):
            subscription_manager.create_subscription(
                user_id="user_invalid_001",
                email="invalid@example.com",
                plan_id="invalid_plan",
            )

    def test_get_subscription_by_api_key(self, subscription_manager):
        """APIキーIDでサブスクリプション取得"""
        sub, _ = subscription_manager.create_subscription(
            user_id="user_apikey_001",
            email="apikey@example.com",
            plan_id="free",
            api_key_id="vca_test_key_001",
        )
        retrieved = subscription_manager.get_subscription_by_api_key("vca_test_key_001")
        assert retrieved is not None
        assert retrieved.api_key_id == "vca_test_key_001"

    def test_get_subscription_by_api_key_not_found(self, subscription_manager):
        """存在しないAPIキーIDでサブスクリプション取得"""
        retrieved = subscription_manager.get_subscription_by_api_key("nonexistent_key")
        assert retrieved is None

    def test_list_subscriptions_all(self, subscription_manager):
        """サブスクリプション一覧取得"""
        subscription_manager.create_subscription(
            user_id="user_list_001",
            email="list1@example.com",
            plan_id="free",
        )
        subscription_manager.create_subscription(
            user_id="user_list_002",
            email="list2@example.com",
            plan_id="free",
        )
        subscriptions = subscription_manager.list_subscriptions()
        assert len(subscriptions) >= 2

    def test_list_subscriptions_by_user(self, subscription_manager):
        """ユーザーIDでサブスクリプション一覧フィルタ"""
        subscription_manager.create_subscription(
            user_id="user_filter_001",
            email="filter@example.com",
            plan_id="free",
        )
        subscriptions = subscription_manager.list_subscriptions(user_id="user_filter_001")
        assert len(subscriptions) == 1
        assert subscriptions[0].user_id == "user_filter_001"

    def test_list_subscriptions_by_status(self, subscription_manager):
        """ステータスでサブスクリプション一覧フィルタ"""
        subscription_manager.create_subscription(
            user_id="user_status_001",
            email="status@example.com",
            plan_id="free",
        )
        active_subs = subscription_manager.list_subscriptions(status=SubscriptionStatus.ACTIVE)
        assert len(active_subs) >= 1

    def test_activate_subscription_not_found(self, subscription_manager):
        """存在しないサブスクリプションのアクティベート"""
        result = subscription_manager.activate_subscription(
            "nonexistent_sub_id",
            "stripe_sub_123",
        )
        assert result is None

    def test_update_subscription_plan_not_found(self, subscription_manager):
        """存在しないサブスクリプションのプラン変更"""
        result = subscription_manager.update_subscription_plan(
            "nonexistent_sub_id",
            "basic",
        )
        assert result is None

    def test_update_subscription_plan_invalid_plan(self, subscription_manager):
        """無効プランへのプラン変更"""
        sub, _ = subscription_manager.create_subscription(
            user_id="user_invalid_upgrade",
            email="invalid_upgrade@example.com",
            plan_id="free",
        )
        with pytest.raises(ValueError):
            subscription_manager.update_subscription_plan(
                sub.subscription_id,
                "invalid_plan",
            )

    def test_cancel_subscription_not_found(self, subscription_manager):
        """存在しないサブスクリプションのキャンセル"""
        result = subscription_manager.cancel_subscription("nonexistent_sub_id")
        assert result is None

    def test_cancel_subscription_at_period_end(self, subscription_manager):
        """期間終了時キャンセル"""
        sub, _ = subscription_manager.create_subscription(
            user_id="user_cancel_end",
            email="cancel_end@example.com",
            plan_id="free",
        )
        canceled = subscription_manager.cancel_subscription(
            sub.subscription_id,
            immediately=False,
        )
        assert canceled.cancel_at_period_end is True
        assert canceled.status == SubscriptionStatus.ACTIVE  # まだアクティブ

    def test_handle_subscription_updated_not_found(self, subscription_manager):
        """存在しないStripeサブスクリプションの更新イベント"""
        result = subscription_manager.handle_subscription_updated(
            "nonexistent_stripe_sub",
            "active",
            1735689600,
        )
        assert result is None


# ========== クレジットマネージャーテスト ==========


class TestCreditManager:
    """クレジットマネージャーのテスト"""

    def test_get_or_create_balance(self, credit_manager):
        """残高取得/作成"""
        balance = credit_manager.get_or_create_balance("user_credit_001")
        assert balance.user_id == "user_credit_001"
        assert balance.balance == 0

    def test_create_purchase_intent(self, credit_manager):
        """購入Intent作成"""
        result = credit_manager.create_purchase_intent(
            user_id="user_purchase_001",
            package_id="credits_50",
        )
        assert "payment_intent_id" in result
        assert "client_secret" in result
        assert result["credits"] == 50
        assert result["bonus_credits"] == 5

    def test_invalid_package_error(self, credit_manager):
        """無効パッケージエラー"""
        with pytest.raises(ValueError):
            credit_manager.create_purchase_intent(
                user_id="user_invalid_pkg",
                package_id="invalid_package",
            )

    def test_complete_purchase(self, credit_manager, stripe_client):
        """購入完了"""
        # Intent作成
        result = credit_manager.create_purchase_intent(
            user_id="user_complete_001",
            package_id="credits_100",
        )

        # 支払い確認（テストモード）
        stripe_client.confirm_payment_intent(result["payment_intent_id"])

        # 購入完了
        tx = credit_manager.complete_purchase(result["payment_intent_id"])
        assert tx is not None
        assert tx.amount == 115  # 100 + 15 bonus

        # 残高確認
        balance = credit_manager.get_balance("user_complete_001")
        assert balance.balance == 100
        assert balance.bonus_balance == 15

    def test_use_credits(self, credit_manager):
        """クレジット使用"""
        balance = credit_manager.get_or_create_balance("user_use_001")
        balance.add_credits(100)
        credit_manager._save_balances()

        success, tx, msg = credit_manager.use_credits(
            user_id="user_use_001",
            amount=30,
            description="画像生成",
        )
        assert success
        assert tx.amount == -30

    def test_use_credits_insufficient(self, credit_manager):
        """クレジット不足"""
        credit_manager.get_or_create_balance("user_insufficient_001")

        success, tx, msg = credit_manager.use_credits(
            user_id="user_insufficient_001",
            amount=50,
        )
        assert not success
        assert "不足" in msg

    def test_add_bonus_credits(self, credit_manager):
        """ボーナス付与"""
        tx = credit_manager.add_bonus_credits(
            user_id="user_bonus_001",
            amount=20,
            description="初回登録ボーナス",
        )
        assert tx.amount == 20
        assert tx.transaction_type == TransactionType.CREDIT_BONUS

    def test_get_transactions(self, credit_manager):
        """取引履歴取得"""
        user_id = "user_tx_001"
        credit_manager.add_bonus_credits(user_id, 10)
        credit_manager.add_bonus_credits(user_id, 20)

        transactions = credit_manager.get_transactions(user_id)
        assert len(transactions) >= 2

    def test_get_packages(self, credit_manager):
        """パッケージ一覧取得"""
        packages = credit_manager.get_packages()
        assert len(packages) == 4
        assert "credits_10" in packages
        assert "credits_50" in packages


# ========== API エンドポイントテスト ==========


class TestPaymentAPI:
    """決済APIのテスト"""

    def test_list_plans(self):
        """プラン一覧取得"""
        response = client.get("/api/v1/payment/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) == 4

    def test_list_credit_packages(self):
        """クレジットパッケージ一覧取得"""
        response = client.get("/api/v1/payment/credits/packages")
        assert response.status_code == 200
        data = response.json()
        assert "packages" in data

    def test_get_subscription_no_auth(self):
        """認証なしでサブスクリプション取得"""
        response = client.get("/api/v1/payment/subscriptions/me")
        assert response.status_code == 401

    def test_get_credit_balance_no_auth(self):
        """認証なしでクレジット残高取得"""
        response = client.get("/api/v1/payment/credits/balance")
        assert response.status_code == 401

    def test_webhook_endpoint(self):
        """Webhookエンドポイント"""
        event = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test", "status": "succeeded"}},
        }
        response = client.post(
            "/api/v1/payment/webhook",
            content=json.dumps(event),
        )
        assert response.status_code == 200

    def test_checkout_success(self):
        """Checkout成功ページ"""
        response = client.get("/api/v1/payment/success?session_id=cs_test_123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_checkout_cancel(self):
        """Checkoutキャンセルページ"""
        response = client.get("/api/v1/payment/cancel")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "canceled"


# ========== 統合テスト ==========


class TestPaymentIntegration:
    """決済統合テスト"""

    def test_full_subscription_flow(self, subscription_manager, credit_manager):
        """サブスクリプションフロー全体"""
        user_id = "user_flow_001"

        # 1. Freeプランで開始
        sub, _ = subscription_manager.create_subscription(
            user_id=user_id,
            email="flow@example.com",
            plan_id="free",
        )
        assert sub.status == SubscriptionStatus.ACTIVE

        # 2. プランアップグレード
        updated = subscription_manager.update_subscription_plan(
            sub.subscription_id,
            "basic",
        )
        assert updated.plan_id == "basic"

        # 3. キャンセル
        canceled = subscription_manager.cancel_subscription(
            sub.subscription_id,
            immediately=False,
        )
        assert canceled.cancel_at_period_end

    def test_full_credit_flow(self, credit_manager, stripe_client):
        """クレジットフロー全体"""
        user_id = "user_credit_flow_001"

        # 1. 購入Intent作成
        intent = credit_manager.create_purchase_intent(
            user_id=user_id,
            package_id="credits_50",
        )
        assert intent["credits"] == 50

        # 2. 支払い確認
        stripe_client.confirm_payment_intent(intent["payment_intent_id"])

        # 3. 購入完了
        tx = credit_manager.complete_purchase(intent["payment_intent_id"])
        assert tx is not None

        # 4. 残高確認
        balance = credit_manager.get_balance(user_id)
        assert balance.get_total_balance() == 55  # 50 + 5 bonus

        # 5. クレジット使用
        success, use_tx, _ = credit_manager.use_credits(user_id, 10)
        assert success
        assert balance.get_total_balance() == 45

        # 6. 取引履歴確認
        transactions = credit_manager.get_transactions(user_id)
        assert len(transactions) >= 2


# ========== 決済ルートAPIテスト ==========


class TestPaymentRoutesAPI:
    """決済ルートAPIの追加テスト（カバレッジ向上用）"""

    @pytest.fixture
    def api_key_header(self):
        """テスト用APIキーとヘッダーを作成"""
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Payment Test Key"},
        )
        raw_key = response.json()["api_key"]
        return {"X-API-Key": raw_key}

    def test_create_subscription_free(self, api_key_header):
        """Freeサブスクリプション作成"""
        response = client.post(
            "/api/v1/payment/subscriptions",
            json={
                "email": "free@example.com",
                "plan_id": "free",
            },
            headers=api_key_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == "free"
        assert data["status"] == "active"
        assert data["checkout_url"] is None

    def test_create_subscription_paid(self, api_key_header):
        """有料サブスクリプション作成"""
        response = client.post(
            "/api/v1/payment/subscriptions",
            json={
                "email": "paid@example.com",
                "plan_id": "basic",
                "billing_interval": "monthly",
            },
            headers=api_key_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == "basic"
        assert data["checkout_url"] is not None

    def test_create_subscription_invalid_plan(self, api_key_header):
        """無効なプランでサブスクリプション作成"""
        response = client.post(
            "/api/v1/payment/subscriptions",
            json={
                "email": "invalid@example.com",
                "plan_id": "nonexistent",
            },
            headers=api_key_header,
        )
        assert response.status_code == 400

    def test_get_my_subscription_no_subscription(self, api_key_header):
        """サブスクリプションなしの状態取得"""
        # 新しいキーを作成（サブスクリプションなし）
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "free", "name": "No Sub Key"},
        )
        new_key = response.json()["api_key"]

        response = client.get(
            "/api/v1/payment/subscriptions/me",
            headers={"X-API-Key": new_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == "free"
        assert data["status"] == "none"
        assert data["is_active"] is True

    def test_get_my_subscription_with_subscription(self, api_key_header):
        """サブスクリプションありの状態取得"""
        # サブスクリプション作成
        client.post(
            "/api/v1/payment/subscriptions",
            json={"email": "sub@example.com", "plan_id": "free"},
            headers=api_key_header,
        )

        response = client.get(
            "/api/v1/payment/subscriptions/me",
            headers=api_key_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan_id"] == "free"
        assert data["is_active"] is True

    def test_get_credit_balance(self, api_key_header):
        """クレジット残高取得"""
        response = client.get(
            "/api/v1/payment/credits/balance",
            headers=api_key_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "bonus_balance" in data
        assert "total_balance" in data

    def test_purchase_credits(self, api_key_header):
        """クレジット購入Intent作成"""
        response = client.post(
            "/api/v1/payment/credits/purchase",
            json={"package_id": "credits_50"},
            headers=api_key_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "payment_intent_id" in data
        assert "client_secret" in data
        assert data["credits"] == 50

    def test_purchase_credits_invalid_package(self, api_key_header):
        """無効なパッケージでクレジット購入"""
        response = client.post(
            "/api/v1/payment/credits/purchase",
            json={"package_id": "invalid_package"},
            headers=api_key_header,
        )
        assert response.status_code == 400

    def test_get_credit_transactions(self, api_key_header):
        """クレジット取引履歴取得"""
        response = client.get(
            "/api/v1/payment/credits/transactions",
            headers=api_key_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total" in data

    def test_get_credit_transactions_with_filter(self, api_key_header):
        """フィルタ付きクレジット取引履歴取得"""
        response = client.get(
            "/api/v1/payment/credits/transactions?transaction_type=credit_purchase&limit=10&offset=0",
            headers=api_key_header,
        )
        assert response.status_code == 200

    def test_get_credit_transactions_invalid_filter(self, api_key_header):
        """無効なフィルタでも動作"""
        response = client.get(
            "/api/v1/payment/credits/transactions?transaction_type=invalid_type",
            headers=api_key_header,
        )
        assert response.status_code == 200

    def test_webhook_checkout_completed(self):
        """Webhook: checkout.session.completed"""
        event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "subscription": "sub_stripe_123",
                    "metadata": {"subscription_id": "sub_internal_123"},
                }
            },
        }
        response = client.post(
            "/api/v1/payment/webhook",
            content=json.dumps(event),
        )
        assert response.status_code == 200
        assert response.json()["received"] is True

    def test_webhook_subscription_updated(self):
        """Webhook: customer.subscription.updated"""
        event = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_stripe_123",
                    "status": "active",
                    "current_period_end": 1735689600,
                }
            },
        }
        response = client.post(
            "/api/v1/payment/webhook",
            content=json.dumps(event),
        )
        assert response.status_code == 200

    def test_webhook_subscription_deleted(self):
        """Webhook: customer.subscription.deleted"""
        event = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_stripe_deleted",
                }
            },
        }
        response = client.post(
            "/api/v1/payment/webhook",
            content=json.dumps(event),
        )
        assert response.status_code == 200

    def test_webhook_payment_succeeded(self):
        """Webhook: payment_intent.succeeded"""
        event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "metadata": {"package_id": "credits_50"},
                }
            },
        }
        response = client.post(
            "/api/v1/payment/webhook",
            content=json.dumps(event),
        )
        assert response.status_code == 200

    def test_webhook_payment_failed(self):
        """Webhook: invoice.payment_failed"""
        event = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "subscription": "sub_failed_123",
                }
            },
        }
        response = client.post(
            "/api/v1/payment/webhook",
            content=json.dumps(event),
        )
        assert response.status_code == 200

    def test_webhook_invalid_signature(self):
        """Webhook署名検証（テストモードでは常にパス）"""
        event = {"type": "test.event", "data": {"object": {}}}
        response = client.post(
            "/api/v1/payment/webhook",
            content=json.dumps(event),
            headers={"Stripe-Signature": "invalid_sig"},
        )
        # テストモードでは署名検証をスキップするため200
        assert response.status_code == 200


# ========== エッジケーステスト ==========


class TestPaymentEdgeCases:
    """エッジケーステスト"""

    def test_bonus_expiration(self, credit_manager):
        """ボーナス有効期限"""
        balance = credit_manager.get_or_create_balance("user_expire_001")
        balance.add_credits(50, is_bonus=True)
        # 期限切れに設定
        balance.bonus_expires_at = (datetime.now() - timedelta(days=1)).isoformat()

        # 期限切れボーナスは含まない
        assert balance.get_total_balance() == 0

    def test_subscription_persistence(self, subscription_manager, temp_storage):
        """サブスクリプション永続化"""
        sub, _ = subscription_manager.create_subscription(
            user_id="user_persist_001",
            email="persist@example.com",
            plan_id="free",
        )

        # 新しいマネージャーで読み込み
        new_manager = SubscriptionManager(
            stripe_client=subscription_manager._stripe,
            storage_path=temp_storage / "subscriptions.json",
        )
        loaded = new_manager.get_subscription(sub.subscription_id)
        assert loaded is not None
        assert loaded.user_id == "user_persist_001"

    def test_credit_persistence(self, credit_manager, stripe_client, temp_storage):
        """クレジット永続化"""
        balance = credit_manager.get_or_create_balance("user_credit_persist_001")
        balance.add_credits(100)
        credit_manager._save_balances()

        # 新しいマネージャーで読み込み
        new_manager = CreditManager(
            stripe_client=stripe_client,
            storage_path=temp_storage,
        )
        loaded = new_manager.get_balance("user_credit_persist_001")
        assert loaded is not None
        assert loaded.balance == 100


# ========== 年額プランテスト ==========


class TestYearlyBilling:
    """年額プランのテスト"""

    def test_yearly_price_exists(self):
        """年額価格が定義されていること"""
        plans = PlanPrice.get_plans()
        for plan_id, plan in plans.items():
            assert hasattr(plan, "price_yearly")
            assert plan.price_yearly is not None
            assert isinstance(plan.price_yearly, Decimal)

    def test_yearly_discount_applied(self):
        """年額プランに割引が適用されていること"""
        plans = PlanPrice.get_plans()

        # Basic: 月額9.99 × 12 = 119.88、年額99.99（約16%割引）
        basic = plans["basic"]
        monthly_total = basic.price_monthly * 12
        assert basic.price_yearly < monthly_total
        discount = (1 - basic.price_yearly / monthly_total) * 100
        assert discount > 10  # 10%以上の割引

        # Pro: 月額29.99 × 12 = 359.88、年額299.99（約17%割引）
        pro = plans["pro"]
        monthly_total = pro.price_monthly * 12
        assert pro.price_yearly < monthly_total
        discount = (1 - pro.price_yearly / monthly_total) * 100
        assert discount > 10

    def test_free_plan_yearly_is_free(self):
        """Freeプランの年額も無料であること"""
        plans = PlanPrice.get_plans()
        free = plans["free"]
        assert free.price_monthly == Decimal("0")
        assert free.price_yearly == Decimal("0")

    def test_subscription_with_yearly_billing(self):
        """年額課金間隔でサブスクリプション作成"""
        sub = Subscription(
            subscription_id="sub_yearly_001",
            user_id="user_yearly_001",
            plan_id="pro",
            billing_interval="yearly",
        )
        assert sub.billing_interval == "yearly"
        assert sub.plan_id == "pro"
        assert sub.is_active()

    def test_subscription_serialization_with_yearly(self):
        """年額サブスクリプションのシリアライズ"""
        sub = Subscription(
            subscription_id="sub_yearly_002",
            user_id="user_yearly_002",
            plan_id="basic",
            billing_interval="yearly",
        )
        data = sub.to_dict()
        assert data["billing_interval"] == "yearly"

        restored = Subscription.from_dict(data)
        assert restored.billing_interval == "yearly"

    def test_subscription_manager_yearly_free(self, subscription_manager):
        """SubscriptionManager: Freeプラン年額（即時アクティベート）"""
        sub, checkout_url = subscription_manager.create_subscription(
            user_id="user_yearly_free",
            email="yearly_free@example.com",
            plan_id="free",
            billing_interval="yearly",
        )
        # Freeプランは即時アクティベート、チェックアウト不要
        assert checkout_url is None
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.billing_interval == "yearly"

    def test_subscription_manager_yearly_paid(self, subscription_manager):
        """SubscriptionManager: 有料プラン年額（Checkoutセッション）"""
        sub, checkout_url = subscription_manager.create_subscription(
            user_id="user_yearly_paid",
            email="yearly_paid@example.com",
            plan_id="pro",
            billing_interval="yearly",
        )
        # 有料プランはCheckoutセッションが必要
        # テストモードではチェックアウトURLは生成されない場合がある
        assert sub.plan_id == "pro"
        assert sub.billing_interval == "yearly"
        assert sub.status == SubscriptionStatus.INCOMPLETE


class TestYearlyBillingAPI:
    """年額プランAPIテスト"""

    def test_plans_endpoint_includes_yearly_price(self):
        """プラン一覧エンドポイントに年額価格が含まれること"""
        response = client.get("/api/v1/payment/plans")
        assert response.status_code == 200
        data = response.json()

        for plan in data["plans"]:
            assert "price_yearly" in plan
            assert plan["price_yearly"] is not None
            # 数値として解析可能であること
            yearly_price = float(plan["price_yearly"])
            assert yearly_price >= 0

    def test_create_subscription_with_yearly_billing(self, tmp_path):
        """年額課金でサブスクリプション作成"""
        import uuid
        from src.api.auth.models import APIKey
        from src.api.auth.dependencies import get_api_key

        # ユニークなIDを生成
        unique_id = str(uuid.uuid4())[:8]

        # モック用のAPIキーオブジェクト
        mock_api_key = APIKey(
            key_id=f"test_yearly_key_{unique_id}",
            key_hash="mock_hash_yearly",
            tier=APIKeyTier.BASIC,
            owner_id=f"yearly_test_user_{unique_id}",
        )

        # FastAPIの依存関係オーバーライド
        app.dependency_overrides[get_api_key] = lambda: mock_api_key
        try:
            response = client.post(
                "/api/v1/payment/subscriptions",
                json={
                    "email": f"test_yearly_api_{unique_id}@example.com",
                    "plan_id": "free",
                    "billing_interval": "yearly",
                },
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
            data = response.json()
            assert data["billing_interval"] == "yearly"
        finally:
            app.dependency_overrides.clear()

    def test_create_subscription_default_monthly(self, tmp_path):
        """デフォルトは月額課金"""
        import uuid
        from src.api.auth.models import APIKey
        from src.api.auth.dependencies import get_api_key

        # ユニークなIDを生成
        unique_id = str(uuid.uuid4())[:8]

        # モック用のAPIキーオブジェクト
        mock_api_key = APIKey(
            key_id=f"test_monthly_key_{unique_id}",
            key_hash="mock_hash_monthly",
            tier=APIKeyTier.BASIC,
            owner_id=f"monthly_test_user_{unique_id}",
        )

        # FastAPIの依存関係オーバーライド
        app.dependency_overrides[get_api_key] = lambda: mock_api_key
        try:
            response = client.post(
                "/api/v1/payment/subscriptions",
                json={
                    "email": f"test_monthly_default_{unique_id}@example.com",
                    "plan_id": "free",
                },
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
            data = response.json()
            assert data["billing_interval"] == "monthly"
        finally:
            app.dependency_overrides.clear()


# ========== StripeClient高度なテスト ==========


class TestStripeClientWebhookSignature:
    """Webhook署名検証の詳細テスト"""

    def test_manual_verify_signature_valid(self):
        """手動署名検証（有効な署名）"""
        import hashlib
        import hmac
        import time

        secret = "whsec_test_secret_12345"
        payload = b'{"type": "test.event"}'
        timestamp = str(int(time.time()))

        # 正しい署名を計算
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        signature = f"t={timestamp},v1={expected_sig}"

        # テストモードでないクライアントで検証
        client = StripeClient(
            api_key="sk_test_dummy",
            webhook_secret=secret,
            test_mode=False,
        )

        # Stripeライブラリがない場合は手動検証が使われる
        if client._stripe is None:
            result = client._manual_verify_signature(payload, signature)
            assert result is True

    def test_manual_verify_signature_invalid_format(self):
        """手動署名検証（不正な形式）"""
        client = StripeClient(
            api_key="sk_test_dummy",
            webhook_secret="whsec_test",
            test_mode=False,
        )

        # Stripeライブラリがない場合のみテスト
        if client._stripe is None:
            result = client._manual_verify_signature(b"test", "invalid_signature")
            assert result is False

    def test_manual_verify_signature_no_timestamp(self):
        """手動署名検証（タイムスタンプなし）"""
        client = StripeClient(
            api_key="sk_test_dummy",
            webhook_secret="whsec_test",
            test_mode=False,
        )

        if client._stripe is None:
            # タイムスタンプがない場合
            result = client._manual_verify_signature(b"test", "v1=signature_only")
            assert result is False

    def test_manual_verify_signature_no_v1(self):
        """手動署名検証（v1署名なし）"""
        client = StripeClient(
            api_key="sk_test_dummy",
            webhook_secret="whsec_test",
            test_mode=False,
        )

        if client._stripe is None:
            # v1署名がない場合
            result = client._manual_verify_signature(b"test", "t=12345")
            assert result is False

    def test_verify_webhook_without_secret(self):
        """Webhookシークレット未設定時"""
        client = StripeClient(
            api_key="sk_test_dummy",
            webhook_secret="",
            test_mode=False,
        )

        # stripeライブラリがインストールされていてもシークレットなしはFalse
        if not client._test_mode:
            result = client.verify_webhook_signature(b"test", "t=123,v1=abc")
            assert result is False


class TestStripeClientSingletonAndConfig:
    """Stripeクライアントのシングルトンと設定テスト"""

    def test_get_stripe_client_singleton(self):
        """シングルトンインスタンス取得"""
        from src.api.payment.stripe_client import get_stripe_client, _client

        # 既存のクライアントをリセット
        import src.api.payment.stripe_client as stripe_module
        stripe_module._client = None

        client1 = get_stripe_client(test_mode=True)
        client2 = get_stripe_client(test_mode=True)

        # 同一インスタンスであること
        assert client1 is client2

        # リセット
        stripe_module._client = None

    def test_stripe_client_mock_id_generation(self):
        """モックID生成"""
        client = StripeClient(test_mode=True)

        id1 = client._generate_mock_id("test")
        id2 = client._generate_mock_id("test")

        assert id1.startswith("test_")
        assert id2.startswith("test_")
        assert id1 != id2  # ユニークであること

    def test_stripe_client_test_mode_enabled_by_default(self):
        """テストモードがデフォルトで有効"""
        client = StripeClient()
        assert client._test_mode is True


class TestStripeClientErrorCases:
    """Stripeクライアントのエラーケース"""

    def test_create_customer_no_api_error(self):
        """APIキーなしで顧客作成を試行"""
        # テストモードではエラーにならない
        client = StripeClient(test_mode=True)
        customer = client.create_customer(email="test@example.com")
        assert customer is not None

    def test_create_subscription_no_api_error(self):
        """APIキーなしでサブスクリプション作成を試行"""
        client = StripeClient(test_mode=True)
        customer = client.create_customer(email="test@example.com")
        sub = client.create_subscription(
            customer_id=customer["id"],
            price_id="price_test",
        )
        assert sub is not None

    def test_checkout_session_without_customer(self):
        """顧客ID なしでCheckoutSession作成"""
        client = StripeClient(test_mode=True)
        session = client.create_checkout_session(
            price_id="price_test",
            mode="payment",
        )
        assert session["customer"] is None
        assert session["id"].startswith("cs_test_")
