# -*- coding: utf-8 -*-
"""
VisionCraftAI - 設定モジュールのテスト
"""

import os
from pathlib import Path

import pytest

from src.utils.config import Config, GeminiConfig, ImageConfig


class TestGeminiConfig:
    """Gemini設定のテスト"""

    def test_default_values(self):
        """デフォルト値が正しく設定されること"""
        config = GeminiConfig()

        assert config.project_id == ""
        assert config.location == "us-central1"
        assert config.credentials_path is None
        assert config.max_requests_per_minute == 60


class TestImageConfig:
    """画像設定のテスト"""

    def test_default_values(self):
        """デフォルト値が正しく設定されること"""
        config = ImageConfig()

        assert config.default_width == 1024
        assert config.default_height == 1024
        assert config.output_format == "png"
        assert config.quality == 95


class TestConfig:
    """全体設定のテスト"""

    def test_from_env_with_vars(self, monkeypatch):
        """環境変数から正しく読み込まれること"""
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
        monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "asia-northeast1")
        monkeypatch.setenv("IMAGE_WIDTH", "512")
        monkeypatch.setenv("DEBUG", "true")

        config = Config.from_env()

        assert config.gemini.project_id == "test-project"
        assert config.gemini.location == "asia-northeast1"
        assert config.image.default_width == 512
        assert config.debug is True

    def test_from_env_without_vars(self, monkeypatch):
        """環境変数がない場合にデフォルト値が使用されること"""
        # 既存の環境変数をクリア
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

        config = Config.from_env()

        assert config.gemini.project_id == ""
        assert config.debug is False

    def test_validate_missing_project(self, monkeypatch):
        """プロジェクトIDがない場合にバリデーションエラー"""
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

        config = Config.from_env()
        is_valid, errors = config.validate()

        assert is_valid is False
        assert any("GOOGLE_CLOUD_PROJECT" in e for e in errors)

    def test_validate_invalid_image_size(self, monkeypatch):
        """無効な画像サイズでバリデーションエラー"""
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
        monkeypatch.setenv("IMAGE_WIDTH", "50")  # 最小値未満

        config = Config.from_env()
        is_valid, errors = config.validate()

        assert is_valid is False
        assert any("画像幅" in e for e in errors)

    def test_ensure_output_dir(self, tmp_path, monkeypatch):
        """出力ディレクトリが作成されること"""
        output_dir = tmp_path / "test_outputs"
        monkeypatch.setenv("OUTPUT_DIR", str(output_dir))

        config = Config.from_env()
        result = config.ensure_output_dir()

        assert result.exists()
        assert result.is_dir()
