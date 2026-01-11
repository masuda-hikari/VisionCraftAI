# -*- coding: utf-8 -*-
"""
VisionCraftAI - リファラルシステムテスト
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.api.referral.models import (
    ReferralCode,
    Referral,
    ReferralStats,
    ReferralStatus,
    REFERRAL_REWARDS,
)
from src.api.referral.manager import ReferralManager


class TestReferralCode:
    """ReferralCodeモデルのテスト"""

    def test_generate_code(self):
        """紹介コードの生成"""
        code = ReferralCode.generate(
            owner_user_id="user_123",
            owner_api_key_id="vca_test",
        )

        assert code.code_id.startswith("ref_")
        assert len(code.code) == 8  # 8文字の大文字英数字
        assert code.owner_user_id == "user_123"
        assert code.owner_api_key_id == "vca_test"
        assert code.referrer_reward_credits == 5
        assert code.referee_reward_credits == 5
        assert code.is_active is True

    def test_code_is_valid(self):
        """コード有効性チェック"""
        code = ReferralCode.generate(
            owner_user_id="user_123",
        )

        is_valid, reason = code.is_valid()
        assert is_valid is True
        assert reason == "OK"

    def test_code_inactive(self):
        """無効化されたコード"""
        code = ReferralCode.generate(owner_user_id="user_123")
        code.is_active = False

        is_valid, reason = code.is_valid()
        assert is_valid is False
        assert "無効化" in reason

    def test_code_expired(self):
        """期限切れコード"""
        code = ReferralCode.generate(
            owner_user_id="user_123",
            expires_at="2020-01-01T00:00:00",
        )

        is_valid, reason = code.is_valid()
        assert is_valid is False
        assert "有効期限" in reason

    def test_code_max_uses(self):
        """使用回数上限"""
        code = ReferralCode.generate(
            owner_user_id="user_123",
            max_uses=1,
        )
        code.current_uses = 1

        is_valid, reason = code.is_valid()
        assert is_valid is False
        assert "使用回数上限" in reason

    def test_code_use(self):
        """コードの使用"""
        code = ReferralCode.generate(
            owner_user_id="user_123",
            max_uses=3,
        )

        assert code.use() is True
        assert code.current_uses == 1

        assert code.use() is True
        assert code.current_uses == 2

        assert code.use() is True
        assert code.current_uses == 3

        # 上限到達
        assert code.use() is False
        assert code.current_uses == 3

    def test_code_to_dict(self):
        """辞書変換"""
        code = ReferralCode.generate(owner_user_id="user_123")
        data = code.to_dict()

        assert "code_id" in data
        assert "code" in data
        assert data["owner_user_id"] == "user_123"

    def test_code_from_dict(self):
        """辞書からの復元"""
        original = ReferralCode.generate(owner_user_id="user_123")
        data = original.to_dict()
        restored = ReferralCode.from_dict(data)

        assert restored.code_id == original.code_id
        assert restored.code == original.code
        assert restored.owner_user_id == original.owner_user_id


class TestReferral:
    """Referralモデルのテスト"""

    def test_create_referral(self):
        """リファラルの作成"""
        referral = Referral(
            referral_id="rfr_test",
            referral_code_id="ref_test",
            referral_code="ABC12345",
            referrer_user_id="referrer_user",
            referee_user_id="referee_user",
            referrer_reward_credits=5,
            referee_reward_credits=5,
        )

        assert referral.status == ReferralStatus.PENDING
        assert referral.referrer_rewarded_at is None
        assert referral.referee_rewarded_at is None

    def test_mark_qualified(self):
        """条件達成マーク"""
        referral = Referral(
            referral_id="rfr_test",
            referral_code_id="ref_test",
            referral_code="ABC12345",
            referrer_user_id="referrer_user",
        )

        referral.mark_qualified()

        assert referral.status == ReferralStatus.QUALIFIED
        assert referral.qualified_at is not None

    def test_mark_rewarded(self):
        """報酬付与マーク"""
        referral = Referral(
            referral_id="rfr_test",
            referral_code_id="ref_test",
            referral_code="ABC12345",
            referrer_user_id="referrer_user",
        )
        referral.mark_qualified()

        # 紹介者に報酬付与
        referral.mark_rewarded(for_referrer=True)
        assert referral.referrer_rewarded_at is not None
        assert referral.status == ReferralStatus.QUALIFIED  # まだ完了ではない

        # 被紹介者に報酬付与
        referral.mark_rewarded(for_referrer=False)
        assert referral.referee_rewarded_at is not None
        assert referral.status == ReferralStatus.REWARDED  # 両方完了で完了

    def test_referral_to_dict(self):
        """辞書変換"""
        referral = Referral(
            referral_id="rfr_test",
            referral_code_id="ref_test",
            referral_code="ABC12345",
            referrer_user_id="referrer_user",
        )
        data = referral.to_dict()

        assert data["referral_id"] == "rfr_test"
        assert data["status"] == "pending"

    def test_referral_from_dict(self):
        """辞書からの復元"""
        original = Referral(
            referral_id="rfr_test",
            referral_code_id="ref_test",
            referral_code="ABC12345",
            referrer_user_id="referrer_user",
        )
        data = original.to_dict()
        restored = Referral.from_dict(data)

        assert restored.referral_id == original.referral_id
        assert restored.status == original.status


class TestReferralManager:
    """ReferralManagerのテスト"""

    @pytest.fixture
    def temp_storage(self):
        """テスト用一時ディレクトリ"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def manager(self, temp_storage):
        """テスト用マネージャー"""
        return ReferralManager(storage_path=temp_storage)

    def test_create_code(self, manager):
        """コード作成"""
        code = manager.create_code(
            owner_user_id="user_123",
            owner_api_key_id="vca_test",
        )

        assert code is not None
        assert code.owner_user_id == "user_123"

    def test_create_code_existing(self, manager):
        """既存コードの返却"""
        code1 = manager.create_code(owner_user_id="user_123")
        code2 = manager.create_code(owner_user_id="user_123")

        assert code1.code_id == code2.code_id
        assert code1.code == code2.code

    def test_get_code(self, manager):
        """コード取得"""
        created = manager.create_code(owner_user_id="user_123")
        retrieved = manager.get_code(created.code)

        assert retrieved is not None
        assert retrieved.code_id == created.code_id

    def test_get_code_case_insensitive(self, manager):
        """大文字小文字を区別しないコード取得"""
        created = manager.create_code(owner_user_id="user_123")
        retrieved = manager.get_code(created.code.lower())

        assert retrieved is not None

    def test_get_user_code(self, manager):
        """ユーザーのコード取得"""
        created = manager.create_code(owner_user_id="user_123")
        retrieved = manager.get_user_code("user_123")

        assert retrieved is not None
        assert retrieved.code_id == created.code_id

    def test_apply_code_success(self, manager):
        """コード適用成功"""
        code = manager.create_code(owner_user_id="referrer_user")

        success, message, referral = manager.apply_code(
            code=code.code,
            referee_user_id="referee_user",
            referee_api_key_id="vca_referee",
        )

        assert success is True
        assert referral is not None
        assert referral.status == ReferralStatus.QUALIFIED

    def test_apply_code_invalid(self, manager):
        """無効なコード適用"""
        success, message, referral = manager.apply_code(
            code="INVALID",
            referee_user_id="referee_user",
        )

        assert success is False
        assert "無効" in message
        assert referral is None

    def test_apply_code_self_referral(self, manager):
        """自己紹介の防止"""
        code = manager.create_code(owner_user_id="user_123")

        success, message, referral = manager.apply_code(
            code=code.code,
            referee_user_id="user_123",
        )

        assert success is False
        assert "自分自身" in message

    def test_apply_code_already_used(self, manager):
        """既に紹介済み"""
        code1 = manager.create_code(owner_user_id="referrer1")
        code2 = manager.create_code(owner_user_id="referrer2")

        # 1回目の適用
        success1, _, _ = manager.apply_code(
            code=code1.code,
            referee_user_id="referee_user",
        )
        assert success1 is True

        # 2回目の適用（別のコード）
        success2, message, _ = manager.apply_code(
            code=code2.code,
            referee_user_id="referee_user",
        )
        assert success2 is False
        assert "既に" in message

    def test_get_user_referrals(self, manager):
        """ユーザーのリファラル一覧"""
        code = manager.create_code(owner_user_id="referrer_user")

        manager.apply_code(code.code, "referee1")
        manager.apply_code(code.code, "referee2")

        referrals = manager.get_user_referrals("referrer_user", as_referrer=True)
        assert len(referrals) == 2

    def test_get_pending_rewards(self, manager):
        """報酬付与待ち取得"""
        code = manager.create_code(owner_user_id="referrer_user")
        _, _, referral = manager.apply_code(code.code, "referee_user")

        pending = manager.get_pending_rewards("referrer_user")
        assert len(pending) == 1

    def test_mark_reward_given(self, manager):
        """報酬付与マーク"""
        code = manager.create_code(owner_user_id="referrer_user")
        _, _, referral = manager.apply_code(code.code, "referee_user")

        result = manager.mark_reward_given(referral.referral_id, for_referrer=True)
        assert result is True

        # 確認
        updated = manager.get_referral(referral.referral_id)
        assert updated.referrer_rewarded_at is not None

    def test_get_stats(self, manager):
        """統計取得"""
        code = manager.create_code(owner_user_id="referrer_user")
        manager.apply_code(code.code, "referee1")
        manager.apply_code(code.code, "referee2")

        stats = manager.get_stats("referrer_user")
        assert stats.total_referrals == 2
        assert stats.pending_referrals == 2

    def test_get_leaderboard(self, manager):
        """ランキング取得"""
        # 複数の紹介者を作成
        code1 = manager.create_code(owner_user_id="top_referrer")
        code2 = manager.create_code(owner_user_id="second_referrer")

        # top_referrer: 3件
        for i in range(3):
            _, _, ref = manager.apply_code(code1.code, f"referee_{i}")
            manager.mark_reward_given(ref.referral_id, True)
            manager.mark_reward_given(ref.referral_id, False)

        # second_referrer: 1件
        _, _, ref = manager.apply_code(code2.code, "referee_single")
        manager.mark_reward_given(ref.referral_id, True)
        manager.mark_reward_given(ref.referral_id, False)

        leaderboard = manager.get_leaderboard(limit=10)
        assert len(leaderboard) == 2
        assert leaderboard[0]["user_id"] == "top_referrer"
        assert leaderboard[0]["successful_referrals"] == 3

    def test_persistence(self, temp_storage):
        """永続化テスト"""
        # 作成
        manager1 = ReferralManager(storage_path=temp_storage)
        code = manager1.create_code(owner_user_id="user_123")
        manager1.apply_code(code.code, "referee_user")

        # 再読み込み
        manager2 = ReferralManager(storage_path=temp_storage)

        # コードが復元されているか
        restored_code = manager2.get_code(code.code)
        assert restored_code is not None
        assert restored_code.code_id == code.code_id

        # リファラルが復元されているか
        referrals = manager2.get_user_referrals("user_123", as_referrer=True)
        assert len(referrals) == 1


class TestReferralRewards:
    """報酬設定のテスト"""

    def test_default_rewards(self):
        """デフォルト報酬設定"""
        rewards = REFERRAL_REWARDS["default"]
        assert rewards["referrer_credits"] == 5
        assert rewards["referee_credits"] == 5

    def test_premium_rewards(self):
        """プレミアム報酬設定"""
        rewards = REFERRAL_REWARDS["premium"]
        assert rewards["referrer_credits"] == 10
        assert rewards["referee_credits"] == 10


# === APIルートテスト ===
from fastapi.testclient import TestClient
from src.api.app import app


class TestReferralRoutes:
    """リファラルAPIルートのテスト"""

    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)

    @pytest.fixture
    def api_key(self, client):
        """テスト用APIキー取得"""
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Test Referral"}
        )
        return response.json()["api_key"]

    def test_create_referral_code(self, client, api_key):
        """紹介コード作成"""
        response = client.post(
            "/api/v1/referral/code",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert len(data["code"]) == 8

    def test_get_referral_code(self, client, api_key):
        """紹介コード取得"""
        # 作成
        client.post(
            "/api/v1/referral/code",
            headers={"X-API-Key": api_key}
        )
        # 取得
        response = client.get(
            "/api/v1/referral/code",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "code" in data

    def test_validate_code(self, client, api_key):
        """コード検証"""
        # コード作成
        create_response = client.post(
            "/api/v1/referral/code",
            headers={"X-API-Key": api_key}
        )
        code = create_response.json()["code"]

        # 検証
        response = client.get(
            f"/api/v1/referral/validate?code={code}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_validate_invalid_code(self, client):
        """無効なコード検証"""
        response = client.get(
            "/api/v1/referral/validate?code=INVALID1"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_apply_code(self, client, api_key):
        """コード適用"""
        # 紹介者のコード作成
        create_response = client.post(
            "/api/v1/referral/code",
            headers={"X-API-Key": api_key}
        )
        code = create_response.json()["code"]

        # 別のユーザーを作成
        new_key_response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Referee User"}
        )
        referee_key = new_key_response.json()["api_key"]

        # コード適用
        response = client.post(
            "/api/v1/referral/apply",
            headers={"X-API-Key": referee_key},
            json={"code": code}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_apply_invalid_code(self, client, api_key):
        """無効なコード適用"""
        response = client.post(
            "/api/v1/referral/apply",
            headers={"X-API-Key": api_key},
            json={"code": "INVALID1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_get_referrals(self, client, api_key):
        """リファラル一覧取得"""
        response = client.get(
            "/api/v1/referral/referrals",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_stats(self, client, api_key):
        """統計取得"""
        response = client.get(
            "/api/v1/referral/stats",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_referrals" in data

    def test_get_leaderboard(self, client):
        """ランキング取得"""
        response = client.get(
            "/api/v1/referral/leaderboard"
        )
        assert response.status_code == 200
        data = response.json()
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)

    def test_get_pending_rewards(self, client, api_key):
        """報酬待ち取得"""
        response = client.get(
            "/api/v1/referral/pending-rewards",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert "referrals" in data
        assert isinstance(data["referrals"], list)
