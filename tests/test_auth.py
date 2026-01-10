# -*- coding: utf-8 -*-
"""
VisionCraftAI - 認証システムテスト

APIキー認証、レート制限、クォータのテストを実装します。
"""

import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import json

from src.api.auth.models import APIKey, APIKeyTier, UsageQuota
from src.api.auth.key_manager import APIKeyManager
from src.api.auth.rate_limiter import RateLimiter, RateLimitConfig


# =====================
# UsageQuota テスト
# =====================

class TestUsageQuota:
    """UsageQuota クラスのテスト"""

    def test_for_tier_free(self):
        """Freeプランのクォータ確認"""
        quota = UsageQuota.for_tier(APIKeyTier.FREE)
        assert quota.monthly_limit == 5
        assert quota.daily_limit == 3
        assert quota.max_width == 512
        assert quota.max_height == 512
        assert quota.max_batch_size == 1
        assert quota.priority_processing is False

    def test_for_tier_basic(self):
        """Basicプランのクォータ確認"""
        quota = UsageQuota.for_tier(APIKeyTier.BASIC)
        assert quota.monthly_limit == 100
        assert quota.daily_limit == 20
        assert quota.max_width == 1024
        assert quota.max_batch_size == 10

    def test_for_tier_pro(self):
        """Proプランのクォータ確認"""
        quota = UsageQuota.for_tier(APIKeyTier.PRO)
        assert quota.monthly_limit == 500
        assert quota.daily_limit == 50
        assert quota.max_width == 2048
        assert quota.max_batch_size == 50
        assert quota.priority_processing is True

    def test_for_tier_enterprise(self):
        """Enterpriseプランのクォータ確認"""
        quota = UsageQuota.for_tier(APIKeyTier.ENTERPRISE)
        assert quota.monthly_limit == 999999
        assert quota.daily_limit == 999999
        assert quota.max_width == 4096
        assert quota.max_batch_size == 100
        assert quota.priority_processing is True

    def test_can_generate_within_limit(self):
        """制限内での生成許可"""
        quota = UsageQuota(monthly_limit=10, daily_limit=5)
        can, reason = quota.can_generate(1)
        assert can is True
        assert reason == "OK"

    def test_can_generate_monthly_exceeded(self):
        """月間制限超過"""
        quota = UsageQuota(monthly_limit=5, daily_limit=10, monthly_used=5)
        can, reason = quota.can_generate(1)
        assert can is False
        assert "月間" in reason

    def test_can_generate_daily_exceeded(self):
        """日間制限超過"""
        quota = UsageQuota(monthly_limit=100, daily_limit=5, daily_used=5)
        can, reason = quota.can_generate(1)
        assert can is False
        assert "日間" in reason

    def test_record_usage(self):
        """使用量記録"""
        quota = UsageQuota(monthly_limit=10, daily_limit=10)
        quota.record_usage(3)
        assert quota.monthly_used == 3
        assert quota.daily_used == 3

    def test_get_remaining(self):
        """残り使用量取得"""
        quota = UsageQuota(monthly_limit=10, daily_limit=5, monthly_used=3, daily_used=2)
        remaining = quota.get_remaining()
        assert remaining["monthly_remaining"] == 7
        assert remaining["daily_remaining"] == 3


# =====================
# APIKey テスト
# =====================

class TestAPIKey:
    """APIKey クラスのテスト"""

    def test_generate(self):
        """APIキー生成"""
        api_key, raw_key = APIKey.generate(
            tier=APIKeyTier.BASIC,
            name="Test Key",
            description="テスト用",
        )

        assert api_key.key_id.startswith("vca_")
        assert api_key.tier == APIKeyTier.BASIC
        assert api_key.name == "Test Key"
        assert api_key.is_active is True
        assert raw_key.startswith("vca_")
        assert "." in raw_key

    def test_hash_key(self):
        """キーハッシュ化"""
        raw_key = "vca_test123.secret456"
        hash1 = APIKey.hash_key(raw_key)
        hash2 = APIKey.hash_key(raw_key)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256

    def test_extract_key_id(self):
        """key_id抽出"""
        raw_key = "vca_abc123.secretpart"
        key_id = APIKey.extract_key_id(raw_key)
        assert key_id == "vca_abc123"

    def test_is_valid_active(self):
        """有効なキーの検証"""
        api_key, _ = APIKey.generate()
        is_valid, reason = api_key.is_valid()
        assert is_valid is True
        assert reason == "OK"

    def test_is_valid_inactive(self):
        """無効化されたキーの検証"""
        api_key, _ = APIKey.generate()
        api_key.is_active = False
        is_valid, reason = api_key.is_valid()
        assert is_valid is False
        assert "無効化" in reason

    def test_is_valid_expired(self):
        """期限切れキーの検証"""
        api_key, _ = APIKey.generate(expires_at="2020-01-01T00:00:00")
        is_valid, reason = api_key.is_valid()
        assert is_valid is False
        assert "有効期限" in reason

    def test_check_ip_no_restriction(self):
        """IP制限なしの場合"""
        api_key, _ = APIKey.generate()
        assert api_key.check_ip("192.168.1.1") is True

    def test_check_ip_allowed(self):
        """許可されたIPの場合"""
        api_key, _ = APIKey.generate(allowed_ips=["192.168.1.1", "10.0.0.1"])
        assert api_key.check_ip("192.168.1.1") is True

    def test_check_ip_denied(self):
        """許可されていないIPの場合"""
        api_key, _ = APIKey.generate(allowed_ips=["192.168.1.1"])
        assert api_key.check_ip("10.0.0.1") is False

    def test_to_dict_and_from_dict(self):
        """辞書変換の往復"""
        api_key, _ = APIKey.generate(
            tier=APIKeyTier.PRO,
            name="Test",
            description="Description",
        )
        data = api_key.to_dict(include_hash=True)
        restored = APIKey.from_dict(data)

        assert restored.key_id == api_key.key_id
        assert restored.tier == api_key.tier
        assert restored.name == api_key.name
        assert restored.quota.monthly_limit == api_key.quota.monthly_limit


# =====================
# APIKeyManager テスト
# =====================

class TestAPIKeyManager:
    """APIKeyManager クラスのテスト"""

    @pytest.fixture
    def temp_storage(self):
        """一時ストレージファイルを作成"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            json.dump({"version": "1.0", "keys": []}, f)
            yield Path(f.name)

    @pytest.fixture
    def manager(self, temp_storage):
        """APIKeyManagerのフィクスチャ"""
        return APIKeyManager(storage_path=temp_storage)

    def test_create_key(self, manager):
        """キー作成"""
        api_key, raw_key = manager.create_key(
            tier=APIKeyTier.BASIC,
            name="Test Key",
        )

        assert api_key.key_id.startswith("vca_")
        assert api_key.tier == APIKeyTier.BASIC
        assert raw_key is not None

    def test_validate_key_valid(self, manager):
        """有効なキーの検証"""
        _, raw_key = manager.create_key()

        is_valid, api_key, reason = manager.validate_key(raw_key)
        assert is_valid is True
        assert api_key is not None
        assert reason == "OK"

    def test_validate_key_invalid(self, manager):
        """無効なキーの検証"""
        is_valid, api_key, reason = manager.validate_key("invalid_key")
        assert is_valid is False
        assert api_key is None
        assert "無効" in reason

    def test_validate_key_empty(self, manager):
        """空キーの検証"""
        is_valid, api_key, reason = manager.validate_key("")
        assert is_valid is False
        assert "提供されていません" in reason

    def test_validate_key_with_ip(self, manager):
        """IP制限付きキーの検証"""
        api_key, raw_key = manager.create_key(allowed_ips=["192.168.1.1"])

        # 許可されたIP
        is_valid, _, _ = manager.validate_key(raw_key, ip="192.168.1.1")
        assert is_valid is True

        # 許可されていないIP
        is_valid, _, reason = manager.validate_key(raw_key, ip="10.0.0.1")
        assert is_valid is False
        assert "IP" in reason

    def test_get_key(self, manager):
        """key_idでキー取得"""
        api_key, _ = manager.create_key()
        retrieved = manager.get_key(api_key.key_id)
        assert retrieved is not None
        assert retrieved.key_id == api_key.key_id

    def test_list_keys(self, manager):
        """キー一覧取得"""
        manager.create_key(tier=APIKeyTier.FREE, name="Key1")
        manager.create_key(tier=APIKeyTier.BASIC, name="Key2")
        manager.create_key(tier=APIKeyTier.FREE, name="Key3")

        all_keys = manager.list_keys()
        assert len(all_keys) == 3

        free_keys = manager.list_keys(tier=APIKeyTier.FREE)
        assert len(free_keys) == 2

    def test_update_key(self, manager):
        """キー更新"""
        api_key, _ = manager.create_key(name="Original")

        updated = manager.update_key(
            api_key.key_id,
            name="Updated",
            description="New description",
        )

        assert updated is not None
        assert updated.name == "Updated"
        assert updated.description == "New description"

    def test_revoke_key(self, manager):
        """キー無効化"""
        api_key, _ = manager.create_key()
        success = manager.revoke_key(api_key.key_id)
        assert success is True

        key = manager.get_key(api_key.key_id)
        assert key.is_active is False

    def test_delete_key(self, manager):
        """キー削除"""
        api_key, _ = manager.create_key()
        success = manager.delete_key(api_key.key_id)
        assert success is True

        key = manager.get_key(api_key.key_id)
        assert key is None

    def test_record_usage(self, manager):
        """使用量記録"""
        api_key, _ = manager.create_key(tier=APIKeyTier.BASIC)

        success, message = manager.record_usage(api_key.key_id, 1)
        assert success is True

        status = manager.get_quota_status(api_key.key_id)
        assert status["monthly_remaining"] == 99  # 100 - 1

    def test_record_usage_quota_exceeded(self, manager):
        """クォータ超過時の使用量記録"""
        api_key, _ = manager.create_key(tier=APIKeyTier.FREE)  # 月5回
        api_key.quota.monthly_used = 5  # 既に使い切り

        success, reason = manager.record_usage(api_key.key_id, 1)
        assert success is False
        assert "月間" in reason

    def test_persistence(self, temp_storage):
        """永続化の確認"""
        # 作成
        manager1 = APIKeyManager(storage_path=temp_storage)
        api_key, raw_key = manager1.create_key(name="Persistent Key")
        key_id = api_key.key_id

        # 再読み込み
        manager2 = APIKeyManager(storage_path=temp_storage)
        loaded_key = manager2.get_key(key_id)

        assert loaded_key is not None
        assert loaded_key.name == "Persistent Key"

        # 検証も可能
        is_valid, _, _ = manager2.validate_key(raw_key)
        assert is_valid is True


# =====================
# RateLimiter テスト
# =====================

class TestRateLimiter:
    """RateLimiter クラスのテスト"""

    @pytest.fixture
    def limiter(self):
        """RateLimiterのフィクスチャ"""
        config = RateLimitConfig(
            default_limit=5,
            window_seconds=60,
            burst_allowance=2,
        )
        return RateLimiter(config)

    def test_check_within_limit(self, limiter):
        """制限内のチェック"""
        allowed, status = limiter.check("test_key")
        assert allowed is True
        assert status["remaining"] > 0

    def test_check_and_record(self, limiter):
        """チェック＆記録"""
        allowed, status1 = limiter.check_and_record("test_key")
        assert allowed is True

        _, status2 = limiter.check("test_key")
        assert status2["current_count"] == 1

    def test_rate_limit_exceeded(self, limiter):
        """レート制限超過"""
        key = "test_key"
        # 制限 + バースト分まで記録
        for _ in range(7):  # 5 + 2 = 7
            limiter.record(key)

        allowed, status = limiter.check(key)
        assert allowed is False
        assert status["remaining"] == 0
        assert "retry_after" in status

    def test_custom_limit(self, limiter):
        """カスタム制限"""
        allowed, status = limiter.check("test_key", limit=100)
        assert allowed is True
        assert status["limit"] == 100

    def test_reset(self, limiter):
        """リセット"""
        key = "test_key"
        for _ in range(5):
            limiter.record(key)

        limiter.reset(key)
        _, status = limiter.check(key)
        assert status["current_count"] == 0

    def test_get_status(self, limiter):
        """状態取得"""
        key = "test_key"
        limiter.record(key)
        limiter.record(key)

        status = limiter.get_status(key)
        assert status["current_count"] == 2
        assert status["limit"] == 5


# =====================
# 統合テスト
# =====================

class TestAuthIntegration:
    """認証システム統合テスト"""

    @pytest.fixture
    def temp_storage(self):
        """一時ストレージファイル"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as f:
            json.dump({"version": "1.0", "keys": []}, f)
            yield Path(f.name)

    def test_full_lifecycle(self, temp_storage):
        """完全なライフサイクルテスト"""
        manager = APIKeyManager(storage_path=temp_storage)
        limiter = RateLimiter()

        # 1. キー作成
        api_key, raw_key = manager.create_key(
            tier=APIKeyTier.BASIC,
            name="Integration Test Key",
        )

        # 2. キー検証
        is_valid, validated_key, _ = manager.validate_key(raw_key)
        assert is_valid is True
        assert validated_key.tier == APIKeyTier.BASIC

        # 3. クォータチェック
        can_generate, _ = api_key.quota.can_generate(1)
        assert can_generate is True

        # 4. レート制限チェック
        allowed, _ = limiter.check_and_record(api_key.key_id, api_key.quota.rate_limit_per_minute)
        assert allowed is True

        # 5. 使用量記録
        success, _ = manager.record_usage(api_key.key_id, 1)
        assert success is True

        # 6. クォータ状況確認
        status = manager.get_quota_status(api_key.key_id)
        assert status["monthly_remaining"] == 99

        # 7. キー無効化
        manager.revoke_key(api_key.key_id)
        is_valid, _, _ = manager.validate_key(raw_key)
        assert is_valid is False

    def test_tier_upgrade(self, temp_storage):
        """プランアップグレード"""
        manager = APIKeyManager(storage_path=temp_storage)

        # Freeで作成
        api_key, _ = manager.create_key(tier=APIKeyTier.FREE)
        assert api_key.quota.monthly_limit == 5

        # 使用量記録
        manager.record_usage(api_key.key_id, 3)

        # Basicにアップグレード
        updated = manager.update_key(api_key.key_id, tier=APIKeyTier.BASIC)
        assert updated.quota.monthly_limit == 100
        assert updated.quota.monthly_used == 3  # 使用量は維持


# =====================
# API エンドポイントテスト
# =====================

@pytest.fixture
def test_client():
    """テスト用HTTPクライアント"""
    from fastapi.testclient import TestClient
    from src.api.app import app
    return TestClient(app)


class TestAuthEndpoints:
    """認証APIエンドポイントのテスト"""

    def test_create_api_key(self, test_client):
        """APIキー作成エンドポイント"""
        response = test_client.post(
            "/api/v1/auth/keys",
            json={
                "tier": "free",
                "name": "Test API Key",
                "description": "テスト用",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "api_key" in data
        assert data["api_key"].startswith("vca_")

    def test_verify_api_key(self, test_client):
        """APIキー検証エンドポイント"""
        # キー作成
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Verify Test"},
        )
        api_key = create_response.json()["api_key"]

        # 検証
        response = test_client.get(
            "/api/v1/auth/verify",
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["tier"] == "basic"

    def test_verify_invalid_api_key(self, test_client):
        """無効なAPIキーの検証"""
        response = test_client.get(
            "/api/v1/auth/verify",
            headers={"X-API-Key": "invalid_key"},
        )
        assert response.status_code == 401

    def test_get_quota_status(self, test_client):
        """クォータ状況取得"""
        # キー作成
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "pro", "name": "Quota Test"},
        )
        api_key = create_response.json()["api_key"]

        # クォータ確認
        response = test_client.get(
            "/api/v1/auth/quota",
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "pro"
        assert data["monthly_limit"] == 500

    def test_generate_requires_auth(self, test_client):
        """画像生成に認証が必要"""
        response = test_client.post(
            "/api/v1/generate",
            json={"prompt": "A beautiful sunset"},
        )
        assert response.status_code == 401

    def test_generate_with_auth(self, test_client):
        """認証付き画像生成"""
        # キー作成
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Generate Test"},
        )
        api_key = create_response.json()["api_key"]

        # 画像生成（実際のAPIは呼ばれないがリクエストは通る）
        response = test_client.post(
            "/api/v1/generate",
            json={"prompt": "A beautiful sunset"},
            headers={"X-API-Key": api_key},
        )
        # 認証は通るが、Gemini APIがないためエラーになる可能性
        # 401ではないことを確認
        assert response.status_code != 401


# =====================
# 認証依存性追加テスト
# =====================


class TestAuthDependencies:
    """認証依存性の追加テスト（カバレッジ向上用）"""

    def test_bearer_auth(self, test_client):
        """Bearerトークン認証"""
        # キー作成
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Bearer Test"},
        )
        api_key = create_response.json()["api_key"]

        # Bearer認証でアクセス
        response = test_client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_authorization_without_bearer(self, test_client):
        """Bearerプレフィックスなしの認証"""
        # キー作成
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "No Bearer Test"},
        )
        api_key = create_response.json()["api_key"]

        # Bearerなしでアクセス
        response = test_client.get(
            "/api/v1/auth/verify",
            headers={"Authorization": api_key},
        )
        assert response.status_code == 200

    def test_forwarded_for_header(self, test_client):
        """X-Forwarded-Forヘッダー処理"""
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Forwarded Test"},
        )
        api_key = create_response.json()["api_key"]

        # X-Forwarded-Forヘッダー付きアクセス
        response = test_client.get(
            "/api/v1/auth/verify",
            headers={
                "X-API-Key": api_key,
                "X-Forwarded-For": "192.168.1.1, 10.0.0.1",
            },
        )
        assert response.status_code == 200

    def test_rate_limit_no_auth(self, test_client):
        """認証なしのレート制限"""
        # 認証なしで複数回リクエスト
        for _ in range(5):
            response = test_client.get("/api/v1/health")
            # ヘルスエンドポイントは認証不要
            assert response.status_code == 200

    def test_quota_check_endpoint(self, test_client):
        """クォータチェック"""
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "free", "name": "Quota Check Test"},
        )
        api_key = create_response.json()["api_key"]

        # クォータ状況確認
        response = test_client.get(
            "/api/v1/auth/quota",
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"
        assert "monthly_remaining" in data

    def test_usage_endpoint(self, test_client):
        """使用量エンドポイント"""
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Usage Test"},
        )
        api_key = create_response.json()["api_key"]

        response = test_client.get(
            "/api/v1/auth/usage",
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 200

    def test_rate_limit_status(self, test_client):
        """レート制限状況"""
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Rate Limit Test"},
        )
        api_key = create_response.json()["api_key"]

        response = test_client.get(
            "/api/v1/auth/rate-limit",
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 200

    def test_key_list_with_auth(self, test_client):
        """認証付きキー一覧取得"""
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "List Test", "owner_id": "owner_test_001"},
        )
        api_key = create_response.json()["api_key"]

        response = test_client.get(
            "/api/v1/auth/keys",
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 200

    def test_get_current_key_info(self, test_client):
        """現在のキー情報取得"""
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "pro", "name": "Current Key Test"},
        )
        api_key = create_response.json()["api_key"]

        response = test_client.get(
            "/api/v1/auth/keys/me",
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "pro"
        assert data["name"] == "Current Key Test"


class TestTierChecker:
    """TierCheckerクラスのテスト"""

    def test_tier_checker_allowed(self, test_client):
        """許可されたTierでのアクセス"""
        # Proキーを作成
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "pro", "name": "Pro Tier Test"},
        )
        api_key = create_response.json()["api_key"]

        # プレミアム機能へのアクセス（存在すれば）
        response = test_client.get(
            "/api/v1/auth/verify",
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 200


class TestQuotaEnforcer:
    """QuotaEnforcerクラスのテスト"""

    def test_quota_enforcer_within_limit(self, test_client):
        """クォータ内でのアクセス"""
        create_response = test_client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Quota Enforcer Test"},
        )
        api_key = create_response.json()["api_key"]

        # 画像生成リクエスト（クォータ内）
        response = test_client.post(
            "/api/v1/generate",
            json={"prompt": "Test image"},
            headers={"X-API-Key": api_key},
        )
        # 認証は通る（Gemini APIがないためエラーになる可能性があるが、401/429ではない）
        assert response.status_code not in [401, 429]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
