# -*- coding: utf-8 -*-
"""
VisionCraftAI - デモAPI テスト

デモモード機能のテストスイート
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


class TestDemoSamples:
    """デモサンプル一覧テスト"""

    def test_get_demo_samples(self, client):
        """サンプル一覧取得"""
        response = client.get("/api/v1/demo/samples")
        assert response.status_code == 200

        data = response.json()
        assert "samples" in data
        assert "total_count" in data
        assert data["total_count"] > 0

        # サンプルの構造確認
        sample = data["samples"][0]
        assert "id" in sample
        assert "name" in sample
        assert "description" in sample
        assert "style" in sample
        assert "keywords" in sample

    def test_samples_have_required_fields(self, client):
        """サンプルが必須フィールドを持つ"""
        response = client.get("/api/v1/demo/samples")
        data = response.json()

        for sample in data["samples"]:
            assert len(sample["id"]) > 0
            assert len(sample["name"]) > 0
            assert len(sample["description"]) > 0


class TestDemoGenerate:
    """デモ画像生成テスト"""

    def test_demo_generate_success(self, client):
        """デモ画像生成成功"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "beautiful sunset over mountains"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["demo_mode"] is True
        assert "prompt" in data
        assert "image_url" in data
        assert "message" in data
        assert "upgrade_info" in data

    def test_demo_generate_with_style(self, client):
        """スタイル指定でデモ画像生成"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "futuristic city", "style": "cyberpunk"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    def test_demo_generate_japanese_prompt(self, client):
        """日本語プロンプトでデモ画像生成"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "美しい夕日と山"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "夕日" in data["prompt"] or "sunset" in data.get("matched_sample", "").lower()

    def test_demo_generate_empty_prompt(self, client):
        """空のプロンプトはエラー"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": ""}
        )
        assert response.status_code == 422  # Validation error

    def test_demo_generate_whitespace_prompt(self, client):
        """空白のみのプロンプトはエラー"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "   "}
        )
        assert response.status_code == 400

    def test_demo_generate_returns_svg(self, client):
        """デモ生成はSVGを返す"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "test image"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["image_url"].startswith("data:image/svg+xml;base64,")

    def test_demo_generate_has_upgrade_info(self, client):
        """アップグレード情報を含む"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "test"}
        )
        assert response.status_code == 200

        data = response.json()
        upgrade_info = data["upgrade_info"]
        assert "message" in upgrade_info
        assert "pricing_url" in upgrade_info
        assert "features" in upgrade_info
        assert len(upgrade_info["features"]) > 0

    def test_demo_generate_matches_sunset_keywords(self, client):
        """夕日関連キーワードでマッチング"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "beautiful sunset scenery"}
        )
        assert response.status_code == 200

        data = response.json()
        # sunsetキーワードにマッチするはず
        assert data["matched_sample"] is not None

    def test_demo_generate_matches_city_keywords(self, client):
        """都市関連キーワードでマッチング"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "cyberpunk neon city"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["matched_sample"] is not None

    def test_demo_generate_matches_ocean_keywords(self, client):
        """海関連キーワードでマッチング"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "underwater coral reef fish"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["matched_sample"] is not None

    def test_demo_generate_generation_time(self, client):
        """生成時間が返される"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "test image"}
        )
        assert response.status_code == 200

        data = response.json()
        assert "generation_time_ms" in data
        assert data["generation_time_ms"] > 0


class TestDemoInfo:
    """デモモード情報テスト"""

    def test_get_demo_info(self, client):
        """デモ情報取得"""
        response = client.get("/api/v1/demo/info")
        assert response.status_code == 200

        data = response.json()
        assert data["demo_mode"] is True
        assert "description" in data
        assert "limitations" in data
        assert "features_available" in data
        assert "upgrade_benefits" in data
        assert "pricing" in data

    def test_demo_info_has_pricing(self, client):
        """料金情報を含む"""
        response = client.get("/api/v1/demo/info")
        data = response.json()

        pricing = data["pricing"]
        assert "free" in pricing
        assert "basic" in pricing
        assert "pro" in pricing
        assert "enterprise" in pricing

        # 各プランの構造確認
        assert pricing["free"]["price"] == 0
        assert pricing["basic"]["price"] > 0
        assert pricing["pro"]["price"] > pricing["basic"]["price"]

    def test_demo_info_has_urls(self, client):
        """関連URLを含む"""
        response = client.get("/api/v1/demo/info")
        data = response.json()

        assert "get_started_url" in data
        assert "docs_url" in data


class TestDemoNoAuth:
    """デモAPIは認証不要であることを確認"""

    def test_demo_samples_no_auth(self, client):
        """サンプル一覧は認証不要"""
        response = client.get("/api/v1/demo/samples")
        assert response.status_code == 200

    def test_demo_generate_no_auth(self, client):
        """デモ生成は認証不要"""
        response = client.post(
            "/api/v1/demo/generate",
            json={"prompt": "test"}
        )
        assert response.status_code == 200

    def test_demo_info_no_auth(self, client):
        """デモ情報は認証不要"""
        response = client.get("/api/v1/demo/info")
        assert response.status_code == 200


class TestDemoIntegration:
    """デモ機能の統合テスト"""

    def test_demo_flow(self, client):
        """デモフロー全体のテスト"""
        # 1. デモ情報取得
        info_response = client.get("/api/v1/demo/info")
        assert info_response.status_code == 200

        # 2. サンプル一覧取得
        samples_response = client.get("/api/v1/demo/samples")
        assert samples_response.status_code == 200
        samples = samples_response.json()["samples"]

        # 3. サンプルのキーワードで生成
        if samples:
            keyword = samples[0]["keywords"][0]
            generate_response = client.post(
                "/api/v1/demo/generate",
                json={"prompt": keyword}
            )
            assert generate_response.status_code == 200
            assert generate_response.json()["success"] is True

    def test_various_prompts(self, client):
        """様々なプロンプトでテスト"""
        prompts = [
            "a cat sitting on a window",
            "宇宙を飛ぶ宇宙船",
            "abstract colorful patterns",
            "forest with sunlight",
            "portrait of a robot",
        ]

        for prompt in prompts:
            response = client.post(
                "/api/v1/demo/generate",
                json={"prompt": prompt}
            )
            assert response.status_code == 200
            assert response.json()["success"] is True
