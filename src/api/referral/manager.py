# -*- coding: utf-8 -*-
"""
VisionCraftAI - リファラルマネージャー

紹介コードの生成、検証、報酬付与を管理します。
"""

import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    REFERRAL_REWARDS,
    Referral,
    ReferralCode,
    ReferralStats,
    ReferralStatus,
)


class ReferralManager:
    """リファラル管理クラス"""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        初期化

        Args:
            storage_path: データ保存先パス（None=メモリのみ）
        """
        self.storage_path = storage_path
        self._codes: dict[str, ReferralCode] = {}  # code -> ReferralCode
        self._codes_by_id: dict[str, ReferralCode] = {}  # code_id -> ReferralCode
        self._referrals: dict[str, Referral] = {}  # referral_id -> Referral
        self._user_codes: dict[str, str] = {}  # user_id -> code_id

        if storage_path:
            self._load()

    def _load(self) -> None:
        """データをストレージから読み込み"""
        if not self.storage_path:
            return

        codes_file = self.storage_path / "referral_codes.json"
        referrals_file = self.storage_path / "referrals.json"

        if codes_file.exists():
            with open(codes_file, encoding="utf-8") as f:
                data = json.load(f)
                for code_data in data.get("codes", []):
                    code = ReferralCode.from_dict(code_data)
                    self._codes[code.code] = code
                    self._codes_by_id[code.code_id] = code
                    self._user_codes[code.owner_user_id] = code.code_id

        if referrals_file.exists():
            with open(referrals_file, encoding="utf-8") as f:
                data = json.load(f)
                for ref_data in data.get("referrals", []):
                    referral = Referral.from_dict(ref_data)
                    self._referrals[referral.referral_id] = referral

    def _save(self) -> None:
        """データをストレージに保存"""
        if not self.storage_path:
            return

        self.storage_path.mkdir(parents=True, exist_ok=True)

        codes_file = self.storage_path / "referral_codes.json"
        with open(codes_file, "w", encoding="utf-8") as f:
            json.dump(
                {"codes": [c.to_dict() for c in self._codes.values()]},
                f,
                ensure_ascii=False,
                indent=2,
            )

        referrals_file = self.storage_path / "referrals.json"
        with open(referrals_file, "w", encoding="utf-8") as f:
            json.dump(
                {"referrals": [r.to_dict() for r in self._referrals.values()]},
                f,
                ensure_ascii=False,
                indent=2,
            )

    def create_code(
        self,
        owner_user_id: str,
        owner_api_key_id: str = "",
        reward_type: str = "default",
        max_uses: int = 0,
        expires_at: Optional[str] = None,
    ) -> ReferralCode:
        """
        新しい紹介コードを作成

        Args:
            owner_user_id: コード所有者のユーザーID
            owner_api_key_id: 所有者のAPIキーID
            reward_type: 報酬タイプ（default, premium）
            max_uses: 最大使用回数（0=無制限）
            expires_at: 有効期限

        Returns:
            ReferralCode: 作成された紹介コード
        """
        # 既存コードがあれば返す
        if owner_user_id in self._user_codes:
            code_id = self._user_codes[owner_user_id]
            if code_id in self._codes_by_id:
                return self._codes_by_id[code_id]

        # 報酬設定を取得
        rewards = REFERRAL_REWARDS.get(reward_type, REFERRAL_REWARDS["default"])

        # 新しいコードを生成
        code = ReferralCode.generate(
            owner_user_id=owner_user_id,
            owner_api_key_id=owner_api_key_id,
            referrer_reward_credits=rewards["referrer_credits"],
            referee_reward_credits=rewards["referee_credits"],
            max_uses=max_uses,
            expires_at=expires_at,
        )

        # 保存
        self._codes[code.code] = code
        self._codes_by_id[code.code_id] = code
        self._user_codes[owner_user_id] = code.code_id
        self._save()

        return code

    def get_code(self, code: str) -> Optional[ReferralCode]:
        """
        紹介コードを取得

        Args:
            code: 紹介コード文字列

        Returns:
            ReferralCode or None: 紹介コード
        """
        return self._codes.get(code.upper())

    def get_code_by_id(self, code_id: str) -> Optional[ReferralCode]:
        """
        コードIDで紹介コードを取得

        Args:
            code_id: コードID

        Returns:
            ReferralCode or None: 紹介コード
        """
        return self._codes_by_id.get(code_id)

    def get_user_code(self, user_id: str) -> Optional[ReferralCode]:
        """
        ユーザーの紹介コードを取得

        Args:
            user_id: ユーザーID

        Returns:
            ReferralCode or None: 紹介コード
        """
        code_id = self._user_codes.get(user_id)
        if code_id:
            return self._codes_by_id.get(code_id)
        return None

    def apply_code(
        self,
        code: str,
        referee_user_id: str,
        referee_api_key_id: str = "",
    ) -> tuple[bool, str, Optional[Referral]]:
        """
        紹介コードを適用

        Args:
            code: 紹介コード
            referee_user_id: 被紹介者のユーザーID
            referee_api_key_id: 被紹介者のAPIキーID

        Returns:
            tuple[bool, str, Optional[Referral]]: (成功か, メッセージ, Referral)
        """
        # コードを取得
        ref_code = self.get_code(code)
        if not ref_code:
            return False, "無効な紹介コードです", None

        # コードの有効性をチェック
        is_valid, reason = ref_code.is_valid()
        if not is_valid:
            return False, reason, None

        # 自己紹介防止
        if ref_code.owner_user_id == referee_user_id:
            return False, "自分自身の紹介コードは使用できません", None

        # 既に紹介済みかチェック
        for referral in self._referrals.values():
            if referral.referee_user_id == referee_user_id:
                return False, "既に他の紹介コードを使用済みです", None

        # コードを使用
        if not ref_code.use():
            return False, "紹介コードの使用に失敗しました", None

        # リファラルレコードを作成
        referral_id = f"rfr_{secrets.token_hex(8)}"
        referral = Referral(
            referral_id=referral_id,
            referral_code_id=ref_code.code_id,
            referral_code=ref_code.code,
            referrer_user_id=ref_code.owner_user_id,
            referrer_api_key_id=ref_code.owner_api_key_id,
            referee_user_id=referee_user_id,
            referee_api_key_id=referee_api_key_id,
            referrer_reward_credits=ref_code.referrer_reward_credits,
            referee_reward_credits=ref_code.referee_reward_credits,
        )

        # 登録時点で条件達成とする（signup条件）
        referral.mark_qualified()

        self._referrals[referral_id] = referral
        self._save()

        return True, "紹介コードが適用されました", referral

    def get_referral(self, referral_id: str) -> Optional[Referral]:
        """リファラルを取得"""
        return self._referrals.get(referral_id)

    def get_user_referrals(
        self,
        user_id: str,
        as_referrer: bool = True,
    ) -> list[Referral]:
        """
        ユーザーのリファラル一覧を取得

        Args:
            user_id: ユーザーID
            as_referrer: 紹介者として検索するか

        Returns:
            list[Referral]: リファラル一覧
        """
        referrals = []
        for referral in self._referrals.values():
            if as_referrer:
                if referral.referrer_user_id == user_id:
                    referrals.append(referral)
            else:
                if referral.referee_user_id == user_id:
                    referrals.append(referral)
        return referrals

    def get_pending_rewards(self, user_id: str) -> list[Referral]:
        """
        報酬付与待ちのリファラルを取得

        Args:
            user_id: ユーザーID

        Returns:
            list[Referral]: 報酬付与待ちリファラル
        """
        pending = []
        for referral in self._referrals.values():
            # 紹介者として報酬待ち
            if (
                referral.referrer_user_id == user_id
                and referral.status == ReferralStatus.QUALIFIED
                and not referral.referrer_rewarded_at
            ):
                pending.append(referral)
            # 被紹介者として報酬待ち
            if (
                referral.referee_user_id == user_id
                and referral.status == ReferralStatus.QUALIFIED
                and not referral.referee_rewarded_at
            ):
                pending.append(referral)
        return pending

    def mark_reward_given(
        self,
        referral_id: str,
        for_referrer: bool = True,
    ) -> bool:
        """
        報酬付与済みとしてマーク

        Args:
            referral_id: リファラルID
            for_referrer: 紹介者への報酬か

        Returns:
            bool: 成功か
        """
        referral = self._referrals.get(referral_id)
        if not referral:
            return False

        referral.mark_rewarded(for_referrer)
        self._save()
        return True

    def get_stats(self, user_id: str) -> ReferralStats:
        """
        ユーザーのリファラル統計を取得

        Args:
            user_id: ユーザーID

        Returns:
            ReferralStats: 統計情報
        """
        referrals = self.get_user_referrals(user_id, as_referrer=True)

        total = len(referrals)
        successful = sum(
            1 for r in referrals if r.status == ReferralStatus.REWARDED
        )
        pending = sum(
            1 for r in referrals
            if r.status in (ReferralStatus.PENDING, ReferralStatus.QUALIFIED)
        )
        credits_earned = sum(
            r.referrer_reward_credits
            for r in referrals
            if r.referrer_rewarded_at
        )

        # ランキング計算（簡易版）
        user_success_counts: dict[str, int] = {}
        for ref in self._referrals.values():
            if ref.status == ReferralStatus.REWARDED:
                uid = ref.referrer_user_id
                user_success_counts[uid] = user_success_counts.get(uid, 0) + 1

        sorted_users = sorted(
            user_success_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        rank = 1
        for i, (uid, _) in enumerate(sorted_users):
            if uid == user_id:
                rank = i + 1
                break

        return ReferralStats(
            user_id=user_id,
            total_referrals=total,
            successful_referrals=successful,
            pending_referrals=pending,
            total_credits_earned=credits_earned,
            rank=rank if user_id in user_success_counts else 0,
        )

    def get_leaderboard(self, limit: int = 10) -> list[dict]:
        """
        リファラルランキングを取得

        Args:
            limit: 取得件数

        Returns:
            list[dict]: ランキング
        """
        user_stats: dict[str, dict] = {}

        for ref in self._referrals.values():
            if ref.status == ReferralStatus.REWARDED:
                uid = ref.referrer_user_id
                if uid not in user_stats:
                    user_stats[uid] = {
                        "user_id": uid,
                        "successful_referrals": 0,
                        "total_credits_earned": 0,
                    }
                user_stats[uid]["successful_referrals"] += 1
                user_stats[uid]["total_credits_earned"] += ref.referrer_reward_credits

        sorted_stats = sorted(
            user_stats.values(),
            key=lambda x: x["successful_referrals"],
            reverse=True,
        )

        return sorted_stats[:limit]


# グローバルインスタンス
_referral_manager: Optional[ReferralManager] = None


def get_referral_manager(storage_path: Optional[Path] = None) -> ReferralManager:
    """
    リファラルマネージャーのグローバルインスタンスを取得

    Args:
        storage_path: データ保存先パス

    Returns:
        ReferralManager: リファラルマネージャー
    """
    global _referral_manager
    if _referral_manager is None:
        _referral_manager = ReferralManager(storage_path)
    return _referral_manager
