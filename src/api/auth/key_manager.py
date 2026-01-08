# -*- coding: utf-8 -*-
"""
VisionCraftAI - APIキー管理

APIキーの生成、検証、保存を管理します。
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.api.auth.models import APIKey, APIKeyTier

logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    APIキー管理クラス

    JSONファイルベースのシンプルな永続化を実装。
    本番環境ではデータベース（Redis/PostgreSQL等）に移行推奨。
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        初期化

        Args:
            storage_path: キー保存ファイルパス
        """
        self._storage_path = storage_path or Path("data/api_keys.json")
        self._keys: dict[str, APIKey] = {}
        self._hash_to_key_id: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """ストレージからキーを読み込む"""
        if not self._storage_path.exists():
            logger.info(f"APIキーストレージが存在しません: {self._storage_path}")
            return

        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for key_data in data.get("keys", []):
                api_key = APIKey.from_dict(key_data)
                self._keys[api_key.key_id] = api_key
                self._hash_to_key_id[api_key.key_hash] = api_key.key_id

            logger.info(f"{len(self._keys)}個のAPIキーを読み込みました")
        except Exception as e:
            logger.error(f"APIキーの読み込みに失敗: {e}")

    def _save(self) -> None:
        """ストレージにキーを保存"""
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "keys": [
                    key.to_dict(include_hash=True)
                    for key in self._keys.values()
                ],
            }

            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"APIキーを保存しました: {self._storage_path}")
        except Exception as e:
            logger.error(f"APIキーの保存に失敗: {e}")
            raise

    def create_key(
        self,
        tier: APIKeyTier = APIKeyTier.FREE,
        name: str = "",
        description: str = "",
        owner_id: str = "",
        expires_at: Optional[str] = None,
        allowed_ips: Optional[list[str]] = None,
    ) -> tuple[APIKey, str]:
        """
        新しいAPIキーを作成

        Args:
            tier: プラン階層
            name: キー名
            description: 説明
            owner_id: オーナーID
            expires_at: 有効期限（ISO形式）
            allowed_ips: 許可IPリスト

        Returns:
            tuple[APIKey, str]: (APIKeyインスタンス, 生のAPIキー文字列)
        """
        api_key, raw_key = APIKey.generate(
            tier=tier,
            name=name,
            description=description,
            owner_id=owner_id,
            expires_at=expires_at,
            allowed_ips=allowed_ips,
        )

        self._keys[api_key.key_id] = api_key
        self._hash_to_key_id[api_key.key_hash] = api_key.key_id
        self._save()

        logger.info(f"新しいAPIキーを作成: {api_key.key_id} (tier={tier.value})")
        return api_key, raw_key

    def validate_key(self, raw_key: str, ip: Optional[str] = None) -> tuple[bool, Optional[APIKey], str]:
        """
        APIキーを検証

        Args:
            raw_key: 生のAPIキー文字列
            ip: クライアントIPアドレス（オプション）

        Returns:
            tuple[bool, Optional[APIKey], str]: (有効か, APIKeyインスタンス, 理由)
        """
        if not raw_key:
            return False, None, "APIキーが提供されていません"

        # ハッシュ化して検索
        key_hash = APIKey.hash_key(raw_key)
        key_id = self._hash_to_key_id.get(key_hash)

        if not key_id:
            return False, None, "無効なAPIキーです"

        api_key = self._keys.get(key_id)
        if not api_key:
            return False, None, "APIキーが見つかりません"

        # 有効性チェック
        is_valid, reason = api_key.is_valid()
        if not is_valid:
            return False, api_key, reason

        # IPチェック
        if ip and not api_key.check_ip(ip):
            return False, api_key, f"IPアドレス {ip} は許可されていません"

        # 最終使用日時更新
        api_key.update_last_used()
        self._save()

        return True, api_key, "OK"

    def get_key(self, key_id: str) -> Optional[APIKey]:
        """
        key_idでAPIキーを取得

        Args:
            key_id: キーID

        Returns:
            APIKeyインスタンス（存在しない場合はNone）
        """
        return self._keys.get(key_id)

    def get_key_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """
        ハッシュでAPIキーを取得

        Args:
            key_hash: キーハッシュ

        Returns:
            APIKeyインスタンス（存在しない場合はNone）
        """
        key_id = self._hash_to_key_id.get(key_hash)
        if key_id:
            return self._keys.get(key_id)
        return None

    def list_keys(
        self,
        owner_id: Optional[str] = None,
        tier: Optional[APIKeyTier] = None,
        active_only: bool = True,
    ) -> list[APIKey]:
        """
        APIキー一覧を取得

        Args:
            owner_id: オーナーIDでフィルタ
            tier: プラン階層でフィルタ
            active_only: アクティブなキーのみ

        Returns:
            APIKeyのリスト
        """
        keys = list(self._keys.values())

        if owner_id:
            keys = [k for k in keys if k.owner_id == owner_id]

        if tier:
            keys = [k for k in keys if k.tier == tier]

        if active_only:
            keys = [k for k in keys if k.is_active]

        return keys

    def update_key(
        self,
        key_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        tier: Optional[APIKeyTier] = None,
        expires_at: Optional[str] = None,
        allowed_ips: Optional[list[str]] = None,
    ) -> Optional[APIKey]:
        """
        APIキーを更新

        Args:
            key_id: キーID
            その他: 更新フィールド

        Returns:
            更新後のAPIKeyインスタンス（存在しない場合はNone）
        """
        api_key = self._keys.get(key_id)
        if not api_key:
            return None

        if name is not None:
            api_key.name = name
        if description is not None:
            api_key.description = description
        if is_active is not None:
            api_key.is_active = is_active
        if tier is not None:
            api_key.tier = tier
            # クォータも更新
            new_quota = api_key.quota.__class__.for_tier(tier)
            # 使用量は維持
            new_quota.monthly_used = api_key.quota.monthly_used
            new_quota.daily_used = api_key.quota.daily_used
            new_quota.last_monthly_reset = api_key.quota.last_monthly_reset
            new_quota.last_daily_reset = api_key.quota.last_daily_reset
            api_key.quota = new_quota
        if expires_at is not None:
            api_key.expires_at = expires_at
        if allowed_ips is not None:
            api_key.allowed_ips = allowed_ips

        self._save()
        logger.info(f"APIキーを更新: {key_id}")
        return api_key

    def revoke_key(self, key_id: str) -> bool:
        """
        APIキーを無効化

        Args:
            key_id: キーID

        Returns:
            成功したかどうか
        """
        api_key = self._keys.get(key_id)
        if not api_key:
            return False

        api_key.is_active = False
        self._save()
        logger.info(f"APIキーを無効化: {key_id}")
        return True

    def delete_key(self, key_id: str) -> bool:
        """
        APIキーを削除

        Args:
            key_id: キーID

        Returns:
            成功したかどうか
        """
        api_key = self._keys.get(key_id)
        if not api_key:
            return False

        del self._keys[key_id]
        if api_key.key_hash in self._hash_to_key_id:
            del self._hash_to_key_id[api_key.key_hash]

        self._save()
        logger.warning(f"APIキーを削除: {key_id}")
        return True

    def record_usage(self, key_id: str, count: int = 1) -> tuple[bool, str]:
        """
        使用量を記録

        Args:
            key_id: キーID
            count: 使用数

        Returns:
            tuple[bool, str]: (成功か, メッセージ)
        """
        api_key = self._keys.get(key_id)
        if not api_key:
            return False, "APIキーが見つかりません"

        # クォータチェック
        can_use, reason = api_key.quota.can_generate(count)
        if not can_use:
            return False, reason

        # 使用量記録
        api_key.quota.record_usage(count)
        self._save()

        return True, "OK"

    def get_quota_status(self, key_id: str) -> Optional[dict]:
        """
        クォータ状況を取得

        Args:
            key_id: キーID

        Returns:
            クォータ情報（存在しない場合はNone）
        """
        api_key = self._keys.get(key_id)
        if not api_key:
            return None

        remaining = api_key.quota.get_remaining()
        return {
            "key_id": key_id,
            "tier": api_key.tier.value,
            **remaining,
            "max_width": api_key.quota.max_width,
            "max_height": api_key.quota.max_height,
            "max_batch_size": api_key.quota.max_batch_size,
            "priority_processing": api_key.quota.priority_processing,
        }


# シングルトンインスタンス
_manager: Optional[APIKeyManager] = None


def get_key_manager() -> APIKeyManager:
    """APIKeyManagerのシングルトンを取得"""
    global _manager
    if _manager is None:
        _manager = APIKeyManager()
    return _manager
