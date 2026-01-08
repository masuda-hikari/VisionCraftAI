# -*- coding: utf-8 -*-
"""
VisionCraftAI - APIテスト

FastAPI エンドポイントのテストスイート。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient

from src.api.app import app
from src.api.schemas import (
    GenerateRequest,
    GenerateResponse,
    BatchRequest,
    BatchPromptItem,
    EstimateRequest,
)
from src.generator.gemini_client import GenerationResult
from src.generator.batch_processor import BatchResult


# テストクライアント
client = TestClient(app)


# テスト用APIキー取得ヘルパー
def get_test_api_key(tier: str = "enterprise") -> str:
    """テスト用APIキーを作成して取得"""
    response = client.post(
        "/api/v1/auth/keys",
        json={"tier": tier, "name": "Test Key"},
    )
    return response.json()["api_key"]


@pytest.fixture
def auth_headers():
    """認証ヘッダーを提供するフィクスチャ"""
    api_key = get_test_api_key()
    return {"X-API-Key": api_key}


class TestRootEndpoint:
    """ルートエンドポイントのテスト"""

    def test_root_returns_api_info(self):
        """ルートエンドポイントがAPI情報を返す"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "VisionCraftAI API"
        assert data["version"] == "0.1.0"
        assert "docs" in data
        assert "health" in data


class TestHealthEndpoint:
    """ヘルスチェックエンドポイントのテスト"""

    def test_health_check_basic(self):
        """基本的なヘルスチェック"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data

    def test_health_check_without_api_check(self):
        """API接続確認なしのヘルスチェック"""
        response = client.get("/api/v1/health?check_api=false")
        assert response.status_code == 200
        data = response.json()
        assert data["api_connection"] is None
        assert data["api_message"] is None


class TestPromptEndpoints:
    """プロンプト関連エンドポイントのテスト"""

    def test_validate_prompt_valid(self):
        """有効なプロンプトの検証"""
        response = client.post(
            "/api/v1/prompt/validate",
            params={"prompt": "A beautiful sunset over mountains"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["blocked_reason"] is None

    def test_validate_prompt_blocked(self):
        """禁止キーワードを含むプロンプトの検証"""
        response = client.post(
            "/api/v1/prompt/validate",
            params={"prompt": "Violence in the city"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["blocked_reason"] is not None

    def test_validate_prompt_with_warning(self):
        """警告キーワードを含むプロンプトの検証"""
        response = client.post(
            "/api/v1/prompt/validate",
            params={"prompt": "A portrait of a famous person"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert len(data["warnings"]) > 0

    def test_enhance_prompt_basic(self):
        """基本的なプロンプト拡張"""
        response = client.post(
            "/api/v1/prompt/enhance",
            params={"prompt": "A cat", "quality_boost": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["original_prompt"] == "A cat"
        assert "high quality" in data["enhanced_prompt"].lower()

    def test_enhance_prompt_with_style(self):
        """スタイル付きプロンプト拡張"""
        response = client.post(
            "/api/v1/prompt/enhance",
            params={"prompt": "A cat", "style": "anime", "quality_boost": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert "anime" in data["enhanced_prompt"].lower()


class TestGenerateEndpoint:
    """画像生成エンドポイントのテスト"""

    @patch("src.api.routes.get_client")
    @patch("src.api.routes.get_usage_tracker")
    def test_generate_success(self, mock_tracker, mock_client, auth_headers):
        """画像生成成功"""
        # モックの設定
        mock_result = GenerationResult(
            success=True,
            image_data=b"fake_image_data",
            file_path="outputs/test.png",
            prompt="test prompt",
            generation_time_ms=1000,
            model_used="gemini-2.0-flash-exp",
        )
        mock_client.return_value.generate_image.return_value = mock_result
        mock_tracker.return_value.record.return_value = Mock()

        response = client.post(
            "/api/v1/generate",
            json={"prompt": "A beautiful sunset", "quality_boost": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["image_base64"] is not None

    @patch("src.api.routes.get_client")
    @patch("src.api.routes.get_usage_tracker")
    def test_generate_failure(self, mock_tracker, mock_client, auth_headers):
        """画像生成失敗"""
        mock_result = GenerationResult(
            success=False,
            prompt="test prompt",
            error_message="API error",
            generation_time_ms=500,
            model_used="gemini-2.0-flash-exp",
        )
        mock_client.return_value.generate_image.return_value = mock_result
        mock_tracker.return_value.record.return_value = Mock()

        response = client.post(
            "/api/v1/generate",
            json={"prompt": "A beautiful sunset"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error_message"] == "API error"

    def test_generate_blocked_prompt(self, auth_headers):
        """禁止プロンプトでの生成"""
        response = client.post(
            "/api/v1/generate",
            json={"prompt": "Violence scene"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_generate_empty_prompt(self, auth_headers):
        """空プロンプトでの生成"""
        response = client.post(
            "/api/v1/generate",
            json={"prompt": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422  # バリデーションエラー

    def test_generate_invalid_style(self, auth_headers):
        """無効なスタイル指定"""
        response = client.post(
            "/api/v1/generate",
            json={"prompt": "A cat", "style": "invalid_style"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_generate_requires_auth(self):
        """画像生成に認証が必要"""
        response = client.post(
            "/api/v1/generate",
            json={"prompt": "A beautiful sunset"},
        )
        assert response.status_code == 401


class TestBatchEndpoints:
    """バッチ処理エンドポイントのテスト"""

    def test_estimate_batch_time(self):
        """バッチ処理時間見積もり"""
        response = client.post(
            "/api/v1/batch/estimate",
            json={"prompt_count": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["prompt_count"] == 10
        assert "total_estimated_seconds" in data
        assert "total_estimated_minutes" in data

    def test_estimate_batch_time_limits(self):
        """バッチ見積もりの範囲チェック"""
        # 下限
        response = client.post(
            "/api/v1/batch/estimate",
            json={"prompt_count": 0}
        )
        assert response.status_code == 422

        # 上限
        response = client.post(
            "/api/v1/batch/estimate",
            json={"prompt_count": 1001}
        )
        assert response.status_code == 422

    @patch("src.api.routes.get_batch_processor")
    @patch("src.api.routes.get_usage_tracker")
    def test_batch_generate_success(self, mock_tracker, mock_processor, auth_headers):
        """バッチ生成成功"""
        # モック設定
        mock_result = BatchResult(
            job_id="test_job",
            total_count=2,
            success_count=2,
            failure_count=0,
            results=[
                GenerationResult(
                    success=True,
                    file_path="outputs/1.png",
                    prompt="prompt 1",
                    generation_time_ms=1000,
                    model_used="gemini-2.0-flash-exp",
                ),
                GenerationResult(
                    success=True,
                    file_path="outputs/2.png",
                    prompt="prompt 2",
                    generation_time_ms=1000,
                    model_used="gemini-2.0-flash-exp",
                ),
            ],
            total_time_ms=2000,
            average_time_ms=1000.0,
        )
        mock_processor.return_value.process_batch.return_value = mock_result
        mock_tracker.return_value.record.return_value = Mock()

        response = client.post(
            "/api/v1/batch/generate",
            json={
                "prompts": [
                    {"prompt": "A cat"},
                    {"prompt": "A dog"}
                ]
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert data["success_count"] == 2

    def test_batch_generate_all_invalid(self, auth_headers):
        """全プロンプト無効のバッチ生成"""
        response = client.post(
            "/api/v1/batch/generate",
            json={
                "prompts": [
                    {"prompt": "violence"},
                    {"prompt": "murder"}
                ]
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_batch_generate_too_many_prompts(self, auth_headers):
        """プロンプト数上限超過（プランの制限）"""
        # EnterpriseはバッチサイズMAX100なので101でエラー
        response = client.post(
            "/api/v1/batch/generate",
            json={
                "prompts": [{"prompt": f"Test {i}"} for i in range(101)]
            },
            headers=auth_headers,
        )
        # スキーマレベルで100が上限なので422
        assert response.status_code == 422

    def test_batch_generate_requires_auth(self):
        """バッチ生成に認証が必要"""
        response = client.post(
            "/api/v1/batch/generate",
            json={
                "prompts": [
                    {"prompt": "A cat"},
                    {"prompt": "A dog"}
                ]
            },
        )
        assert response.status_code == 401


class TestUsageEndpoints:
    """使用量エンドポイントのテスト"""

    @patch("src.api.routes.get_usage_tracker")
    def test_get_usage_summary(self, mock_tracker):
        """使用量サマリー取得"""
        from src.utils.usage_tracker import UsageSummary
        mock_summary = UsageSummary(
            period_start="2026-01-01T00:00:00",
            period_end="2026-01-08T00:00:00",
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            total_generation_time_ms=100000,
            average_generation_time_ms=1000.0,
            total_estimated_cost_usd=1.0,
            operations_breakdown={"generate_image": 100},
        )
        mock_tracker.return_value.get_summary.return_value = mock_summary

        response = client.get("/api/v1/usage")
        assert response.status_code == 200
        data = response.json()
        assert data["total_requests"] == 100
        assert data["success_rate"] == 95.0

    @patch("src.api.routes.get_usage_tracker")
    def test_get_usage_summary_with_days(self, mock_tracker):
        """期間指定の使用量サマリー取得"""
        from src.utils.usage_tracker import UsageSummary
        mock_summary = UsageSummary(
            period_start="2026-01-01T00:00:00",
            period_end="2026-01-08T00:00:00",
            total_requests=50,
            successful_requests=48,
            failed_requests=2,
            total_generation_time_ms=50000,
            average_generation_time_ms=1000.0,
            total_estimated_cost_usd=0.5,
        )
        mock_tracker.return_value.get_summary.return_value = mock_summary

        response = client.get("/api/v1/usage?days=7")
        assert response.status_code == 200

    @patch("src.api.routes.get_usage_tracker")
    def test_get_daily_usage(self, mock_tracker):
        """日別使用量取得"""
        mock_tracker.return_value.get_daily_breakdown.return_value = [
            {
                "date": "2026-01-07",
                "requests": 10,
                "successful": 9,
                "failed": 1,
                "total_time_ms": 10000,
                "estimated_cost_usd": 0.1,
            },
            {
                "date": "2026-01-08",
                "requests": 15,
                "successful": 15,
                "failed": 0,
                "total_time_ms": 15000,
                "estimated_cost_usd": 0.15,
            },
        ]

        response = client.get("/api/v1/usage/daily?days=7")
        assert response.status_code == 200
        data = response.json()
        assert data["days"] == 7
        assert len(data["daily_data"]) == 2

    @patch("src.api.routes.get_usage_tracker")
    def test_export_usage_report(self, mock_tracker):
        """使用量レポートエクスポート"""
        from pathlib import Path
        mock_tracker.return_value.export_report.return_value = Path("logs/test_report.json")

        response = client.post("/api/v1/usage/export?days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "file_path" in data


class TestSchemas:
    """スキーマのテスト"""

    def test_generate_request_valid(self):
        """有効なGenerateRequest"""
        req = GenerateRequest(prompt="Test prompt")
        assert req.prompt == "Test prompt"
        assert req.quality_boost is True

    def test_generate_request_with_style(self):
        """スタイル付きGenerateRequest"""
        req = GenerateRequest(prompt="Test", style="anime")
        assert req.style == "anime"

    def test_generate_request_invalid_style(self):
        """無効なスタイル"""
        with pytest.raises(ValueError):
            GenerateRequest(prompt="Test", style="invalid")

    def test_batch_request_valid(self):
        """有効なBatchRequest"""
        req = BatchRequest(
            prompts=[
                BatchPromptItem(prompt="Test 1"),
                BatchPromptItem(prompt="Test 2"),
            ]
        )
        assert len(req.prompts) == 2

    def test_estimate_request_valid(self):
        """有効なEstimateRequest"""
        req = EstimateRequest(prompt_count=50)
        assert req.prompt_count == 50

    def test_estimate_request_bounds(self):
        """EstimateRequestの範囲チェック"""
        with pytest.raises(ValueError):
            EstimateRequest(prompt_count=0)
        with pytest.raises(ValueError):
            EstimateRequest(prompt_count=1001)


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_404_not_found(self):
        """存在しないエンドポイント"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed(self):
        """許可されていないメソッド"""
        response = client.put("/api/v1/generate", json={})
        assert response.status_code == 405
