#!/usr/bin/env python3
"""
Stripe 本番環境セットアップスクリプト

VisionCraftAI の Stripe 本番環境を設定するための自動化スクリプト。
商品・価格の作成、Webhookの設定を行う。

使用方法:
    python scripts/setup_stripe.py --api-key sk_live_xxx

前提条件:
    - Stripeアカウント作成済み
    - 本番APIキー取得済み
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

# stripeのインポートを遅延させる
stripe = None


def import_stripe():
    """Stripeライブラリのインポート"""
    global stripe
    try:
        import stripe as _stripe
        stripe = _stripe
        return True
    except ImportError:
        print("エラー: stripe ライブラリがインストールされていません")
        print("  pip install stripe")
        return False


class StripeSetup:
    """Stripe セットアップクラス"""

    # 商品定義
    PRODUCTS = {
        "subscription": {
            "name": "VisionCraftAI サブスクリプション",
            "description": "AI画像生成サービスの月額プラン",
        },
        "credits": {
            "name": "VisionCraftAI クレジット",
            "description": "従量課金用クレジット",
        },
    }

    # 価格定義（サブスクリプション）
    SUBSCRIPTION_PRICES = {
        "basic": {
            "unit_amount": 999,  # $9.99
            "currency": "usd",
            "nickname": "Basic Plan",
            "recurring": {"interval": "month"},
        },
        "pro": {
            "unit_amount": 2999,  # $29.99
            "currency": "usd",
            "nickname": "Pro Plan",
            "recurring": {"interval": "month"},
        },
        "enterprise": {
            "unit_amount": 9999,  # $99.99
            "currency": "usd",
            "nickname": "Enterprise Plan",
            "recurring": {"interval": "month"},
        },
    }

    # クレジットパッケージ価格
    CREDIT_PRICES = {
        "credits_10": {
            "unit_amount": 499,  # $4.99
            "currency": "usd",
            "nickname": "10 Credits",
        },
        "credits_50": {
            "unit_amount": 1999,  # $19.99
            "currency": "usd",
            "nickname": "50 Credits (+5 Bonus)",
        },
        "credits_100": {
            "unit_amount": 3499,  # $34.99
            "currency": "usd",
            "nickname": "100 Credits (+15 Bonus)",
        },
        "credits_500": {
            "unit_amount": 14999,  # $149.99
            "currency": "usd",
            "nickname": "500 Credits (+100 Bonus)",
        },
    }

    def __init__(self, api_key: str, webhook_url: Optional[str] = None):
        self.api_key = api_key
        self.webhook_url = webhook_url
        self.created_ids: dict[str, str] = {}
        self.project_root = Path(__file__).parent.parent

    def init_stripe(self) -> bool:
        """Stripe初期化"""
        if not import_stripe():
            return False

        stripe.api_key = self.api_key

        # APIキー検証
        print("\n[1/5] APIキー検証...")
        try:
            stripe.Account.retrieve()
            is_live = self.api_key.startswith("sk_live_")
            mode = "本番" if is_live else "テスト"
            print(f"  ✓ APIキー有効（{mode}モード）")
            return True
        except stripe.error.AuthenticationError:
            print("  ✗ APIキーが無効です")
            return False

    def create_products(self) -> bool:
        """商品作成"""
        print("\n[2/5] 商品作成...")

        for product_id, product_data in self.PRODUCTS.items():
            # 既存確認
            existing = list(stripe.Product.list(limit=100).data)
            found = next(
                (p for p in existing if p.metadata.get("vca_id") == product_id), None
            )

            if found:
                print(f"  ✓ 商品既存: {product_data['name']} ({found.id})")
                self.created_ids[f"product_{product_id}"] = found.id
            else:
                product = stripe.Product.create(
                    name=product_data["name"],
                    description=product_data["description"],
                    metadata={"vca_id": product_id},
                )
                print(f"  ✓ 商品作成: {product_data['name']} ({product.id})")
                self.created_ids[f"product_{product_id}"] = product.id

        return True

    def create_prices(self) -> bool:
        """価格作成"""
        print("\n[3/5] 価格作成...")

        # サブスクリプション価格
        subscription_product_id = self.created_ids.get("product_subscription")
        if subscription_product_id:
            for price_id, price_data in self.SUBSCRIPTION_PRICES.items():
                existing = list(
                    stripe.Price.list(
                        product=subscription_product_id, active=True, limit=100
                    ).data
                )
                found = next(
                    (p for p in existing if p.metadata.get("vca_id") == price_id), None
                )

                if found:
                    print(f"  ✓ 価格既存: {price_data['nickname']} ({found.id})")
                    self.created_ids[f"price_{price_id}"] = found.id
                else:
                    price = stripe.Price.create(
                        product=subscription_product_id,
                        unit_amount=price_data["unit_amount"],
                        currency=price_data["currency"],
                        nickname=price_data["nickname"],
                        recurring=price_data["recurring"],
                        metadata={"vca_id": price_id},
                    )
                    print(f"  ✓ 価格作成: {price_data['nickname']} ({price.id})")
                    self.created_ids[f"price_{price_id}"] = price.id

        # クレジット価格
        credits_product_id = self.created_ids.get("product_credits")
        if credits_product_id:
            for price_id, price_data in self.CREDIT_PRICES.items():
                existing = list(
                    stripe.Price.list(
                        product=credits_product_id, active=True, limit=100
                    ).data
                )
                found = next(
                    (p for p in existing if p.metadata.get("vca_id") == price_id), None
                )

                if found:
                    print(f"  ✓ 価格既存: {price_data['nickname']} ({found.id})")
                    self.created_ids[f"price_{price_id}"] = found.id
                else:
                    price = stripe.Price.create(
                        product=credits_product_id,
                        unit_amount=price_data["unit_amount"],
                        currency=price_data["currency"],
                        nickname=price_data["nickname"],
                        metadata={"vca_id": price_id},
                    )
                    print(f"  ✓ 価格作成: {price_data['nickname']} ({price.id})")
                    self.created_ids[f"price_{price_id}"] = price.id

        return True

    def create_webhook(self) -> Optional[str]:
        """Webhook作成"""
        print("\n[4/5] Webhook設定...")

        if not self.webhook_url:
            print("  スキップ（--webhook-url 未指定）")
            return None

        webhook_endpoint = f"{self.webhook_url}/api/v1/payment/webhook"

        # 既存確認
        existing = list(stripe.WebhookEndpoint.list(limit=100).data)
        found = next((w for w in existing if w.url == webhook_endpoint), None)

        if found:
            print(f"  ✓ Webhook既存: {found.id}")
            return found.secret if hasattr(found, "secret") else None

        webhook = stripe.WebhookEndpoint.create(
            url=webhook_endpoint,
            enabled_events=[
                "checkout.session.completed",
                "customer.subscription.created",
                "customer.subscription.updated",
                "customer.subscription.deleted",
                "invoice.paid",
                "invoice.payment_failed",
                "payment_intent.succeeded",
                "payment_intent.payment_failed",
            ],
            description="VisionCraftAI Payment Webhook",
        )

        print(f"  ✓ Webhook作成: {webhook.id}")
        print(f"  ⚠ Webhookシークレット: {webhook.secret}")
        print("    このシークレットを環境変数 STRIPE_WEBHOOK_SECRET に設定してください")

        return webhook.secret

    def save_config(self, webhook_secret: Optional[str]):
        """設定保存"""
        print("\n[5/5] 設定保存...")

        config = {
            "products": {
                k.replace("product_", ""): v
                for k, v in self.created_ids.items()
                if k.startswith("product_")
            },
            "prices": {
                k.replace("price_", ""): v
                for k, v in self.created_ids.items()
                if k.startswith("price_")
            },
        }

        # 設定ファイル保存
        config_file = self.project_root / "config" / "stripe_ids.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"  ✓ 設定保存: {config_file}")

        # .env追加内容を表示
        print("\n" + "=" * 60)
        print(".env に追加する内容:")
        print("=" * 60)
        print(f"\n# Stripe設定")
        print(f"# STRIPE_SECRET_KEY={self.api_key[:20]}...")
        for price_id, stripe_id in config["prices"].items():
            env_key = f"STRIPE_PRICE_{price_id.upper()}"
            print(f"{env_key}={stripe_id}")
        if webhook_secret:
            print(f"STRIPE_WEBHOOK_SECRET={webhook_secret}")
        print()

    def setup(self) -> bool:
        """セットアップ実行"""
        print("=" * 60)
        print("VisionCraftAI - Stripe セットアップ")
        print("=" * 60)

        if not self.init_stripe():
            return False

        if not self.create_products():
            return False

        if not self.create_prices():
            return False

        webhook_secret = self.create_webhook()
        self.save_config(webhook_secret)

        print("\n✓ Stripe セットアップ完了！")
        return True


def main():
    parser = argparse.ArgumentParser(description="VisionCraftAI Stripe セットアップ")
    parser.add_argument(
        "--api-key",
        "-k",
        required=True,
        help="Stripe APIキー（sk_live_xxx または sk_test_xxx）",
    )
    parser.add_argument(
        "--webhook-url",
        "-w",
        help="Webhook URL（例: https://your-domain.com）",
    )

    args = parser.parse_args()

    setup = StripeSetup(args.api_key, args.webhook_url)
    success = setup.setup()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
