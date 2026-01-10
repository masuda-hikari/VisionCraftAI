# -*- coding: utf-8 -*-
"""
VisionCraftAI - オンボーディングマネージャー

オンボーディング進捗と無料トライアルを管理します。
"""

import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import (
    ONBOARDING_HELP,
    TRIAL_CONFIGS,
    FreeTrial,
    OnboardingProgress,
    OnboardingStep,
    TrialStatus,
)


class OnboardingManager:
    """オンボーディング管理クラス"""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        初期化

        Args:
            storage_path: データ保存先パス（None=メモリのみ）
        """
        self.storage_path = storage_path
        self._progress: dict[str, OnboardingProgress] = {}  # user_id -> progress
        self._trials: dict[str, FreeTrial] = {}  # trial_id -> trial
        self._user_trials: dict[str, str] = {}  # user_id -> trial_id

        if storage_path:
            self._load()

    def _load(self) -> None:
        """データをストレージから読み込み"""
        if not self.storage_path:
            return

        progress_file = self.storage_path / "onboarding_progress.json"
        trials_file = self.storage_path / "trials.json"

        if progress_file.exists():
            with open(progress_file, encoding="utf-8") as f:
                data = json.load(f)
                for prog_data in data.get("progress", []):
                    progress = OnboardingProgress.from_dict(prog_data)
                    self._progress[progress.user_id] = progress

        if trials_file.exists():
            with open(trials_file, encoding="utf-8") as f:
                data = json.load(f)
                for trial_data in data.get("trials", []):
                    trial = FreeTrial.from_dict(trial_data)
                    self._trials[trial.trial_id] = trial
                    self._user_trials[trial.user_id] = trial.trial_id

    def _save(self) -> None:
        """データをストレージに保存"""
        if not self.storage_path:
            return

        self.storage_path.mkdir(parents=True, exist_ok=True)

        progress_file = self.storage_path / "onboarding_progress.json"
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(
                {"progress": [p.to_dict() for p in self._progress.values()]},
                f,
                ensure_ascii=False,
                indent=2,
            )

        trials_file = self.storage_path / "trials.json"
        with open(trials_file, "w", encoding="utf-8") as f:
            json.dump(
                {"trials": [t.to_dict() for t in self._trials.values()]},
                f,
                ensure_ascii=False,
                indent=2,
            )

    # === オンボーディング進捗 ===

    def get_or_create_progress(
        self,
        user_id: str,
        api_key_id: str = "",
    ) -> OnboardingProgress:
        """
        オンボーディング進捗を取得（なければ作成）

        Args:
            user_id: ユーザーID
            api_key_id: APIキーID

        Returns:
            OnboardingProgress: オンボーディング進捗
        """
        if user_id not in self._progress:
            progress = OnboardingProgress(
                user_id=user_id,
                api_key_id=api_key_id,
            )
            self._progress[user_id] = progress
            self._save()
        return self._progress[user_id]

    def get_progress(self, user_id: str) -> Optional[OnboardingProgress]:
        """オンボーディング進捗を取得"""
        return self._progress.get(user_id)

    def complete_step(
        self,
        user_id: str,
        step: OnboardingStep,
    ) -> OnboardingProgress:
        """ステップを完了としてマーク"""
        progress = self.get_or_create_progress(user_id)
        progress.complete_step(step)
        self._save()
        return progress

    def complete_checklist_item(
        self,
        user_id: str,
        item: str,
    ) -> tuple[bool, OnboardingProgress]:
        """チェックリスト項目を完了"""
        progress = self.get_or_create_progress(user_id)
        success = progress.complete_checklist_item(item)
        if success:
            self._save()
        return success, progress

    def get_next_step_hint(
        self,
        user_id: str,
    ) -> dict:
        """次のステップのヒントを取得"""
        progress = self.get_or_create_progress(user_id)
        step = progress.current_step
        help_info = ONBOARDING_HELP.get(step, {})
        return {
            "step": step.value,
            "title": help_info.get("title", ""),
            "description": help_info.get("description", ""),
            "action": help_info.get("action", ""),
            "completion_rate": progress.get_completion_rate(),
        }

    # === 無料トライアル ===

    def start_trial(
        self,
        user_id: str,
        api_key_id: str = "",
        trial_type: str = "default",
    ) -> tuple[bool, str, Optional[FreeTrial]]:
        """
        無料トライアルを開始

        Args:
            user_id: ユーザーID
            api_key_id: APIキーID
            trial_type: トライアルタイプ（default, extended, premium）

        Returns:
            tuple[bool, str, Optional[FreeTrial]]: (成功か, メッセージ, トライアル)
        """
        # 既存トライアルチェック
        if user_id in self._user_trials:
            existing_trial = self._trials.get(self._user_trials[user_id])
            if existing_trial:
                if existing_trial.is_active():
                    return False, "既にアクティブなトライアルがあります", existing_trial
                if existing_trial.status == TrialStatus.CONVERTED:
                    return False, "既に有料プランに転換済みです", None

        # トライアル設定を取得
        config = TRIAL_CONFIGS.get(trial_type, TRIAL_CONFIGS["default"])

        # トライアル作成
        trial_id = f"trial_{secrets.token_hex(8)}"
        trial = FreeTrial(
            trial_id=trial_id,
            user_id=user_id,
            api_key_id=api_key_id,
            plan_id=config["plan_id"],
            duration_days=config["duration_days"],
            credits_granted=config["credits_granted"],
            expires_at=(datetime.now() + timedelta(days=config["duration_days"])).isoformat(),
        )

        self._trials[trial_id] = trial
        self._user_trials[user_id] = trial_id
        self._save()

        return True, "トライアルを開始しました", trial

    def get_trial(self, user_id: str) -> Optional[FreeTrial]:
        """ユーザーのトライアルを取得"""
        trial_id = self._user_trials.get(user_id)
        if trial_id:
            trial = self._trials.get(trial_id)
            # 期限切れチェック
            if trial and trial.status == TrialStatus.ACTIVE:
                if datetime.fromisoformat(trial.expires_at) < datetime.now():
                    trial.expire()
                    self._save()
            return trial
        return None

    def use_trial_credits(
        self,
        user_id: str,
        amount: int = 1,
    ) -> tuple[bool, str]:
        """トライアルクレジットを使用"""
        trial = self.get_trial(user_id)
        if not trial:
            return False, "トライアルがありません"
        if not trial.is_active():
            return False, "トライアルが期限切れです"
        if not trial.use_credits(amount):
            return False, "クレジットが不足しています"
        self._save()
        return True, "クレジットを使用しました"

    def convert_trial(
        self,
        user_id: str,
        plan_id: str,
    ) -> tuple[bool, str]:
        """トライアルを有料プランに転換"""
        trial = self.get_trial(user_id)
        if not trial:
            return False, "トライアルがありません"
        if trial.status == TrialStatus.CONVERTED:
            return False, "既に転換済みです"

        trial.convert(plan_id)
        self._save()
        return True, f"プラン {plan_id} に転換しました"

    def get_trial_stats(self) -> dict:
        """トライアル統計を取得"""
        total = len(self._trials)
        active = sum(1 for t in self._trials.values() if t.is_active())
        converted = sum(1 for t in self._trials.values() if t.status == TrialStatus.CONVERTED)
        expired = sum(1 for t in self._trials.values() if t.status == TrialStatus.EXPIRED)

        conversion_rate = converted / total if total > 0 else 0.0

        return {
            "total_trials": total,
            "active_trials": active,
            "converted_trials": converted,
            "expired_trials": expired,
            "conversion_rate": conversion_rate,
        }

    def get_expiring_trials(self, within_days: int = 3) -> list[FreeTrial]:
        """間もなく期限切れのトライアルを取得"""
        threshold = datetime.now() + timedelta(days=within_days)
        expiring = []
        for trial in self._trials.values():
            if trial.is_active():
                expires = datetime.fromisoformat(trial.expires_at)
                if expires <= threshold:
                    expiring.append(trial)
        return expiring


# グローバルインスタンス
_onboarding_manager: Optional[OnboardingManager] = None


def get_onboarding_manager(storage_path: Optional[Path] = None) -> OnboardingManager:
    """
    オンボーディングマネージャーのグローバルインスタンスを取得

    Args:
        storage_path: データ保存先パス

    Returns:
        OnboardingManager: オンボーディングマネージャー
    """
    global _onboarding_manager
    if _onboarding_manager is None:
        _onboarding_manager = OnboardingManager(storage_path)
    return _onboarding_manager
