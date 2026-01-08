# -*- coding: utf-8 -*-
"""
VisionCraftAI - E2Eテスト

エンドツーエンドの統合テストスイート。
完全なユーザーフローをシミュレートしてテストする。
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json

from fastapi.testclient import TestClient

from src.api.app import app
from src.generator.gemini_client import GenerationResult
from src.generator.batch_processor import BatchResult


client = TestClient(app)


class TestE2EUserJourney:
    """完全なユーザージャーニーのE2Eテスト"""

    def test_new_user_journey_free_tier(self):
        """
        新規ユーザーの無料プラン体験フロー:
        1. ランディングページ閲覧
        2. APIキー作成（Free）
        3. プロンプト検証
        4. プロンプト拡張
        5. 画像生成（モック）
        6. クォータ確認
        """
        # 1. ランディングページ閲覧
        response = client.get("/", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "VisionCraftAI" in response.text
        assert "無料で試す" in response.text

        # 2. APIキー作成（Freeプラン）
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "free", "name": "New User Key"},
        )
        assert response.status_code == 201  # 作成成功は201 Created
        data = response.json()
        api_key = data["api_key"]
        assert api_key.startswith("vca_")
        assert data["tier"] == "free"
        headers = {"X-API-Key": api_key}

        # 3. プロンプト検証
        response = client.post(
            "/api/v1/prompt/validate",
            params={"prompt": "A beautiful sunset over mountains"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

        # 4. プロンプト拡張
        response = client.post(
            "/api/v1/prompt/enhance",
            params={
                "prompt": "A beautiful sunset",
                "quality_boost": True,
                "style": "photorealistic"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "high quality" in data["enhanced_prompt"].lower()
        assert "photorealistic" in data["enhanced_prompt"].lower()
        enhanced_prompt = data["enhanced_prompt"]

        # 5. 画像生成（モック）
        with patch("src.api.routes.get_client") as mock_client, \
             patch("src.api.routes.get_usage_tracker") as mock_tracker:
            mock_result = GenerationResult(
                success=True,
                image_data=b"fake_image_data",
                file_path="outputs/test.png",
                prompt=enhanced_prompt,
                generation_time_ms=1500,
                model_used="gemini-2.0-flash-exp",
            )
            mock_client.return_value.generate_image.return_value = mock_result
            mock_tracker.return_value.record.return_value = Mock()

            response = client.post(
                "/api/v1/generate",
                json={
                    "prompt": enhanced_prompt,
                    "width": 512,
                    "height": 512,
                    "quality_boost": True
                },
                headers=headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["image_base64"] is not None

        # 6. クォータ確認
        response = client.get("/api/v1/auth/quota", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"
        # 実際のレスポンス形式に合わせる
        assert "monthly_remaining" in data
        assert "daily_remaining" in data

    def test_pro_user_batch_workflow(self):
        """
        Proユーザーのバッチ処理ワークフロー:
        1. APIキー作成（Pro）
        2. バッチ見積もり
        3. バッチ画像生成
        4. 使用量確認
        """
        # 1. APIキー作成（Proプラン）
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "pro", "name": "Pro User Key"},
        )
        assert response.status_code == 201  # 作成成功は201 Created
        api_key = response.json()["api_key"]
        headers = {"X-API-Key": api_key}

        # 2. バッチ見積もり
        response = client.post(
            "/api/v1/batch/estimate",
            json={"prompt_count": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["prompt_count"] == 10
        assert data["total_estimated_seconds"] > 0

        # 3. バッチ画像生成
        prompts = [
            {"prompt": f"Beautiful landscape {i}", "style": "photorealistic"}
            for i in range(5)
        ]

        with patch("src.api.routes.get_batch_processor") as mock_processor, \
             patch("src.api.routes.get_usage_tracker") as mock_tracker:
            mock_result = BatchResult(
                job_id="batch_test_123",
                total_count=5,
                success_count=5,
                failure_count=0,
                results=[
                    GenerationResult(
                        success=True,
                        file_path=f"outputs/batch_{i}.png",
                        prompt=f"Beautiful landscape {i}",
                        generation_time_ms=1000,
                        model_used="gemini-2.0-flash-exp",
                    )
                    for i in range(5)
                ],
                total_time_ms=5000,
                average_time_ms=1000.0,
            )
            mock_processor.return_value.process_batch.return_value = mock_result
            mock_tracker.return_value.record.return_value = Mock()

            response = client.post(
                "/api/v1/batch/generate",
                json={"prompts": prompts},
                headers=headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 5
            assert data["success_count"] == 5
            assert data["failure_count"] == 0

        # 4. 使用量確認
        with patch("src.api.routes.get_usage_tracker") as mock_tracker:
            from src.utils.usage_tracker import UsageSummary
            mock_summary = UsageSummary(
                period_start="2026-01-01T00:00:00",
                period_end="2026-01-08T00:00:00",
                total_requests=5,
                successful_requests=5,
                failed_requests=0,
                total_generation_time_ms=5000,
                average_generation_time_ms=1000.0,
                total_estimated_cost_usd=0.05,
            )
            mock_tracker.return_value.get_summary.return_value = mock_summary

            response = client.get("/api/v1/usage")
            assert response.status_code == 200


class TestE2EAPIKeyLifecycle:
    """APIキーのライフサイクルE2Eテスト"""

    def test_api_key_full_lifecycle(self):
        """
        APIキーの完全なライフサイクル:
        1. 作成
        2. 情報取得
        3. 更新
        4. 削除
        """
        # 1. 作成
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Lifecycle Test Key"},
        )
        assert response.status_code == 201  # 作成成功は201 Created
        data = response.json()
        api_key = data["api_key"]
        key_id = data["key_id"]
        headers = {"X-API-Key": api_key}

        # 2. 情報取得
        response = client.get("/api/v1/auth/keys/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Lifecycle Test Key"
        assert data["tier"] == "basic"

        # 3. 更新
        response = client.patch(
            f"/api/v1/auth/keys/{key_id}",
            json={"name": "Updated Key Name"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        # 更新成功のレスポンスを確認（success/message形式またはキー情報）
        assert data.get("success") is True or "key_id" in data

        # 4. 削除
        response = client.delete(
            f"/api/v1/auth/keys/{key_id}",
            headers=headers,
        )
        assert response.status_code in [200, 204]  # 削除成功は200または204

        # 削除後のアクセス確認（失敗すべき）
        response = client.get("/api/v1/auth/keys/me", headers=headers)
        assert response.status_code == 401


class TestE2EPaymentFlow:
    """決済フローのE2Eテスト"""

    def test_view_plans_and_packages(self):
        """
        プラン・パッケージ閲覧フロー:
        1. プラン一覧表示
        2. クレジットパッケージ一覧表示
        """
        # 1. プラン一覧表示
        response = client.get("/api/v1/payment/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        plans = data["plans"]
        assert len(plans) == 4  # Free, Basic, Pro, Enterprise

        # プラン内容の検証
        plan_names = [p["name"] for p in plans]
        assert "Free" in plan_names
        assert "Basic" in plan_names
        assert "Pro" in plan_names
        assert "Enterprise" in plan_names

        # 2. クレジットパッケージ一覧表示
        response = client.get("/api/v1/payment/credits/packages")
        assert response.status_code == 200
        data = response.json()
        assert "packages" in data
        packages = data["packages"]
        assert len(packages) >= 1

    def test_subscription_checkout_flow(self):
        """
        サブスクリプションチェックアウトフロー（モック）:
        1. APIキー作成
        2. サブスクリプション作成
        """
        # 1. APIキー作成
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "free", "name": "Payment Test Key"},
        )
        assert response.status_code == 201
        api_key = response.json()["api_key"]
        headers = {"X-API-Key": api_key}

        # 2. サブスクリプション作成（Stripeへのリダイレクト前）
        with patch("src.api.payment.routes.get_stripe_client") as mock_stripe:
            mock_stripe.return_value.create_checkout_session.return_value = {
                "checkout_url": "https://checkout.stripe.com/test"
            }
            response = client.post(
                "/api/v1/payment/subscriptions",
                json={
                    "email": "test@example.com",
                    "plan_id": "basic",
                    "billing_interval": "monthly"
                },
                headers=headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert "checkout_url" in data


class TestE2ERateLimiting:
    """レート制限のE2Eテスト"""

    def test_free_tier_rate_limits(self):
        """
        Freeプランのレート制限確認:
        1. APIキー作成（Free）
        2. レート制限状況確認
        """
        # 1. APIキー作成
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "free", "name": "Rate Limit Test"},
        )
        assert response.status_code == 201
        api_key = response.json()["api_key"]
        headers = {"X-API-Key": api_key}

        # 2. レート制限状況確認
        response = client.get("/api/v1/auth/rate-limit", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # 実際のレスポンス形式に合わせる
        assert "remaining" in data
        assert "window_seconds" in data
        assert "limit" in data


class TestE2EErrorRecovery:
    """エラーリカバリーのE2Eテスト"""

    def test_invalid_prompt_recovery(self):
        """
        無効プロンプト時のリカバリーフロー:
        1. 無効プロンプトで検証
        2. プロンプト修正
        3. 再検証
        """
        # 1. 無効プロンプトで検証
        response = client.post(
            "/api/v1/prompt/validate",
            params={"prompt": "Violence scene"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["blocked_reason"] is not None

        # 2. プロンプト修正後の検証
        response = client.post(
            "/api/v1/prompt/validate",
            params={"prompt": "A peaceful garden scene"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    def test_api_connection_failure_recovery(self):
        """
        API接続失敗時のリカバリー:
        1. ヘルスチェック（API接続なし）
        2. ヘルスチェック（基本のみ）
        """
        # API接続確認なしのヘルスチェック
        response = client.get("/api/v1/health?check_api=false")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestE2EDocumentation:
    """ドキュメントエンドポイントのE2Eテスト"""

    def test_swagger_ui_accessible(self):
        """Swagger UIがアクセス可能"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_accessible(self):
        """ReDocがアクセス可能"""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json_accessible(self):
        """OpenAPI JSONがアクセス可能"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestE2ESecurityHeaders:
    """セキュリティヘッダーのE2Eテスト"""

    def test_cors_headers_on_api_request(self):
        """CORS設定の確認"""
        # プリフライトリクエスト
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        # CORSが適切に設定されている場合、200または204を返す
        assert response.status_code in [200, 204, 405]

    def test_invalid_api_key_returns_401(self):
        """無効なAPIキーで401を返す"""
        response = client.post(
            "/api/v1/generate",
            json={"prompt": "test"},
            headers={"X-API-Key": "invalid_key"}
        )
        assert response.status_code == 401


class TestE2EStaticAssets:
    """静的アセットのE2Eテスト"""

    def test_css_accessible(self):
        """CSSファイルがアクセス可能"""
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers.get("content-type", "")

    def test_js_accessible(self):
        """JavaScriptファイルがアクセス可能"""
        response = client.get("/static/js/app.js")
        assert response.status_code == 200
        assert "javascript" in response.headers.get("content-type", "").lower()
