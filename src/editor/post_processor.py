# -*- coding: utf-8 -*-
"""
VisionCraftAI - 画像後処理モジュール

生成された画像の後処理・最適化を行います。
"""

import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """後処理結果"""
    success: bool
    output_path: Optional[str] = None
    original_size: tuple[int, int] = (0, 0)
    processed_size: tuple[int, int] = (0, 0)
    file_size_bytes: int = 0
    error_message: Optional[str] = None


class PostProcessor:
    """
    画像後処理クラス

    生成画像のリサイズ、フォーマット変換、最適化を行います。
    """

    SUPPORTED_FORMATS = ["png", "jpeg", "jpg", "webp"]

    def __init__(self, default_quality: int = 95):
        """
        後処理を初期化

        Args:
            default_quality: デフォルトの出力品質（1-100）
        """
        self.default_quality = min(100, max(1, default_quality))

    def resize_image(
        self,
        image_data: bytes,
        width: int,
        height: int,
        maintain_aspect: bool = True,
        output_format: str = "png",
        quality: Optional[int] = None,
    ) -> tuple[bytes, tuple[int, int]]:
        """
        画像をリサイズ

        Args:
            image_data: 入力画像データ
            width: 目標幅
            height: 目標高さ
            maintain_aspect: アスペクト比を維持
            output_format: 出力フォーマット
            quality: 出力品質

        Returns:
            tuple[bytes, tuple[int, int]]: (出力データ, (実際の幅, 実際の高さ))
        """
        img = Image.open(io.BytesIO(image_data))
        original_width, original_height = img.size

        if maintain_aspect:
            # アスペクト比を維持してリサイズ
            ratio = min(width / original_width, height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
        else:
            new_width = width
            new_height = height

        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 出力
        output = io.BytesIO()
        save_kwargs = {}
        if output_format.lower() in ["jpeg", "jpg"]:
            # RGBAをRGBに変換（JPEG用）
            if resized.mode == "RGBA":
                resized = resized.convert("RGB")
            save_kwargs["quality"] = quality or self.default_quality
            save_kwargs["optimize"] = True
        elif output_format.lower() == "webp":
            save_kwargs["quality"] = quality or self.default_quality
        elif output_format.lower() == "png":
            save_kwargs["optimize"] = True

        resized.save(output, format=output_format.upper(), **save_kwargs)
        return output.getvalue(), (new_width, new_height)

    def convert_format(
        self,
        image_data: bytes,
        target_format: str,
        quality: Optional[int] = None,
    ) -> bytes:
        """
        画像フォーマットを変換

        Args:
            image_data: 入力画像データ
            target_format: 目標フォーマット（png, jpeg, webp）
            quality: 出力品質（非可逆圧縮用）

        Returns:
            bytes: 変換後の画像データ
        """
        if target_format.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"サポートされていないフォーマット: {target_format}")

        img = Image.open(io.BytesIO(image_data))

        output = io.BytesIO()
        save_kwargs = {}

        if target_format.lower() in ["jpeg", "jpg"]:
            if img.mode == "RGBA":
                img = img.convert("RGB")
            save_kwargs["quality"] = quality or self.default_quality
            save_kwargs["optimize"] = True
        elif target_format.lower() == "webp":
            save_kwargs["quality"] = quality or self.default_quality
        elif target_format.lower() == "png":
            save_kwargs["optimize"] = True

        img.save(output, format=target_format.upper(), **save_kwargs)
        return output.getvalue()

    def optimize_for_web(
        self,
        image_data: bytes,
        max_file_size_kb: int = 500,
        preferred_format: str = "webp",
    ) -> bytes:
        """
        Web用に画像を最適化

        Args:
            image_data: 入力画像データ
            max_file_size_kb: 最大ファイルサイズ（KB）
            preferred_format: 希望フォーマット

        Returns:
            bytes: 最適化後の画像データ
        """
        img = Image.open(io.BytesIO(image_data))
        quality = 95
        max_bytes = max_file_size_kb * 1024

        while quality > 10:
            output = io.BytesIO()
            save_kwargs = {}

            if preferred_format.lower() in ["jpeg", "jpg"]:
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                save_kwargs["quality"] = quality
                save_kwargs["optimize"] = True
            elif preferred_format.lower() == "webp":
                save_kwargs["quality"] = quality
            else:
                save_kwargs["optimize"] = True

            img.save(output, format=preferred_format.upper(), **save_kwargs)
            result = output.getvalue()

            if len(result) <= max_bytes:
                return result

            quality -= 10

        # 最低品質でも目標サイズに収まらない場合はリサイズ
        width, height = img.size
        while len(result) > max_bytes and width > 100:
            width = int(width * 0.8)
            height = int(height * 0.8)
            resized = img.resize((width, height), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            if preferred_format.lower() in ["jpeg", "jpg"]:
                if resized.mode == "RGBA":
                    resized = resized.convert("RGB")
            resized.save(output, format=preferred_format.upper(), quality=quality, optimize=True)
            result = output.getvalue()

        return result

    def process_and_save(
        self,
        image_data: bytes,
        output_path: str,
        resize: Optional[tuple[int, int]] = None,
        target_format: Optional[str] = None,
        quality: Optional[int] = None,
    ) -> ProcessingResult:
        """
        画像を処理して保存

        Args:
            image_data: 入力画像データ
            output_path: 出力パス
            resize: リサイズサイズ (width, height)
            target_format: 目標フォーマット
            quality: 出力品質

        Returns:
            ProcessingResult: 処理結果
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            original_size = img.size
            processed_data = image_data

            # リサイズ
            if resize:
                processed_data, processed_size = self.resize_image(
                    processed_data,
                    resize[0],
                    resize[1],
                    output_format=target_format or "png",
                    quality=quality,
                )
            else:
                processed_size = original_size

            # フォーマット変換
            if target_format:
                processed_data = self.convert_format(
                    processed_data,
                    target_format,
                    quality,
                )

            # 保存
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(processed_data)

            return ProcessingResult(
                success=True,
                output_path=str(output_file),
                original_size=original_size,
                processed_size=processed_size,
                file_size_bytes=len(processed_data),
            )

        except Exception as e:
            logger.error(f"画像処理エラー: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
            )

    @staticmethod
    def get_image_info(image_data: bytes) -> dict:
        """
        画像情報を取得

        Args:
            image_data: 画像データ

        Returns:
            dict: 画像情報
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            return {
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "size_bytes": len(image_data),
            }
        except Exception as e:
            return {"error": str(e)}
