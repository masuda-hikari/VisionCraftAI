#!/usr/bin/env python3
"""
VisionCraftAI - AI画像生成プラットフォーム

このモジュールはVisionCraftAIのエントリーポイントです。
Google Gemini APIを使用した画像生成機能を提供します。
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment() -> bool:
    """
    必要な環境変数が設定されているか確認

    Returns:
        bool: 環境が正しく設定されている場合True
    """
    required_vars = [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_CLOUD_PROJECT",
    ]

    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        print(f"警告: 以下の環境変数が設定されていません: {', '.join(missing)}")
        print("本番環境では必ず設定してください。")
        return False

    return True


def generate_image(prompt: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    プロンプトから画像を生成

    Args:
        prompt: 画像生成プロンプト
        output_path: 出力ファイルパス（省略時は自動生成）

    Returns:
        生成された画像のパス、またはNone（エラー時）
    """
    # 環境変数チェック
    if not check_environment():
        logger.warning("環境変数が設定されていないためプレースホルダーモードで動作")
        print(f"[プレースホルダー] 画像生成リクエスト受信:")
        print(f"  プロンプト: {prompt}")

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(__file__).parent.parent / "outputs"
            output_dir.mkdir(exist_ok=True)
            output_path = str(output_dir / f"generated_{timestamp}.png")

        print(f"  出力先: {output_path}")
        print()
        print("注意: これはプレースホルダー実装です。")
        print("実際の画像生成にはGemini API認証設定が必要です。")
        return output_path

    # Gemini APIを使用した実際の画像生成
    try:
        from src.generator.gemini_client import GeminiClient
        from src.generator.prompt_handler import PromptHandler

        # プロンプト検証
        handler = PromptHandler()
        validation = handler.validate_and_sanitize(prompt)

        if not validation.is_valid:
            logger.error(f"プロンプト検証エラー: {validation.blocked_reason}")
            print(f"エラー: {validation.blocked_reason}")
            return None

        if validation.warnings:
            for warning in validation.warnings:
                logger.warning(warning)
                print(f"警告: {warning}")

        # 画像生成
        client = GeminiClient()
        result = client.generate_image(validation.sanitized_prompt, output_path)

        if result.success:
            logger.info(f"画像生成成功: {result.file_path}")
            return result.file_path
        else:
            logger.error(f"画像生成失敗: {result.error_message}")
            print(f"エラー: {result.error_message}")
            return None

    except ImportError as e:
        logger.error(f"モジュールインポートエラー: {e}")
        print("エラー: 必要なモジュールがインストールされていません")
        print("pip install -r requirements.txt を実行してください")
        return None
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        print(f"エラー: {e}")
        return None


def main() -> int:
    """
    メインエントリーポイント

    Returns:
        終了コード（0: 成功、1: エラー）
    """
    print("=" * 50)
    print("VisionCraftAI - AI画像生成プラットフォーム")
    print("=" * 50)
    print()

    parser = argparse.ArgumentParser(
        description="VisionCraftAI - AI画像生成ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py --prompt "A beautiful sunset over mountains"
  python main.py --prompt "Futuristic city" --output outputs/city.png
  python main.py --prompt "A cat" --style photorealistic
        """
    )

    parser.add_argument(
        "--prompt", "-p",
        type=str,
        help="画像生成プロンプト"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="出力ファイルパス"
    )

    parser.add_argument(
        "--style", "-s",
        type=str,
        choices=["photorealistic", "anime", "watercolor", "oil_painting", "digital_art", "sketch"],
        help="画像スタイル"
    )

    parser.add_argument(
        "--check-env",
        action="store_true",
        help="環境設定を確認"
    )

    parser.add_argument(
        "--check-api",
        action="store_true",
        help="API接続を確認"
    )

    args = parser.parse_args()

    # 環境チェックモード
    if args.check_env:
        if check_environment():
            print("環境設定OK")
            return 0
        else:
            return 1

    # API接続チェックモード
    if args.check_api:
        try:
            from src.generator.gemini_client import GeminiClient
            client = GeminiClient()
            success, message = client.check_connection()
            print(message)
            return 0 if success else 1
        except Exception as e:
            print(f"API接続確認エラー: {e}")
            return 1

    # プロンプトが指定されていない場合
    if not args.prompt:
        print("VisionCraftAI セットアップ完了!")
        print()
        print("使用方法:")
        print("  python main.py --prompt \"your image description\"")
        print()
        print("オプション:")
        print("  --style     : 画像スタイル (photorealistic, anime, watercolor等)")
        print("  --output    : 出力ファイルパス")
        print("  --check-env : 環境設定確認")
        print("  --check-api : API接続確認")
        print()
        check_environment()
        return 0

    # スタイル適用
    prompt = args.prompt
    if args.style:
        try:
            from src.generator.prompt_handler import PromptHandler
            handler = PromptHandler()
            prompt = handler.enhance_prompt(args.prompt, style=args.style)
            logger.info(f"スタイル適用: {args.style}")
        except ImportError:
            logger.warning("PromptHandlerが利用できないためスタイル適用をスキップ")

    # 画像生成
    result = generate_image(prompt, args.output)

    if result:
        print(f"画像生成リクエスト処理完了: {result}")
        return 0
    else:
        print("画像生成に失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
