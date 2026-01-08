# -*- coding: utf-8 -*-
"""
VisionCraftAI - クレジット管理

クレジットの購入、使用、残高管理を提供します。
"""

import json
import logging
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

from src.api.payment.models import (
    CREDIT_PACKAGES,
    CreditBalance,
    CreditTransaction,
    TransactionType,
)
from src.api.payment.stripe_client import StripeClient, get_stripe_client

logger = logging.getLogger(__name__)


class CreditManager:
    """
    クレジット管理クラス

    クレジットの購入、使用、残高追跡を管理します。
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
            storage_path: データ保存ディレクトリ
        """
        self._stripe = stripe_client or get_stripe_client()
        self._storage_path = storage_path or Path("data")
        self._balances_path = self._storage_path / "credit_balances.json"
        self._transactions_path = self._storage_path / "credit_transactions.json"

        self._balances: dict[str, CreditBalance] = {}
        self._transactions: list[CreditTransaction] = []
        self._load()

    def _load(self) -> None:
        """ストレージからデータを読み込む"""
        # 残高読み込み
        if self._balances_path.exists():
            try:
                with open(self._balances_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for balance_data in data.get("balances", []):
                    balance = CreditBalance.from_dict(balance_data)
                    self._balances[balance.user_id] = balance
                logger.info(f"{len(self._balances)}個のクレジット残高を読み込みました")
            except Exception as e:
                logger.error(f"クレジット残高の読み込みに失敗: {e}")

        # 取引履歴読み込み
        if self._transactions_path.exists():
            try:
                with open(self._transactions_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for tx_data in data.get("transactions", []):
                    tx = CreditTransaction.from_dict(tx_data)
                    self._transactions.append(tx)
                logger.info(f"{len(self._transactions)}件の取引履歴を読み込みました")
            except Exception as e:
                logger.error(f"取引履歴の読み込みに失敗: {e}")

    def _save_balances(self) -> None:
        """残高を保存"""
        try:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "balances": [b.to_dict() for b in self._balances.values()],
            }
            with open(self._balances_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"クレジット残高の保存に失敗: {e}")
            raise

    def _save_transactions(self) -> None:
        """取引履歴を保存"""
        try:
            self._storage_path.mkdir(parents=True, exist_ok=True)
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "transactions": [t.to_dict() for t in self._transactions[-1000:]],
            }
            with open(self._transactions_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"取引履歴の保存に失敗: {e}")
            raise

    def _generate_transaction_id(self) -> str:
        """取引ID生成"""
        return f"tx_{secrets.token_hex(12)}"

    def get_or_create_balance(
        self,
        user_id: str,
        api_key_id: str = "",
    ) -> CreditBalance:
        """
        ユーザーの残高を取得（なければ作成）

        Args:
            user_id: ユーザーID
            api_key_id: APIキーID

        Returns:
            CreditBalance
        """
        if user_id not in self._balances:
            self._balances[user_id] = CreditBalance(
                user_id=user_id,
                api_key_id=api_key_id,
            )
            self._save_balances()
        return self._balances[user_id]

    def get_balance(self, user_id: str) -> Optional[CreditBalance]:
        """
        ユーザーの残高を取得

        Args:
            user_id: ユーザーID

        Returns:
            CreditBalance（存在しない場合はNone）
        """
        return self._balances.get(user_id)

    def create_purchase_intent(
        self,
        user_id: str,
        package_id: str,
        api_key_id: str = "",
    ) -> dict:
        """
        クレジット購入用のPaymentIntentを作成

        Args:
            user_id: ユーザーID
            package_id: パッケージID
            api_key_id: APIキーID

        Returns:
            PaymentIntent情報（client_secret含む）
        """
        if package_id not in CREDIT_PACKAGES:
            raise ValueError(f"無効なパッケージID: {package_id}")

        package = CREDIT_PACKAGES[package_id]
        amount_cents = int(package["price_usd"] * 100)

        # PaymentIntent作成
        intent = self._stripe.create_payment_intent(
            amount_cents=amount_cents,
            currency="usd",
            metadata={
                "user_id": user_id,
                "api_key_id": api_key_id,
                "package_id": package_id,
                "credits": package["credits"],
                "bonus_credits": package["bonus_credits"],
            },
        )

        logger.info(f"クレジット購入Intent作成: {intent['id']} (user={user_id}, package={package_id})")
        return {
            "payment_intent_id": intent["id"],
            "client_secret": intent["client_secret"],
            "amount_usd": str(package["price_usd"]),
            "credits": package["credits"],
            "bonus_credits": package["bonus_credits"],
            "total_credits": package["credits"] + package["bonus_credits"],
        }

    def complete_purchase(
        self,
        payment_intent_id: str,
    ) -> Optional[CreditTransaction]:
        """
        クレジット購入を完了（Webhook経由または確認後に呼び出し）

        Args:
            payment_intent_id: PaymentIntent ID

        Returns:
            取引情報
        """
        # PaymentIntent取得
        intent = self._stripe.get_payment_intent(payment_intent_id)
        if not intent:
            logger.error(f"PaymentIntentが見つかりません: {payment_intent_id}")
            return None

        if intent["status"] != "succeeded":
            logger.warning(f"PaymentIntentが完了していません: {intent['status']}")
            return None

        # メタデータから情報取得
        metadata = intent.get("metadata", {})
        user_id = metadata.get("user_id")
        api_key_id = metadata.get("api_key_id", "")
        package_id = metadata.get("package_id")
        credits = int(metadata.get("credits", 0))
        bonus_credits = int(metadata.get("bonus_credits", 0))

        if not user_id or not package_id:
            logger.error(f"PaymentIntentのメタデータが不正: {metadata}")
            return None

        # 残高取得/作成
        balance = self.get_or_create_balance(user_id, api_key_id)

        # クレジット追加
        balance.add_credits(credits, is_bonus=False)
        if bonus_credits > 0:
            # ボーナスは30日後に期限切れ
            balance.add_credits(bonus_credits, is_bonus=True)
            balance.bonus_expires_at = (
                datetime.now() + timedelta(days=30)
            ).isoformat()

        self._save_balances()

        # 取引記録
        package = CREDIT_PACKAGES[package_id]
        transaction = CreditTransaction(
            transaction_id=self._generate_transaction_id(),
            user_id=user_id,
            transaction_type=TransactionType.CREDIT_PURCHASE,
            amount=credits + bonus_credits,
            balance_after=balance.get_total_balance(),
            stripe_payment_intent_id=payment_intent_id,
            price_usd=Decimal(str(package["price_usd"])),
            description=package["description"],
        )
        self._transactions.append(transaction)
        self._save_transactions()

        logger.info(
            f"クレジット購入完了: {transaction.transaction_id} "
            f"(user={user_id}, credits={credits}+{bonus_credits})"
        )
        return transaction

    def use_credits(
        self,
        user_id: str,
        amount: int,
        reference_id: str = "",
        description: str = "",
    ) -> tuple[bool, Optional[CreditTransaction], str]:
        """
        クレジットを使用

        Args:
            user_id: ユーザーID
            amount: 使用数
            reference_id: 参照ID（画像生成ID等）
            description: 説明

        Returns:
            tuple[bool, Optional[CreditTransaction], str]: (成功, 取引, メッセージ)
        """
        balance = self._balances.get(user_id)
        if not balance:
            return False, None, "クレジット残高が見つかりません"

        if not balance.can_use(amount):
            return False, None, f"クレジット不足（残高: {balance.get_total_balance()}）"

        # クレジット消費
        balance.use_credits(amount)
        self._save_balances()

        # 取引記録
        transaction = CreditTransaction(
            transaction_id=self._generate_transaction_id(),
            user_id=user_id,
            transaction_type=TransactionType.CREDIT_USAGE,
            amount=-amount,
            balance_after=balance.get_total_balance(),
            reference_id=reference_id,
            description=description or f"{amount}クレジット使用",
        )
        self._transactions.append(transaction)
        self._save_transactions()

        logger.info(
            f"クレジット使用: {transaction.transaction_id} "
            f"(user={user_id}, amount={amount})"
        )
        return True, transaction, "OK"

    def add_bonus_credits(
        self,
        user_id: str,
        amount: int,
        description: str = "",
        expires_days: int = 30,
    ) -> Optional[CreditTransaction]:
        """
        ボーナスクレジットを付与

        Args:
            user_id: ユーザーID
            amount: ボーナス数
            description: 説明
            expires_days: 有効期限（日数）

        Returns:
            取引情報
        """
        balance = self.get_or_create_balance(user_id)

        # ボーナス追加
        balance.add_credits(amount, is_bonus=True)
        balance.bonus_expires_at = (
            datetime.now() + timedelta(days=expires_days)
        ).isoformat()
        self._save_balances()

        # 取引記録
        transaction = CreditTransaction(
            transaction_id=self._generate_transaction_id(),
            user_id=user_id,
            transaction_type=TransactionType.CREDIT_BONUS,
            amount=amount,
            balance_after=balance.get_total_balance(),
            description=description or f"ボーナス{amount}クレジット付与",
        )
        self._transactions.append(transaction)
        self._save_transactions()

        logger.info(
            f"ボーナスクレジット付与: {transaction.transaction_id} "
            f"(user={user_id}, amount={amount})"
        )
        return transaction

    def refund_credits(
        self,
        user_id: str,
        amount: int,
        reference_id: str = "",
        description: str = "",
    ) -> Optional[CreditTransaction]:
        """
        クレジットを返金

        Args:
            user_id: ユーザーID
            amount: 返金数
            reference_id: 参照ID
            description: 説明

        Returns:
            取引情報
        """
        balance = self.get_or_create_balance(user_id)

        # クレジット追加
        balance.add_credits(amount, is_bonus=False)
        self._save_balances()

        # 取引記録
        transaction = CreditTransaction(
            transaction_id=self._generate_transaction_id(),
            user_id=user_id,
            transaction_type=TransactionType.CREDIT_REFUND,
            amount=amount,
            balance_after=balance.get_total_balance(),
            reference_id=reference_id,
            description=description or f"{amount}クレジット返金",
        )
        self._transactions.append(transaction)
        self._save_transactions()

        logger.info(
            f"クレジット返金: {transaction.transaction_id} "
            f"(user={user_id}, amount={amount})"
        )
        return transaction

    def get_transactions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[TransactionType] = None,
    ) -> list[CreditTransaction]:
        """
        取引履歴を取得

        Args:
            user_id: ユーザーID
            limit: 取得件数
            offset: オフセット
            transaction_type: タイプでフィルタ

        Returns:
            取引リスト
        """
        transactions = [
            t for t in self._transactions
            if t.user_id == user_id
        ]

        if transaction_type:
            transactions = [
                t for t in transactions
                if t.transaction_type == transaction_type
            ]

        # 新しい順にソート
        transactions.sort(key=lambda t: t.created_at, reverse=True)

        return transactions[offset:offset + limit]

    def get_packages(self) -> dict:
        """利用可能なクレジットパッケージを取得"""
        return {
            pkg_id: {
                "package_id": pkg_id,
                "credits": pkg["credits"],
                "bonus_credits": pkg["bonus_credits"],
                "total_credits": pkg["credits"] + pkg["bonus_credits"],
                "price_usd": str(pkg["price_usd"]),
                "description": pkg["description"],
            }
            for pkg_id, pkg in CREDIT_PACKAGES.items()
        }


# シングルトンインスタンス
_manager: Optional[CreditManager] = None


def get_credit_manager() -> CreditManager:
    """CreditManagerのシングルトンを取得"""
    global _manager
    if _manager is None:
        _manager = CreditManager()
    return _manager
