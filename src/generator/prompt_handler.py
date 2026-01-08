# -*- coding: utf-8 -*-
"""
VisionCraftAI - プロンプトハンドラー

ユーザー入力のプロンプトを処理・安全性フィルタリングします。
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PromptValidationResult:
    """プロンプト検証結果"""
    is_valid: bool
    sanitized_prompt: str
    original_prompt: str
    warnings: list[str] = field(default_factory=list)
    blocked_reason: Optional[str] = None


class PromptHandler:
    """
    プロンプト処理クラス

    ユーザー入力の安全性チェック、サニタイズ、拡張を行います。
    """

    # 禁止キーワード（不適切コンテンツ防止）
    BLOCKED_KEYWORDS: list[str] = [
        # 暴力・危険
        "violence", "gore", "blood", "weapon", "kill", "murder",
        # 不適切コンテンツ
        "nsfw", "nude", "explicit", "pornographic",
        # 著作権侵害
        "copyrighted", "trademarked",
        # 日本語禁止キーワード
        "暴力", "殺人", "武器", "ヌード", "成人向け",
    ]

    # 警告キーワード（生成は許可するが警告）
    WARNING_KEYWORDS: list[str] = [
        "celebrity", "famous person", "real person",
        "有名人", "芸能人", "実在の人物",
    ]

    # プロンプト最大長
    MAX_PROMPT_LENGTH: int = 2000

    def __init__(self, custom_blocked: Optional[list[str]] = None):
        """
        ハンドラーを初期化

        Args:
            custom_blocked: 追加の禁止キーワード
        """
        self.blocked_keywords = self.BLOCKED_KEYWORDS.copy()
        if custom_blocked:
            self.blocked_keywords.extend(custom_blocked)

    def validate_and_sanitize(self, prompt: str) -> PromptValidationResult:
        """
        プロンプトを検証しサニタイズ

        Args:
            prompt: ユーザー入力プロンプト

        Returns:
            PromptValidationResult: 検証結果
        """
        original = prompt
        warnings: list[str] = []

        # 空チェック
        if not prompt or not prompt.strip():
            return PromptValidationResult(
                is_valid=False,
                sanitized_prompt="",
                original_prompt=original,
                blocked_reason="プロンプトが空です",
            )

        # 基本サニタイズ
        sanitized = prompt.strip()

        # 長さチェック
        if len(sanitized) > self.MAX_PROMPT_LENGTH:
            sanitized = sanitized[:self.MAX_PROMPT_LENGTH]
            warnings.append(f"プロンプトが{self.MAX_PROMPT_LENGTH}文字に切り詰められました")

        # 禁止キーワードチェック
        prompt_lower = sanitized.lower()
        for keyword in self.blocked_keywords:
            if keyword.lower() in prompt_lower:
                return PromptValidationResult(
                    is_valid=False,
                    sanitized_prompt="",
                    original_prompt=original,
                    blocked_reason=f"禁止キーワードが含まれています: {keyword}",
                )

        # 警告キーワードチェック
        for keyword in self.WARNING_KEYWORDS:
            if keyword.lower() in prompt_lower:
                warnings.append(f"注意: '{keyword}' が含まれています。実在の人物の画像生成は推奨されません")

        # 制御文字除去
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)

        # 連続空白の正規化
        sanitized = re.sub(r'\s+', ' ', sanitized)

        return PromptValidationResult(
            is_valid=True,
            sanitized_prompt=sanitized,
            original_prompt=original,
            warnings=warnings,
        )

    def enhance_prompt(
        self,
        prompt: str,
        style: Optional[str] = None,
        quality_boost: bool = True,
    ) -> str:
        """
        プロンプトを拡張（品質向上）

        Args:
            prompt: 基本プロンプト
            style: 適用するスタイル（例: "photorealistic", "anime", "watercolor"）
            quality_boost: 品質向上キーワードを追加

        Returns:
            str: 拡張されたプロンプト
        """
        parts = [prompt]

        # スタイル適用
        style_mappings = {
            "photorealistic": "photorealistic, highly detailed, 8k resolution",
            "anime": "anime style, vibrant colors, detailed linework",
            "watercolor": "watercolor painting, soft colors, artistic",
            "oil_painting": "oil painting style, rich textures, classical",
            "digital_art": "digital art, modern, clean lines",
            "sketch": "pencil sketch, hand-drawn, artistic",
        }

        if style and style.lower() in style_mappings:
            parts.append(style_mappings[style.lower()])

        # 品質向上キーワード
        if quality_boost:
            parts.append("high quality, detailed, professional")

        return ", ".join(parts)

    @staticmethod
    def suggest_improvements(prompt: str) -> list[str]:
        """
        プロンプト改善提案を生成

        Args:
            prompt: 元のプロンプト

        Returns:
            list[str]: 改善提案リスト
        """
        suggestions: list[str] = []

        # 短すぎるプロンプト
        if len(prompt) < 20:
            suggestions.append("より詳細な説明を追加すると品質が向上します")

        # 色の指定がない
        color_keywords = ["red", "blue", "green", "color", "色", "赤", "青", "緑"]
        if not any(kw in prompt.lower() for kw in color_keywords):
            suggestions.append("色の指定を追加すると意図した結果が得られやすくなります")

        # 構図の指定がない
        composition_keywords = ["background", "foreground", "center", "背景", "前景", "中央"]
        if not any(kw in prompt.lower() for kw in composition_keywords):
            suggestions.append("構図の指定を追加することを検討してください")

        return suggestions
