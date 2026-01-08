# -*- coding: utf-8 -*-
"""
VisionCraftAI - Gemini APIクライアント

Google Gemini APIを使用した画像生成機能を提供します。
"""

import base64
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from src.utils.config import Config, GeminiConfig

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """画像生成結果"""
    success: bool
    image_data: Optional[bytes] = None
    file_path: Optional[str] = None
    prompt: str = ""
    error_message: Optional[str] = None
    generation_time_ms: int = 0
    model_used: str = ""


class GeminiClient:
    """
    Gemini API クライアント

    Google Gemini APIを使用した画像生成機能を提供します。
    レート制限とコスト管理を考慮した設計になっています。
    """

    def __init__(self, config: Optional[Config] = None):
        """
        クライアントを初期化

        Args:
            config: アプリケーション設定（省略時は環境変数から読み込み）
        """
        self.config = config or Config.from_env()
        self._client: Optional[genai.Client] = None
        self._request_count = 0

    def _get_client(self) -> genai.Client:
        """
        Gemini クライアントを取得（遅延初期化）

        Returns:
            genai.Client: 初期化されたクライアント

        Raises:
            ValueError: 認証情報が不正な場合
        """
        if self._client is None:
            try:
                # Vertex AI経由で接続
                self._client = genai.Client(
                    vertexai=True,
                    project=self.config.gemini.project_id,
                    location=self.config.gemini.location,
                )
                logger.info(
                    f"Gemini クライアント初期化完了: "
                    f"project={self.config.gemini.project_id}, "
                    f"location={self.config.gemini.location}"
                )
            except Exception as e:
                logger.error(f"Gemini クライアント初期化失敗: {e}")
                raise ValueError(f"Gemini APIへの接続に失敗しました: {e}") from e

        return self._client

    def generate_image(
        self,
        prompt: str,
        output_path: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> GenerationResult:
        """
        プロンプトから画像を生成

        Args:
            prompt: 画像生成プロンプト
            output_path: 出力ファイルパス（省略時は自動生成）
            width: 画像幅（省略時はデフォルト値）
            height: 画像高さ（省略時はデフォルト値）

        Returns:
            GenerationResult: 生成結果
        """
        start_time = datetime.now()

        # 入力検証
        if not prompt or not prompt.strip():
            return GenerationResult(
                success=False,
                prompt=prompt,
                error_message="プロンプトが空です",
            )

        try:
            client = self._get_client()

            # 画像生成リクエスト
            logger.info(f"画像生成リクエスト: {prompt[:50]}...")

            response = client.models.generate_content(
                model=self.config.gemini.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            self._request_count += 1

            # レスポンス処理
            image_data = None
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    break

            if image_data is None:
                return GenerationResult(
                    success=False,
                    prompt=prompt,
                    error_message="画像データが取得できませんでした",
                    model_used=self.config.gemini.model_name,
                )

            # ファイル保存
            if output_path is None:
                output_dir = self.config.ensure_output_dir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(
                    output_dir / f"generated_{timestamp}.{self.config.image.output_format}"
                )

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(image_data)

            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info(f"画像生成完了: {output_path} ({elapsed_ms}ms)")

            return GenerationResult(
                success=True,
                image_data=image_data,
                file_path=output_path,
                prompt=prompt,
                generation_time_ms=elapsed_ms,
                model_used=self.config.gemini.model_name,
            )

        except Exception as e:
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            error_msg = str(e)
            logger.error(f"画像生成エラー: {error_msg}")

            return GenerationResult(
                success=False,
                prompt=prompt,
                error_message=error_msg,
                generation_time_ms=elapsed_ms,
                model_used=self.config.gemini.model_name,
            )

    def get_request_count(self) -> int:
        """
        APIリクエスト回数を取得

        Returns:
            int: リクエスト回数
        """
        return self._request_count

    def check_connection(self) -> tuple[bool, str]:
        """
        API接続を確認

        Returns:
            tuple[bool, str]: (接続成功, メッセージ)
        """
        try:
            client = self._get_client()
            # 簡単なテキスト生成で接続確認
            response = client.models.generate_content(
                model=self.config.gemini.model_name,
                contents="Hello, respond with 'OK' only.",
            )
            return True, f"接続成功: {self.config.gemini.model_name}"
        except Exception as e:
            return False, f"接続失敗: {e}"
