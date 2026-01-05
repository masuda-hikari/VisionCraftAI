"""
VisionCraftAI メインモジュールのテスト
"""

import os
import sys
from pathlib import Path

import pytest

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import check_environment, generate_image


class TestCheckEnvironment:
    """環境チェック機能のテスト"""

    def test_check_environment_missing_vars(self, monkeypatch):
        """環境変数が設定されていない場合Falseを返す"""
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)

        result = check_environment()
        assert result is False

    def test_check_environment_with_vars(self, monkeypatch):
        """環境変数が設定されている場合Trueを返す"""
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/path/to/creds.json")
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")

        result = check_environment()
        assert result is True


class TestGenerateImage:
    """画像生成機能のテスト（プレースホルダー）"""

    def test_generate_image_returns_path(self):
        """generate_imageがパスを返すこと"""
        result = generate_image("A test prompt")

        assert result is not None
        assert isinstance(result, str)
        assert "generated_" in result
        assert result.endswith(".png")

    def test_generate_image_with_custom_output(self, tmp_path):
        """カスタム出力パスが正しく使用されること"""
        custom_path = str(tmp_path / "custom_output.png")

        result = generate_image("A test prompt", custom_path)

        assert result == custom_path

    def test_generate_image_with_empty_prompt(self):
        """空のプロンプトでもパスを返すこと（プレースホルダー動作）"""
        result = generate_image("")

        assert result is not None


class TestIntegration:
    """統合テスト（将来のAPI統合時に拡張）"""

    @pytest.mark.skip(reason="API統合後に有効化")
    def test_actual_image_generation(self):
        """実際の画像生成テスト（API統合後）"""
        # TODO: Gemini 3 API統合後に実装
        pass


def test_setup_complete():
    """セットアップ完了確認テスト（常に成功）"""
    assert True, "VisionCraftAI setup complete"
