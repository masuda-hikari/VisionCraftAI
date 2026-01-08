# -*- coding: utf-8 -*-
"""
VisionCraftAI - 認証モデル定義

APIキーとクォータのデータモデルを定義します。
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class APIKeyTier(str, Enum):
    """APIキーのプラン階層"""
    FREE = "free"           # 無料: 月5生成、低解像度
    BASIC = "basic"         # Basic: 月100枚、標準解像度 $9.99/月
    PRO = "pro"             # Pro: 月500枚、高解像度、優先処理 $29.99/月
    ENTERPRISE = "enterprise"  # Enterprise: 無制限API、カスタム


@dataclass
class UsageQuota:
    """使用量クォータ"""
    # 月間制限
    monthly_limit: int = 5
    monthly_used: int = 0

    # 日間制限（バースト防止）
    daily_limit: int = 10
    daily_used: int = 0

    # レート制限（1分あたり）
    rate_limit_per_minute: int = 10

    # 最大解像度
    max_width: int = 512
    max_height: int = 512

    # バッチ処理制限
    max_batch_size: int = 5

    # 優先処理フラグ
    priority_processing: bool = False

    # リセット日
    last_monthly_reset: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-01")
    )
    last_daily_reset: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d")
    )

    @classmethod
    def for_tier(cls, tier: APIKeyTier) -> "UsageQuota":
        """プラン階層に応じたクォータを作成"""
        quotas = {
            APIKeyTier.FREE: cls(
                monthly_limit=5,
                daily_limit=3,
                rate_limit_per_minute=5,
                max_width=512,
                max_height=512,
                max_batch_size=1,
                priority_processing=False,
            ),
            APIKeyTier.BASIC: cls(
                monthly_limit=100,
                daily_limit=20,
                rate_limit_per_minute=15,
                max_width=1024,
                max_height=1024,
                max_batch_size=10,
                priority_processing=False,
            ),
            APIKeyTier.PRO: cls(
                monthly_limit=500,
                daily_limit=50,
                rate_limit_per_minute=30,
                max_width=2048,
                max_height=2048,
                max_batch_size=50,
                priority_processing=True,
            ),
            APIKeyTier.ENTERPRISE: cls(
                monthly_limit=999999,  # 実質無制限
                daily_limit=999999,
                rate_limit_per_minute=60,
                max_width=4096,
                max_height=4096,
                max_batch_size=100,
                priority_processing=True,
            ),
        }
        return quotas.get(tier, quotas[APIKeyTier.FREE])

    def check_monthly_reset(self) -> bool:
        """月次リセットが必要かチェックし、必要なら実行"""
        current_month = datetime.now().strftime("%Y-%m-01")
        if self.last_monthly_reset != current_month:
            self.monthly_used = 0
            self.last_monthly_reset = current_month
            return True
        return False

    def check_daily_reset(self) -> bool:
        """日次リセットが必要かチェックし、必要なら実行"""
        current_day = datetime.now().strftime("%Y-%m-%d")
        if self.last_daily_reset != current_day:
            self.daily_used = 0
            self.last_daily_reset = current_day
            return True
        return False

    def can_generate(self, count: int = 1) -> tuple[bool, str]:
        """
        生成可能かチェック

        Returns:
            tuple[bool, str]: (生成可能か, 理由)
        """
        # リセットチェック
        self.check_monthly_reset()
        self.check_daily_reset()

        # 月間制限チェック
        if self.monthly_used + count > self.monthly_limit:
            remaining = self.monthly_limit - self.monthly_used
            return False, f"月間制限超過（残り: {remaining}枚）"

        # 日間制限チェック
        if self.daily_used + count > self.daily_limit:
            remaining = self.daily_limit - self.daily_used
            return False, f"日間制限超過（残り: {remaining}枚）"

        return True, "OK"

    def record_usage(self, count: int = 1) -> None:
        """使用量を記録"""
        self.check_monthly_reset()
        self.check_daily_reset()
        self.monthly_used += count
        self.daily_used += count

    def get_remaining(self) -> dict:
        """残り使用量を取得"""
        self.check_monthly_reset()
        self.check_daily_reset()
        return {
            "monthly_remaining": max(0, self.monthly_limit - self.monthly_used),
            "daily_remaining": max(0, self.daily_limit - self.daily_used),
            "monthly_limit": self.monthly_limit,
            "daily_limit": self.daily_limit,
        }


@dataclass
class APIKey:
    """APIキーモデル"""
    # キー識別子（公開）
    key_id: str

    # キーハッシュ（保存用）
    key_hash: str

    # プラン階層
    tier: APIKeyTier = APIKeyTier.FREE

    # クォータ
    quota: UsageQuota = field(default_factory=UsageQuota)

    # メタデータ
    name: str = ""
    description: str = ""
    owner_id: str = ""

    # 有効期限（None=無期限）
    expires_at: Optional[str] = None

    # 状態
    is_active: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    last_used_at: Optional[str] = None

    # 許可されたIPアドレス（空=全許可）
    allowed_ips: list[str] = field(default_factory=list)

    @classmethod
    def generate(
        cls,
        tier: APIKeyTier = APIKeyTier.FREE,
        name: str = "",
        description: str = "",
        owner_id: str = "",
        expires_at: Optional[str] = None,
        allowed_ips: Optional[list[str]] = None,
    ) -> tuple["APIKey", str]:
        """
        新しいAPIキーを生成

        Returns:
            tuple[APIKey, str]: (APIKeyインスタンス, 生のAPIキー文字列)
        """
        # キーID（プレフィックス付き）
        key_id = f"vca_{secrets.token_hex(8)}"

        # 秘密キー
        secret = secrets.token_hex(24)
        raw_key = f"{key_id}.{secret}"

        # ハッシュ化
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # クォータ作成
        quota = UsageQuota.for_tier(tier)

        return cls(
            key_id=key_id,
            key_hash=key_hash,
            tier=tier,
            quota=quota,
            name=name,
            description=description,
            owner_id=owner_id,
            expires_at=expires_at,
            allowed_ips=allowed_ips or [],
        ), raw_key

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """APIキーをハッシュ化"""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @staticmethod
    def extract_key_id(raw_key: str) -> str:
        """生のAPIキーからkey_idを抽出"""
        parts = raw_key.split(".")
        return parts[0] if parts else ""

    def is_valid(self) -> tuple[bool, str]:
        """
        キーの有効性をチェック

        Returns:
            tuple[bool, str]: (有効か, 理由)
        """
        if not self.is_active:
            return False, "APIキーが無効化されています"

        if self.expires_at:
            if datetime.fromisoformat(self.expires_at) < datetime.now():
                return False, "APIキーの有効期限が切れています"

        return True, "OK"

    def check_ip(self, ip: str) -> bool:
        """IPアドレスが許可されているかチェック"""
        if not self.allowed_ips:
            return True  # 制限なし
        return ip in self.allowed_ips

    def update_last_used(self) -> None:
        """最終使用日時を更新"""
        self.last_used_at = datetime.now().isoformat()

    def to_dict(self, include_hash: bool = False) -> dict:
        """辞書形式に変換"""
        data = {
            "key_id": self.key_id,
            "tier": self.tier.value,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "expires_at": self.expires_at,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "allowed_ips": self.allowed_ips,
            "quota": {
                "monthly_limit": self.quota.monthly_limit,
                "monthly_used": self.quota.monthly_used,
                "daily_limit": self.quota.daily_limit,
                "daily_used": self.quota.daily_used,
                "rate_limit_per_minute": self.quota.rate_limit_per_minute,
                "max_width": self.quota.max_width,
                "max_height": self.quota.max_height,
                "max_batch_size": self.quota.max_batch_size,
                "priority_processing": self.quota.priority_processing,
            },
        }
        if include_hash:
            data["key_hash"] = self.key_hash
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "APIKey":
        """辞書からインスタンスを作成"""
        quota_data = data.get("quota", {})
        quota = UsageQuota(
            monthly_limit=quota_data.get("monthly_limit", 5),
            monthly_used=quota_data.get("monthly_used", 0),
            daily_limit=quota_data.get("daily_limit", 10),
            daily_used=quota_data.get("daily_used", 0),
            rate_limit_per_minute=quota_data.get("rate_limit_per_minute", 10),
            max_width=quota_data.get("max_width", 512),
            max_height=quota_data.get("max_height", 512),
            max_batch_size=quota_data.get("max_batch_size", 5),
            priority_processing=quota_data.get("priority_processing", False),
            last_monthly_reset=quota_data.get(
                "last_monthly_reset",
                datetime.now().strftime("%Y-%m-01")
            ),
            last_daily_reset=quota_data.get(
                "last_daily_reset",
                datetime.now().strftime("%Y-%m-%d")
            ),
        )

        return cls(
            key_id=data["key_id"],
            key_hash=data.get("key_hash", ""),
            tier=APIKeyTier(data.get("tier", "free")),
            quota=quota,
            name=data.get("name", ""),
            description=data.get("description", ""),
            owner_id=data.get("owner_id", ""),
            expires_at=data.get("expires_at"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_used_at=data.get("last_used_at"),
            allowed_ips=data.get("allowed_ips", []),
        )
