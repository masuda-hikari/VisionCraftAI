# -*- coding: utf-8 -*-
"""
VisionCraftAI - 画像後処理のテスト
"""

import io
from pathlib import Path

import pytest
from PIL import Image

from src.editor.post_processor import PostProcessor, ProcessingResult


def create_test_image(
    width: int = 100,
    height: int = 100,
    color: tuple = (255, 0, 0),
    mode: str = "RGB",
    format: str = "PNG",
) -> bytes:
    """テスト用画像を生成"""
    img = Image.new(mode, (width, height), color)
    output = io.BytesIO()
    img.save(output, format=format)
    return output.getvalue()


class TestPostProcessor:
    """後処理クラスのテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        self.processor = PostProcessor(default_quality=90)

    def test_resize_image(self):
        """リサイズが正しく動作すること"""
        original = create_test_image(200, 200)
        resized_data, size = self.processor.resize_image(
            original, 100, 100, maintain_aspect=True
        )

        assert size == (100, 100)
        assert len(resized_data) > 0

        # 実際の画像サイズを確認
        img = Image.open(io.BytesIO(resized_data))
        assert img.size == (100, 100)

    def test_resize_maintain_aspect(self):
        """アスペクト比維持リサイズが正しく動作すること"""
        # 200x100の画像を100x100にリサイズ（アスペクト比維持）
        original = create_test_image(200, 100)
        resized_data, size = self.processor.resize_image(
            original, 100, 100, maintain_aspect=True
        )

        # 幅100で高さは50になるはず（2:1のアスペクト比維持）
        assert size == (100, 50)

    def test_convert_format_to_jpeg(self):
        """PNG→JPEG変換が正しく動作すること"""
        original = create_test_image(format="PNG")
        converted = self.processor.convert_format(original, "jpeg")

        img = Image.open(io.BytesIO(converted))
        assert img.format == "JPEG"

    def test_convert_format_to_webp(self):
        """PNG→WebP変換が正しく動作すること"""
        original = create_test_image(format="PNG")
        converted = self.processor.convert_format(original, "webp")

        img = Image.open(io.BytesIO(converted))
        assert img.format == "WEBP"

    def test_convert_rgba_to_jpeg(self):
        """RGBA→JPEG変換でRGBに変換されること"""
        original = create_test_image(mode="RGBA", color=(255, 0, 0, 128))
        converted = self.processor.convert_format(original, "jpeg")

        img = Image.open(io.BytesIO(converted))
        assert img.mode == "RGB"

    def test_unsupported_format_error(self):
        """サポートされていないフォーマットでエラー"""
        original = create_test_image()

        with pytest.raises(ValueError, match="サポートされていないフォーマット"):
            self.processor.convert_format(original, "bmp")

    def test_optimize_for_web(self):
        """Web最適化が動作すること"""
        # 大きな画像を作成
        original = create_test_image(500, 500)
        optimized = self.processor.optimize_for_web(
            original, max_file_size_kb=10, preferred_format="webp"
        )

        assert len(optimized) <= 10 * 1024  # 10KB以下

    def test_process_and_save(self, tmp_path):
        """処理と保存が正しく動作すること"""
        original = create_test_image(200, 200)
        output_path = str(tmp_path / "processed.png")

        result = self.processor.process_and_save(
            original,
            output_path,
            resize=(100, 100),
        )

        assert result.success is True
        assert result.output_path == output_path
        assert result.original_size == (200, 200)
        assert result.processed_size == (100, 100)
        assert Path(output_path).exists()

    def test_process_and_save_with_format_conversion(self, tmp_path):
        """フォーマット変換付き保存が動作すること"""
        original = create_test_image(format="PNG")
        output_path = str(tmp_path / "converted.jpg")

        result = self.processor.process_and_save(
            original,
            output_path,
            target_format="jpeg",
            quality=80,
        )

        assert result.success is True
        img = Image.open(output_path)
        assert img.format == "JPEG"

    def test_process_invalid_data(self, tmp_path):
        """無効なデータでエラーハンドリングされること"""
        output_path = str(tmp_path / "invalid.png")

        result = self.processor.process_and_save(
            b"invalid image data",
            output_path,
        )

        assert result.success is False
        assert result.error_message is not None

    def test_get_image_info(self):
        """画像情報取得が正しく動作すること"""
        original = create_test_image(300, 200, format="PNG")
        info = PostProcessor.get_image_info(original)

        assert info["format"] == "PNG"
        assert info["width"] == 300
        assert info["height"] == 200
        assert info["mode"] == "RGB"

    def test_get_image_info_invalid_data(self):
        """無効なデータでエラー情報が返ること"""
        info = PostProcessor.get_image_info(b"invalid data")

        assert "error" in info
