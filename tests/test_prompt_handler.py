# -*- coding: utf-8 -*-
"""
VisionCraftAI - プロンプトハンドラーのテスト
"""

import pytest

from src.generator.prompt_handler import PromptHandler, PromptValidationResult


class TestPromptValidation:
    """プロンプト検証のテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.handler = PromptHandler()

    def test_valid_prompt(self):
        """有効なプロンプトが正しく処理されること"""
        result = self.handler.validate_and_sanitize("A beautiful sunset over mountains")

        assert result.is_valid is True
        assert result.sanitized_prompt == "A beautiful sunset over mountains"
        assert len(result.warnings) == 0
        assert result.blocked_reason is None

    def test_empty_prompt(self):
        """空のプロンプトが拒否されること"""
        result = self.handler.validate_and_sanitize("")

        assert result.is_valid is False
        assert result.blocked_reason is not None

    def test_whitespace_only_prompt(self):
        """空白のみのプロンプトが拒否されること"""
        result = self.handler.validate_and_sanitize("   ")

        assert result.is_valid is False

    def test_blocked_keyword(self):
        """禁止キーワードを含むプロンプトが拒否されること"""
        result = self.handler.validate_and_sanitize("Generate violence scene")

        assert result.is_valid is False
        assert result.blocked_reason is not None
        assert "禁止キーワード" in result.blocked_reason

    def test_warning_keyword(self):
        """警告キーワードで警告が出ること"""
        result = self.handler.validate_and_sanitize("Draw a celebrity portrait")

        assert result.is_valid is True
        assert len(result.warnings) > 0

    def test_long_prompt_truncation(self):
        """長いプロンプトが切り詰められること"""
        long_prompt = "a" * 3000
        result = self.handler.validate_and_sanitize(long_prompt)

        assert result.is_valid is True
        assert len(result.sanitized_prompt) == 2000
        assert any("切り詰められ" in w for w in result.warnings)

    def test_control_character_removal(self):
        """制御文字が除去されること"""
        result = self.handler.validate_and_sanitize("Hello\x00World\x1f")

        assert result.is_valid is True
        assert "\x00" not in result.sanitized_prompt
        assert "\x1f" not in result.sanitized_prompt

    def test_whitespace_normalization(self):
        """連続空白が正規化されること"""
        result = self.handler.validate_and_sanitize("Hello    World")

        assert result.is_valid is True
        assert result.sanitized_prompt == "Hello World"

    def test_japanese_blocked_keyword(self):
        """日本語の禁止キーワードが検出されること"""
        result = self.handler.validate_and_sanitize("暴力的なシーン")

        assert result.is_valid is False

    def test_custom_blocked_keywords(self):
        """カスタム禁止キーワードが機能すること"""
        handler = PromptHandler(custom_blocked=["custom_block"])
        result = handler.validate_and_sanitize("Generate custom_block image")

        assert result.is_valid is False


class TestPromptEnhancement:
    """プロンプト拡張のテスト"""

    def setup_method(self):
        self.handler = PromptHandler()

    def test_enhance_with_style(self):
        """スタイル適用が機能すること"""
        result = self.handler.enhance_prompt(
            "A cat",
            style="photorealistic",
        )

        assert "photorealistic" in result
        assert "A cat" in result

    def test_enhance_with_quality_boost(self):
        """品質向上キーワードが追加されること"""
        result = self.handler.enhance_prompt(
            "A dog",
            quality_boost=True,
        )

        assert "high quality" in result

    def test_enhance_without_quality_boost(self):
        """品質向上を無効化できること"""
        result = self.handler.enhance_prompt(
            "A bird",
            quality_boost=False,
        )

        assert "high quality" not in result

    def test_unknown_style_ignored(self):
        """未知のスタイルは無視されること"""
        result = self.handler.enhance_prompt(
            "A fish",
            style="unknown_style",
        )

        assert "A fish" in result


class TestPromptSuggestions:
    """プロンプト改善提案のテスト"""

    def test_short_prompt_suggestion(self):
        """短いプロンプトに改善提案が出ること"""
        suggestions = PromptHandler.suggest_improvements("A cat")

        assert len(suggestions) > 0
        assert any("詳細" in s for s in suggestions)

    def test_detailed_prompt_no_suggestion(self):
        """詳細なプロンプトには短い提案がないこと"""
        detailed = "A beautiful orange cat sitting on a red couch with blue background"
        suggestions = PromptHandler.suggest_improvements(detailed)

        # 色と構図を含むので、関連する提案は出ない
        assert not any("色" in s for s in suggestions)
        assert not any("構図" in s for s in suggestions)
