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

    def test_create_subscription(self, stripe_client):
        """サブスクリプション作成"""
        customer = stripe_client.create_customer(email="sub@example.com")
        subscription = stripe_client.create_subscription(
            customer_id=customer["id"],
            price_id="price_basic_monthly",
        )
        assert subscription["id"].startswith("sub_test_")
        assert subscription["status"] == "active"

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

    def test_create_payment_intent(self, stripe_client):
        """PaymentIntent作成"""
        intent = stripe_client.create_payment_intent(
            amount_cents=999,
            metadata={"user_id": "test_user"},
        )
        assert intent["id"].startswith("pi_test_")
        assert intent["amount"] == 999
        assert "client_secret" in intent

    def test_confirm_payment_intent(self, stripe_client):
        """PaymentIntent確認"""
        intent = stripe_client.create_payment_intent(amount_cents=1999)
        confirmed = stripe_client.confirm_payment_intent(intent["id"])
        assert confirmed["status"] == "succeeded"

    def test_verify_webhook_signature_test_mode(self, stripe_client):
        """Webhook署名検証（テストモード）"""
        result = stripe_client.verify_webhook_signature(b"test", "sig")
        assert result  # テストモードでは常にTrue


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
