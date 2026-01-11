# -*- coding: utf-8 -*-
"""
VisionCraftAI - オンボーディング・トライアルテスト
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta

from src.api.onboarding.models import (
    OnboardingProgress,
    OnboardingStep,
    FreeTrial,
    TrialStatus,
    TRIAL_CONFIGS,
    ONBOARDING_HELP,
)
from src.api.onboarding.manager import OnboardingManager


class TestOnboardingProgress:
    """OnboardingProgressモデルのテスト"""

    def test_create_progress(self):
        """進捗の作成"""
        progress = OnboardingProgress(user_id="user_123")

        assert progress.user_id == "user_123"
        assert progress.current_step == OnboardingStep.WELCOME
        assert len(progress.completed_steps) == 0
        assert progress.get_completion_rate() == 0.0

    def test_complete_step(self):
        """ステップ完了"""
        progress = OnboardingProgress(user_id="user_123")

        progress.complete_step(OnboardingStep.WELCOME)

        assert OnboardingStep.WELCOME.value in progress.completed_steps
        assert progress.current_step == OnboardingStep.CREATE_API_KEY

    def test_complete_checklist_item(self):
        """チェックリスト項目完了"""
        progress = OnboardingProgress(user_id="user_123")

        result = progress.complete_checklist_item("api_key_created")

        assert result is True
        assert progress.checklist["api_key_created"] is True

    def test_complete_invalid_checklist_item(self):
        """無効なチェックリスト項目"""
        progress = OnboardingProgress(user_id="user_123")

        result = progress.complete_checklist_item("invalid_item")

        assert result is False

    def test_completion_rate(self):
        """完了率計算"""
        progress = OnboardingProgress(user_id="user_123")

        # 2項目完了
        progress.complete_checklist_item("api_key_created")
        progress.complete_checklist_item("first_image_generated")

        rate = progress.get_completion_rate()
        assert rate == 2 / 8  # 8項目中2項目

    def test_is_completed(self):
        """完了チェック"""
        progress = OnboardingProgress(user_id="user_123")

        assert progress.is_completed() is False

        progress.current_step = OnboardingStep.COMPLETED
        assert progress.is_completed() is True

    def test_progress_to_dict(self):
        """辞書変換"""
        progress = OnboardingProgress(user_id="user_123")
        data = progress.to_dict()

        assert "user_id" in data
        assert "current_step" in data
        assert "checklist" in data
        assert "completion_rate" in data

    def test_progress_from_dict(self):
        """辞書からの復元"""
        original = OnboardingProgress(user_id="user_123")
        original.complete_step(OnboardingStep.WELCOME)
        data = original.to_dict()

        restored = OnboardingProgress.from_dict(data)

        assert restored.user_id == original.user_id
        assert restored.current_step == original.current_step


class TestFreeTrial:
    """FreeTrialモデルのテスト"""

    def test_create_trial(self):
        """トライアルの作成"""
        trial = FreeTrial(
            trial_id="trial_123",
            user_id="user_123",
        )

        assert trial.trial_id == "trial_123"
        assert trial.status == TrialStatus.ACTIVE
        assert trial.credits_granted == 20
        assert trial.credits_used == 0

    def test_trial_is_active(self):
        """アクティブチェック"""
        trial = FreeTrial(
            trial_id="trial_123",
            user_id="user_123",
        )

        assert trial.is_active() is True

    def test_trial_expired(self):
        """期限切れチェック"""
        trial = FreeTrial(
            trial_id="trial_123",
            user_id="user_123",
            expires_at="2020-01-01T00:00:00",
        )

        assert trial.is_active() is False

    def test_remaining_days(self):
        """残り日数"""
        trial = FreeTrial(
            trial_id="trial_123",
            user_id="user_123",
            expires_at=(datetime.now() + timedelta(days=5)).isoformat(),
        )

        remaining = trial.get_remaining_days()
        assert remaining >= 4  # 約5日

    def test_use_credits(self):
        """クレジット使用"""
        trial = FreeTrial(
            trial_id="trial_123",
            user_id="user_123",
            credits_granted=10,
        )

        assert trial.use_credits(3) is True
        assert trial.credits_used == 3
        assert trial.get_remaining_credits() == 7

    def test_use_credits_insufficient(self):
        """クレジット不足"""
        trial = FreeTrial(
            trial_id="trial_123",
            user_id="user_123",
            credits_granted=5,
            credits_used=5,
        )

        assert trial.use_credits(1) is False

    def test_convert(self):
        """有料転換"""
        trial = FreeTrial(
            trial_id="trial_123",
            user_id="user_123",
        )

        trial.convert("pro")

        assert trial.status == TrialStatus.CONVERTED
        assert trial.converted_plan == "pro"
        assert trial.converted_at is not None

    def test_expire(self):
        """期限切れ設定"""
        trial = FreeTrial(
            trial_id="trial_123",
            user_id="user_123",
        )

        trial.expire()

        assert trial.status == TrialStatus.EXPIRED

    def test_trial_to_dict(self):
        """辞書変換"""
        trial = FreeTrial(
            trial_id="trial_123",
            user_id="user_123",
        )
        data = trial.to_dict()

        assert "trial_id" in data
        assert "remaining_days" in data
        assert "remaining_credits" in data

    def test_trial_from_dict(self):
        """辞書からの復元"""
        original = FreeTrial(
            trial_id="trial_123",
            user_id="user_123",
        )
        data = original.to_dict()

        restored = FreeTrial.from_dict(data)

        assert restored.trial_id == original.trial_id
        assert restored.user_id == original.user_id


class TestOnboardingManager:
    """OnboardingManagerのテスト"""

    @pytest.fixture
    def temp_storage(self):
        """テスト用一時ディレクトリ"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def manager(self, temp_storage):
        """テスト用マネージャー"""
        return OnboardingManager(storage_path=temp_storage)

    # === オンボーディング進捗 ===

    def test_get_or_create_progress(self, manager):
        """進捗取得または作成"""
        progress = manager.get_or_create_progress("user_123", "vca_test")

        assert progress is not None
        assert progress.user_id == "user_123"

    def test_get_progress_existing(self, manager):
        """既存進捗の取得"""
        manager.get_or_create_progress("user_123")
        progress = manager.get_progress("user_123")

        assert progress is not None
        assert progress.user_id == "user_123"

    def test_complete_step(self, manager):
        """ステップ完了"""
        progress = manager.complete_step("user_123", OnboardingStep.WELCOME)

        assert OnboardingStep.WELCOME.value in progress.completed_steps

    def test_complete_checklist_item(self, manager):
        """チェックリスト項目完了"""
        success, progress = manager.complete_checklist_item("user_123", "api_key_created")

        assert success is True
        assert progress.checklist["api_key_created"] is True

    def test_get_next_step_hint(self, manager):
        """次のステップヒント"""
        hint = manager.get_next_step_hint("user_123")

        assert "step" in hint
        assert "title" in hint
        assert "description" in hint

    # === 無料トライアル ===

    def test_start_trial(self, manager):
        """トライアル開始"""
        success, message, trial = manager.start_trial("user_123", "vca_test")

        assert success is True
        assert trial is not None
        assert trial.is_active() is True

    def test_start_trial_already_active(self, manager):
        """アクティブなトライアルがある場合"""
        manager.start_trial("user_123")
        success, message, trial = manager.start_trial("user_123")

        assert success is False
        assert "既にアクティブ" in message

    def test_start_trial_extended(self, manager):
        """延長トライアル"""
        success, message, trial = manager.start_trial(
            "user_123",
            trial_type="extended",
        )

        assert success is True
        assert trial.duration_days == 14
        assert trial.credits_granted == 50

    def test_get_trial(self, manager):
        """トライアル取得"""
        manager.start_trial("user_123")
        trial = manager.get_trial("user_123")

        assert trial is not None
        assert trial.user_id == "user_123"

    def test_use_trial_credits(self, manager):
        """トライアルクレジット使用"""
        manager.start_trial("user_123")

        success, message = manager.use_trial_credits("user_123", 5)

        assert success is True
        trial = manager.get_trial("user_123")
        assert trial.credits_used == 5

    def test_use_trial_credits_insufficient(self, manager):
        """クレジット不足"""
        manager.start_trial("user_123")
        trial = manager.get_trial("user_123")
        trial.credits_used = trial.credits_granted  # 全て使用済み

        success, message = manager.use_trial_credits("user_123", 1)

        assert success is False
        assert "不足" in message

    def test_convert_trial(self, manager):
        """トライアル転換"""
        manager.start_trial("user_123")

        success, message = manager.convert_trial("user_123", "pro")

        assert success is True
        trial = manager.get_trial("user_123")
        assert trial.status == TrialStatus.CONVERTED

    def test_get_trial_stats(self, manager):
        """トライアル統計"""
        # 複数のトライアルを作成
        manager.start_trial("user_1")
        manager.start_trial("user_2")
        manager.convert_trial("user_2", "pro")

        stats = manager.get_trial_stats()

        assert stats["total_trials"] == 2
        assert stats["active_trials"] == 1
        assert stats["converted_trials"] == 1

    def test_get_expiring_trials(self, manager):
        """間もなく期限切れのトライアル"""
        success, _, trial = manager.start_trial("user_123")
        # 2日後に期限切れに設定
        trial.expires_at = (datetime.now() + timedelta(days=2)).isoformat()

        expiring = manager.get_expiring_trials(within_days=3)

        assert len(expiring) == 1

    def test_persistence(self, temp_storage):
        """永続化テスト"""
        # 作成
        manager1 = OnboardingManager(storage_path=temp_storage)
        manager1.get_or_create_progress("user_123")
        manager1.start_trial("user_456")

        # 再読み込み
        manager2 = OnboardingManager(storage_path=temp_storage)

        # 進捗が復元されているか
        progress = manager2.get_progress("user_123")
        assert progress is not None

        # トライアルが復元されているか
        trial = manager2.get_trial("user_456")
        assert trial is not None


class TestTrialConfigs:
    """トライアル設定のテスト"""

    def test_default_config(self):
        """デフォルト設定"""
        config = TRIAL_CONFIGS["default"]
        assert config["plan_id"] == "pro"
        assert config["duration_days"] == 7
        assert config["credits_granted"] == 20

    def test_extended_config(self):
        """延長設定"""
        config = TRIAL_CONFIGS["extended"]
        assert config["duration_days"] == 14
        assert config["credits_granted"] == 50

    def test_premium_config(self):
        """プレミアム設定"""
        config = TRIAL_CONFIGS["premium"]
        assert config["plan_id"] == "enterprise"
        assert config["duration_days"] == 30
        assert config["credits_granted"] == 100


class TestOnboardingHelp:
    """オンボーディングヘルプのテスト"""

    def test_all_steps_have_help(self):
        """全ステップにヘルプがある"""
        for step in OnboardingStep:
            assert step in ONBOARDING_HELP
            help_info = ONBOARDING_HELP[step]
            assert "title" in help_info
            assert "description" in help_info
            assert "action" in help_info


# === APIルートテスト ===
from fastapi.testclient import TestClient
from src.api.app import app


class TestOnboardingRoutes:
    """オンボーディングAPIルートのテスト"""

    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)

    @pytest.fixture
    def api_key(self, client):
        """テスト用APIキー取得"""
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Test Onboarding"}
        )
        return response.json()["api_key"]

    def test_welcome_endpoint(self, client, api_key):
        """ウェルカムエンドポイント"""
        response = client.get(
            "/api/v1/onboarding/welcome",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "has_trial" in data
        assert "tips" in data

    def test_welcome_without_auth(self, client):
        """認証なしでウェルカム取得"""
        response = client.get("/api/v1/onboarding/welcome")
        assert response.status_code == 401

    def test_get_progress(self, client, api_key):
        """進捗取得"""
        response = client.get(
            "/api/v1/onboarding/progress",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "current_step" in data
        assert "checklist" in data
        assert "completion_rate" in data

    def test_get_hint(self, client, api_key):
        """ヒント取得"""
        response = client.get(
            "/api/v1/onboarding/hint",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "step" in data
        assert "title" in data
        assert "description" in data

    def test_complete_step(self, client, api_key):
        """ステップ完了"""
        response = client.post(
            "/api/v1/onboarding/step/complete",
            headers={"X-API-Key": api_key},
            json={"step": "welcome"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "welcome" in data["completed_steps"]

    def test_complete_step_invalid(self, client, api_key):
        """無効なステップ完了"""
        response = client.post(
            "/api/v1/onboarding/step/complete",
            headers={"X-API-Key": api_key},
            json={"step": "invalid_step"}
        )
        assert response.status_code == 400

    def test_complete_checklist(self, client, api_key):
        """チェックリスト完了"""
        response = client.post(
            "/api/v1/onboarding/checklist/complete",
            headers={"X-API-Key": api_key},
            json={"item": "api_key_created"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["checklist"]["api_key_created"] is True

    def test_complete_checklist_invalid(self, client, api_key):
        """無効なチェックリスト項目完了"""
        response = client.post(
            "/api/v1/onboarding/checklist/complete",
            headers={"X-API-Key": api_key},
            json={"item": "invalid_item"}
        )
        assert response.status_code == 400

    def test_start_trial(self, client, api_key):
        """トライアル開始"""
        response = client.post(
            "/api/v1/onboarding/trial/start",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
        assert "trial_id" in data

    def test_start_trial_already_active(self, client, api_key):
        """アクティブなトライアルがある場合"""
        # 1回目
        client.post(
            "/api/v1/onboarding/trial/start",
            headers={"X-API-Key": api_key}
        )
        # 2回目
        response = client.post(
            "/api/v1/onboarding/trial/start",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 400

    def test_get_trial(self, client, api_key):
        """トライアル取得"""
        # まずトライアル開始
        client.post(
            "/api/v1/onboarding/trial/start",
            headers={"X-API-Key": api_key}
        )
        response = client.get(
            "/api/v1/onboarding/trial",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "trial_id" in data
        assert "remaining_credits" in data

    def test_get_trial_not_started(self, client):
        """トライアル未開始の場合"""
        # 新しいAPIキーを作成
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "No Trial User"}
        )
        new_key = response.json()["api_key"]

        response = client.get(
            "/api/v1/onboarding/trial",
            headers={"X-API-Key": new_key}
        )
        assert response.status_code == 404

    def test_use_trial_credits(self, client, api_key):
        """トライアルクレジット使用"""
        # トライアル開始
        client.post(
            "/api/v1/onboarding/trial/start",
            headers={"X-API-Key": api_key}
        )
        response = client.post(
            "/api/v1/onboarding/trial/use-credits",
            headers={"X-API-Key": api_key},
            json={"amount": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["remaining_credits"] >= 0

    def test_convert_trial(self, client, api_key):
        """トライアル転換"""
        # トライアル開始
        client.post(
            "/api/v1/onboarding/trial/start",
            headers={"X-API-Key": api_key}
        )
        response = client.post(
            "/api/v1/onboarding/trial/convert",
            headers={"X-API-Key": api_key},
            json={"plan_id": "pro"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["converted_to"] == "pro"

    def test_trial_stats(self, client, api_key):
        """トライアル統計"""
        response = client.get(
            "/api/v1/onboarding/trial/stats",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_trials" in data
        assert "conversion_rate" in data
