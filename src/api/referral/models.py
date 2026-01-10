# -*- coding: utf-8 -*-
"""
VisionCraftAI - リファラルモデル定義

紹介コード、紹介履歴、報酬のデータモデルを定義します。
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ReferralStatus(str, Enum):
    """リファラルステータス"""
    PENDING = "pending"          # 登録済み、条件未達成
    QUALIFIED = "qualified"      # 条件達成、報酬付与可能
    REWARDED = "rewarded"        # 報酬付与済み
    EXPIRED = "expired"          # 有効期限切れ
    CANCELLED = "cancelled"      # キャンセル


class ReferralRewardType(str, Enum):
    """報酬タイプ"""
    CREDITS = "credits"          # クレジット付与
    DISCOUNT = "discount"        # 割引クーポン
    UPGRADE = "upgrade"          # プランアップグレード
    EXTENDED_TRIAL = "extended_trial"  # 延長トライアル


@dataclass
class ReferralCode:
    """リファラルコード"""
    code_id: str                     # コードID
    code: str                        # 紹介コード（ユーザーに表示）
    owner_user_id: str               # コード所有者のユーザーID
    owner_api_key_id: str = ""       # 所有者のAPIキーID

    # 報酬設定
    referrer_reward_credits: int = 5     # 紹介者への報酬クレジット
    referee_reward_credits: int = 5      # 被紹介者への報酬クレジット

    # 使用制限
    max_uses: int = 0                # 最大使用回数（0=無制限）
    current_uses: int = 0            # 現在の使用回数

    # 有効期限
    expires_at: Optional[str] = None # 有効期限（None=無期限）

    # 状態
    is_active: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    @classmethod
    def generate(
        cls,
        owner_user_id: str,
        owner_api_key_id: str = "",
        referrer_reward_credits: int = 5,
        referee_reward_credits: int = 5,
        max_uses: int = 0,
        expires_at: Optional[str] = None,
    ) -> "ReferralCode":
        """
        新しいリファラルコードを生成

        Returns:
            ReferralCode: 生成されたリファラルコード
        """
        code_id = f"ref_{secrets.token_hex(8)}"
        # 読みやすいコード（大文字英数字8文字）
        code = secrets.token_hex(4).upper()

        return cls(
            code_id=code_id,
            code=code,
            owner_user_id=owner_user_id,
            owner_api_key_id=owner_api_key_id,
            referrer_reward_credits=referrer_reward_credits,
            referee_reward_credits=referee_reward_credits,
            max_uses=max_uses,
            expires_at=expires_at,
        )

    def is_valid(self) -> tuple[bool, str]:
        """
        コードの有効性をチェック

        Returns:
            tuple[bool, str]: (有効か, 理由)
        """
        if not self.is_active:
            return False, "紹介コードが無効化されています"

        if self.expires_at:
            if datetime.fromisoformat(self.expires_at) < datetime.now():
                return False, "紹介コードの有効期限が切れています"

        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False, "紹介コードの使用回数上限に達しました"

        return True, "OK"

    def use(self) -> bool:
        """コードを使用（使用回数をインクリメント）"""
        valid, _ = self.is_valid()
        if not valid:
            return False
        self.current_uses += 1
        return True

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "code_id": self.code_id,
            "code": self.code,
            "owner_user_id": self.owner_user_id,
            "owner_api_key_id": self.owner_api_key_id,
            "referrer_reward_credits": self.referrer_reward_credits,
            "referee_reward_credits": self.referee_reward_credits,
            "max_uses": self.max_uses,
            "current_uses": self.current_uses,
            "expires_at": self.expires_at,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReferralCode":
        """辞書からインスタンスを作成"""
        return cls(
            code_id=data["code_id"],
            code=data["code"],
            owner_user_id=data["owner_user_id"],
            owner_api_key_id=data.get("owner_api_key_id", ""),
            referrer_reward_credits=data.get("referrer_reward_credits", 5),
            referee_reward_credits=data.get("referee_reward_credits", 5),
            max_uses=data.get("max_uses", 0),
            current_uses=data.get("current_uses", 0),
            expires_at=data.get("expires_at"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


@dataclass
class Referral:
    """リファラル（紹介）記録"""
    referral_id: str                 # リファラルID
    referral_code_id: str            # 使用された紹介コードID
    referral_code: str               # 使用された紹介コード

    # 紹介者情報
    referrer_user_id: str            # 紹介者のユーザーID
    referrer_api_key_id: str = ""    # 紹介者のAPIキーID

    # 被紹介者情報
    referee_user_id: str = ""        # 被紹介者のユーザーID
    referee_api_key_id: str = ""     # 被紹介者のAPIキーID

    # ステータス
    status: ReferralStatus = ReferralStatus.PENDING

    # 報酬
    referrer_reward_credits: int = 0 # 紹介者への報酬クレジット
    referee_reward_credits: int = 0  # 被紹介者への報酬クレジット
    referrer_rewarded_at: Optional[str] = None
    referee_rewarded_at: Optional[str] = None

    # 条件達成（被紹介者の初回課金など）
    qualification_type: str = "signup"  # signup, first_payment, first_generate
    qualified_at: Optional[str] = None

    # 日時
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def mark_qualified(self) -> None:
        """条件達成としてマーク"""
        self.status = ReferralStatus.QUALIFIED
        self.qualified_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def mark_rewarded(self, for_referrer: bool = True) -> None:
        """報酬付与済みとしてマーク"""
        now = datetime.now().isoformat()
        if for_referrer:
            self.referrer_rewarded_at = now
        else:
            self.referee_rewarded_at = now

        # 両方に報酬付与済みならステータス更新
        if self.referrer_rewarded_at and self.referee_rewarded_at:
            self.status = ReferralStatus.REWARDED
        self.updated_at = now

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "referral_id": self.referral_id,
            "referral_code_id": self.referral_code_id,
            "referral_code": self.referral_code,
            "referrer_user_id": self.referrer_user_id,
            "referrer_api_key_id": self.referrer_api_key_id,
            "referee_user_id": self.referee_user_id,
            "referee_api_key_id": self.referee_api_key_id,
            "status": self.status.value,
            "referrer_reward_credits": self.referrer_reward_credits,
            "referee_reward_credits": self.referee_reward_credits,
            "referrer_rewarded_at": self.referrer_rewarded_at,
            "referee_rewarded_at": self.referee_rewarded_at,
            "qualification_type": self.qualification_type,
            "qualified_at": self.qualified_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Referral":
        """辞書からインスタンスを作成"""
        return cls(
            referral_id=data["referral_id"],
            referral_code_id=data["referral_code_id"],
            referral_code=data.get("referral_code", ""),
            referrer_user_id=data["referrer_user_id"],
            referrer_api_key_id=data.get("referrer_api_key_id", ""),
            referee_user_id=data.get("referee_user_id", ""),
            referee_api_key_id=data.get("referee_api_key_id", ""),
            status=ReferralStatus(data.get("status", "pending")),
            referrer_reward_credits=data.get("referrer_reward_credits", 0),
            referee_reward_credits=data.get("referee_reward_credits", 0),
            referrer_rewarded_at=data.get("referrer_rewarded_at"),
            referee_rewarded_at=data.get("referee_rewarded_at"),
            qualification_type=data.get("qualification_type", "signup"),
            qualified_at=data.get("qualified_at"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )


@dataclass
class ReferralStats:
    """リファラル統計"""
    user_id: str

    # 紹介実績
    total_referrals: int = 0         # 総紹介数
    successful_referrals: int = 0    # 成功した紹介数
    pending_referrals: int = 0       # 保留中の紹介数

    # 報酬
    total_credits_earned: int = 0    # 累計獲得クレジット

    # ランキング
    rank: int = 0                    # 紹介ランキング順位

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "user_id": self.user_id,
            "total_referrals": self.total_referrals,
            "successful_referrals": self.successful_referrals,
            "pending_referrals": self.pending_referrals,
            "total_credits_earned": self.total_credits_earned,
            "rank": self.rank,
        }


# リファラル報酬設定（デフォルト）
REFERRAL_REWARDS = {
    "default": {
        "referrer_credits": 5,       # 紹介者へのクレジット
        "referee_credits": 5,        # 被紹介者へのクレジット
        "qualification_type": "signup",  # 条件達成タイプ
    },
    "premium": {
        "referrer_credits": 10,
        "referee_credits": 10,
        "qualification_type": "first_payment",
    },
}
