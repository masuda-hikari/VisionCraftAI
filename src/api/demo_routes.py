# -*- coding: utf-8 -*-
"""
VisionCraftAI - デモAPIルーター

認証情報なしでもサービスを体験できるデモ機能を提供します。
収益化への貢献: ユーザー獲得・コンバージョン向上
"""

import base64
import hashlib
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ルーター初期化
router = APIRouter(prefix="/demo", tags=["Demo"])

# デモ用サンプル画像の定義
DEMO_SAMPLES = {
    "sunset": {
        "name": "夕日の風景",
        "description": "山の上に沈む美しい夕日",
        "keywords": ["sunset", "夕日", "風景", "山", "空", "nature"],
        "style": "realistic",
    },
    "city": {
        "name": "近未来都市",
        "description": "ネオンが輝くサイバーパンク風の都市",
        "keywords": ["city", "都市", "サイバーパンク", "cyberpunk", "neon", "未来"],
        "style": "cyberpunk",
    },
    "forest": {
        "name": "幻想的な森",
        "description": "光が差し込む神秘的な森",
        "keywords": ["forest", "森", "幻想", "fantasy", "自然", "光"],
        "style": "fantasy",
    },
    "ocean": {
        "name": "海中世界",
        "description": "色鮮やかな海中の生態系",
        "keywords": ["ocean", "海", "水中", "underwater", "魚", "珊瑚"],
        "style": "realistic",
    },
    "space": {
        "name": "宇宙探査",
        "description": "壮大な宇宙と惑星",
        "keywords": ["space", "宇宙", "惑星", "星", "galaxy", "銀河"],
        "style": "sci-fi",
    },
    "portrait": {
        "name": "AIポートレート",
        "description": "AIが生成したポートレート",
        "keywords": ["portrait", "人物", "ポートレート", "face", "顔"],
        "style": "artistic",
    },
    "animal": {
        "name": "可愛い動物",
        "description": "愛らしい動物のイラスト",
        "keywords": ["animal", "動物", "cat", "猫", "dog", "犬", "cute"],
        "style": "illustration",
    },
    "abstract": {
        "name": "抽象アート",
        "description": "色彩豊かな抽象的アートワーク",
        "keywords": ["abstract", "抽象", "アート", "art", "色彩"],
        "style": "abstract",
    },
}


class DemoGenerateRequest(BaseModel):
    """デモ画像生成リクエスト"""
    prompt: str = Field(..., min_length=1, max_length=500, description="画像生成プロンプト")
    style: Optional[str] = Field(None, description="スタイル（realistic, fantasy, etc.）")


class DemoGenerateResponse(BaseModel):
    """デモ画像生成レスポンス"""
    success: bool = Field(..., description="処理成功フラグ")
    demo_mode: bool = Field(True, description="デモモードフラグ")
    prompt: str = Field(..., description="入力プロンプト")
    matched_sample: Optional[str] = Field(None, description="マッチしたサンプル名")
    sample_info: Optional[dict] = Field(None, description="サンプル情報")
    image_url: Optional[str] = Field(None, description="画像URL")
    message: str = Field(..., description="メッセージ")
    generation_time_ms: int = Field(0, description="擬似生成時間（ms）")
    upgrade_info: dict = Field(
        default_factory=lambda: {
            "message": "本番環境では高品質なAI画像を生成できます",
            "pricing_url": "/#pricing",
            "features": [
                "プロンプトに完全対応した画像生成",
                "最大4096x4096の高解像度",
                "多様なスタイルとカスタマイズ",
                "商用利用可能",
            ],
        },
        description="アップグレード案内",
    )


class DemoSamplesResponse(BaseModel):
    """デモサンプル一覧レスポンス"""
    samples: list[dict] = Field(..., description="利用可能なサンプル一覧")
    total_count: int = Field(..., description="サンプル総数")


def find_matching_sample(prompt: str, style: Optional[str] = None) -> Optional[str]:
    """
    プロンプトに最もマッチするサンプルを検索

    Args:
        prompt: ユーザー入力プロンプト
        style: 指定スタイル

    Returns:
        マッチしたサンプルのキー、またはNone
    """
    prompt_lower = prompt.lower()
    best_match = None
    best_score = 0

    for key, sample in DEMO_SAMPLES.items():
        score = 0

        # キーワードマッチング
        for keyword in sample["keywords"]:
            if keyword.lower() in prompt_lower:
                score += 2

        # スタイルマッチング
        if style and sample["style"] == style:
            score += 3

        # サンプル名マッチング
        if sample["name"].lower() in prompt_lower:
            score += 5

        if score > best_score:
            best_score = score
            best_match = key

    # スコアが低い場合はランダム選択
    if best_score < 2:
        return random.choice(list(DEMO_SAMPLES.keys()))

    return best_match


def generate_placeholder_svg(prompt: str, width: int = 512, height: int = 512) -> str:
    """
    プレースホルダーSVG画像を生成

    Args:
        prompt: プロンプト（ハッシュに使用）
        width: 幅
        height: 高さ

    Returns:
        SVGデータのBase64エンコード
    """
    # プロンプトからハッシュを生成して色を決定
    hash_val = hashlib.md5(prompt.encode()).hexdigest()
    color1 = f"#{hash_val[:6]}"
    color2 = f"#{hash_val[6:12]}"

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{color1};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{color2};stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#grad)"/>
  <text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle"
        font-family="Arial, sans-serif" font-size="18" fill="white" opacity="0.9">
    VisionCraftAI Demo
  </text>
  <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle"
        font-family="Arial, sans-serif" font-size="12" fill="white" opacity="0.7">
    {prompt[:40]}{'...' if len(prompt) > 40 else ''}
  </text>
</svg>"""
    return base64.b64encode(svg.encode()).decode()


@router.get(
    "/samples",
    response_model=DemoSamplesResponse,
    summary="デモサンプル一覧",
    description="利用可能なデモサンプルの一覧を取得します。",
)
async def get_demo_samples() -> DemoSamplesResponse:
    """
    デモサンプル一覧取得

    デモモードで利用可能なサンプル画像の一覧を返します。
    """
    samples = [
        {
            "id": key,
            "name": sample["name"],
            "description": sample["description"],
            "style": sample["style"],
            "keywords": sample["keywords"],
        }
        for key, sample in DEMO_SAMPLES.items()
    ]

    return DemoSamplesResponse(
        samples=samples,
        total_count=len(samples),
    )


@router.post(
    "/generate",
    response_model=DemoGenerateResponse,
    summary="デモ画像生成",
    description="デモモードで擬似的な画像生成を行います。APIキーなしで利用可能です。",
)
async def demo_generate(request: DemoGenerateRequest) -> DemoGenerateResponse:
    """
    デモ画像生成

    - 入力プロンプトに基づいてサンプル画像を選択
    - 実際のAI生成は行わず、デモ用の応答を返す
    - ユーザーにサービスの体験機会を提供
    """
    start_time = datetime.now()

    # 入力検証
    if not request.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "EMPTY_PROMPT", "message": "プロンプトを入力してください"},
        )

    # マッチするサンプルを検索
    matched_key = find_matching_sample(request.prompt, request.style)
    matched_sample = DEMO_SAMPLES.get(matched_key)

    # 擬似生成時間（リアリティのため）
    generation_time_ms = random.randint(500, 2000)

    # プレースホルダーSVGを生成
    placeholder_svg = generate_placeholder_svg(request.prompt)

    elapsed = int((datetime.now() - start_time).total_seconds() * 1000) + generation_time_ms

    return DemoGenerateResponse(
        success=True,
        demo_mode=True,
        prompt=request.prompt,
        matched_sample=matched_sample["name"] if matched_sample else None,
        sample_info={
            "id": matched_key,
            "description": matched_sample["description"],
            "style": matched_sample["style"],
        } if matched_sample else None,
        image_url=f"data:image/svg+xml;base64,{placeholder_svg}",
        message="これはデモモードです。本番環境では、プロンプトに完全に対応した高品質なAI画像を生成できます。",
        generation_time_ms=elapsed,
    )


@router.get(
    "/info",
    summary="デモモード情報",
    description="デモモードの情報と制限事項を取得します。",
)
async def get_demo_info() -> dict:
    """
    デモモード情報

    デモモードの説明、制限事項、アップグレード情報を返します。
    """
    return {
        "demo_mode": True,
        "description": "VisionCraftAI のデモモードです。APIキーなしでサービスを体験できます。",
        "limitations": [
            "実際のAI画像生成は行われません",
            "プレースホルダー画像が表示されます",
            "商用利用はできません",
        ],
        "features_available": [
            "プロンプト入力体験",
            "UIインターフェースの確認",
            "API構造の理解",
        ],
        "upgrade_benefits": [
            "プロンプトに完全対応した高品質AI画像生成",
            "最大4096x4096の高解像度出力",
            "多様なスタイルとカスタマイズオプション",
            "バッチ処理（複数画像の一括生成）",
            "APIアクセスによる自動化",
            "商用利用ライセンス",
        ],
        "pricing": {
            "free": {"price": 0, "generations": 5, "description": "月5生成まで無料"},
            "basic": {"price": 9.99, "generations": 100, "description": "$9.99/月で100枚"},
            "pro": {"price": 29.99, "generations": 500, "description": "$29.99/月で500枚"},
            "enterprise": {"price": None, "generations": "unlimited", "description": "要見積"},
        },
        "get_started_url": "/#pricing",
        "docs_url": "/docs",
    }
