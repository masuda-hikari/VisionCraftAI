# -*- coding: utf-8 -*-
"""
VisionCraftAI - APIルーター

FastAPIのエンドポイントを定義します。
収益化の中核となるRESTful API実装。
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse

from src.api.schemas import (
    GenerateRequest,
    GenerateResponse,
    BatchRequest,
    BatchResponse,
    BatchItemResult,
    UsageResponse,
    DailyUsageResponse,
    DailyUsage,
    HealthResponse,
    ErrorResponse,
    EstimateRequest,
    EstimateResponse,
)
from src.api.auth.models import APIKey, APIKeyTier
from src.api.auth.dependencies import (
    get_api_key,
    get_optional_api_key,
    check_rate_limit,
    check_quota,
    QuotaEnforcer,
)
from src.api.auth.key_manager import get_key_manager, APIKeyManager
from src.generator.gemini_client import GeminiClient
from src.generator.prompt_handler import PromptHandler
from src.generator.batch_processor import BatchProcessor, BatchJob
from src.utils.config import Config
from src.utils.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)

# ルーター初期化
router = APIRouter()

# シングルトンインスタンス（アプリ起動時に初期化）
_config: Optional[Config] = None
_client: Optional[GeminiClient] = None
_prompt_handler: Optional[PromptHandler] = None
_batch_processor: Optional[BatchProcessor] = None
_usage_tracker: Optional[UsageTracker] = None


def get_config() -> Config:
    """設定を取得"""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def get_client() -> GeminiClient:
    """Geminiクライアントを取得"""
    global _client
    if _client is None:
        _client = GeminiClient(get_config())
    return _client


def get_prompt_handler() -> PromptHandler:
    """プロンプトハンドラーを取得"""
    global _prompt_handler
    if _prompt_handler is None:
        _prompt_handler = PromptHandler()
    return _prompt_handler


def get_batch_processor() -> BatchProcessor:
    """バッチプロセッサを取得"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor(get_client(), get_config())
    return _batch_processor


def get_usage_tracker() -> UsageTracker:
    """使用量トラッカーを取得"""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker()
    return _usage_tracker


# =====================
# ヘルスチェック
# =====================

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="ヘルスチェック",
    description="サービスの状態を確認します。",
)
async def health_check(
    check_api: bool = Query(False, description="API接続確認を行うか"),
) -> HealthResponse:
    """
    サービスヘルスチェック

    - check_api=True の場合、Gemini APIへの接続確認も行います
    """
    response = HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.now().isoformat(),
    )

    if check_api:
        try:
            client = get_client()
            connected, message = client.check_connection()
            response.api_connection = connected
            response.api_message = message
        except Exception as e:
            response.api_connection = False
            response.api_message = str(e)

    return response


# =====================
# 画像生成
# =====================

@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "リクエストエラー"},
        401: {"model": ErrorResponse, "description": "認証エラー"},
        429: {"model": ErrorResponse, "description": "レート制限/クォータ超過"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
    tags=["Generation"],
    summary="画像生成",
    description="プロンプトから画像を生成します。APIキー認証が必要です。",
)
async def generate_image(
    request: GenerateRequest,
    api_key: APIKey = Depends(get_api_key),
    rate_limit_status: dict = Depends(check_rate_limit),
    quota_status: dict = Depends(check_quota),
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> GenerateResponse:
    """
    プロンプトから画像を生成

    - プロンプトは安全性フィルタリングを通過する必要があります
    - スタイルと品質向上オプションが利用可能です
    - 解像度はプランの制限に従います
    """
    handler = get_prompt_handler()
    client = get_client()
    tracker = get_usage_tracker()

    # 解像度制限チェック
    max_width = api_key.quota.max_width
    max_height = api_key.quota.max_height
    if request.width and request.width > max_width:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="RESOLUTION_EXCEEDED",
                message=f"幅が制限を超えています（最大: {max_width}px）",
            ).model_dump(),
        )
    if request.height and request.height > max_height:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="RESOLUTION_EXCEEDED",
                message=f"高さが制限を超えています（最大: {max_height}px）",
            ).model_dump(),
        )

    # プロンプト検証
    validation = handler.validate_and_sanitize(request.prompt)
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="INVALID_PROMPT",
                message=validation.blocked_reason or "無効なプロンプト",
            ).model_dump(),
        )

    # プロンプト拡張
    enhanced_prompt = handler.enhance_prompt(
        validation.sanitized_prompt,
        style=request.style,
        quality_boost=request.quality_boost,
    )

    # 改善提案を取得
    suggestions = handler.suggest_improvements(request.prompt)

    try:
        # 画像生成
        result = client.generate_image(
            prompt=enhanced_prompt,
            width=request.width,
            height=request.height,
        )

        # 使用量記録
        tracker.record(
            operation="generate_image",
            prompt_length=len(enhanced_prompt),
            success=result.success,
            generation_time_ms=result.generation_time_ms,
            model=result.model_used,
            error_message=result.error_message,
        )

        # クォータ消費（成功時のみ）
        if result.success:
            key_manager.record_usage(api_key.key_id, 1)

        if result.success:
            # 画像データをBase64エンコード
            image_base64 = None
            if result.image_data:
                image_base64 = base64.b64encode(result.image_data).decode("utf-8")

            return GenerateResponse(
                success=True,
                image_url=result.file_path,
                image_base64=image_base64,
                prompt=request.prompt,
                enhanced_prompt=enhanced_prompt,
                generation_time_ms=result.generation_time_ms,
                model_used=result.model_used,
                warnings=validation.warnings,
                suggestions=suggestions,
            )
        else:
            return GenerateResponse(
                success=False,
                prompt=request.prompt,
                enhanced_prompt=enhanced_prompt,
                generation_time_ms=result.generation_time_ms,
                model_used=result.model_used,
                error_message=result.error_message,
                warnings=validation.warnings,
                suggestions=suggestions,
            )

    except Exception as e:
        logger.error(f"画像生成エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="GENERATION_ERROR",
                message="画像生成中にエラーが発生しました",
                detail=str(e),
            ).model_dump(),
        )


# =====================
# バッチ処理
# =====================

@router.post(
    "/batch/generate",
    response_model=BatchResponse,
    responses={
        400: {"model": ErrorResponse, "description": "リクエストエラー"},
        401: {"model": ErrorResponse, "description": "認証エラー"},
        429: {"model": ErrorResponse, "description": "レート制限/クォータ超過"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
    tags=["Batch"],
    summary="バッチ画像生成",
    description="複数のプロンプトから画像を一括生成します。APIキー認証が必要です。",
)
async def batch_generate(
    request: BatchRequest,
    api_key: APIKey = Depends(get_api_key),
    rate_limit_status: dict = Depends(check_rate_limit),
    key_manager: APIKeyManager = Depends(get_key_manager),
) -> BatchResponse:
    """
    バッチ画像生成

    - 最大100件のプロンプトを一括処理
    - レート制限を自動管理
    - 処理進捗を追跡
    - プランに応じたバッチサイズ制限あり
    """
    handler = get_prompt_handler()
    processor = get_batch_processor()
    tracker = get_usage_tracker()

    # バッチサイズ制限チェック
    max_batch_size = api_key.quota.max_batch_size
    if len(request.prompts) > max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="BATCH_SIZE_EXCEEDED",
                message=f"バッチサイズが制限を超えています（最大: {max_batch_size}件）",
            ).model_dump(),
        )

    # クォータ事前チェック
    can_generate, reason = api_key.quota.can_generate(len(request.prompts))
    if not can_generate:
        raise HTTPException(
            status_code=429,
            detail=ErrorResponse(
                error="QUOTA_EXCEEDED",
                message=reason,
            ).model_dump(),
        )

    # プロンプトの検証と拡張
    processed_prompts: list[str] = []
    errors: list[str] = []

    for idx, item in enumerate(request.prompts):
        validation = handler.validate_and_sanitize(item.prompt)
        if not validation.is_valid:
            errors.append(f"[{idx}] {validation.blocked_reason}")
            continue

        enhanced = handler.enhance_prompt(
            validation.sanitized_prompt,
            style=item.style,
            quality_boost=item.quality_boost,
        )
        processed_prompts.append(enhanced)

    if not processed_prompts:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="ALL_PROMPTS_INVALID",
                message="すべてのプロンプトが無効です",
                detail="; ".join(errors),
            ).model_dump(),
        )

    try:
        # バッチジョブ作成
        job = BatchJob(
            job_id=request.job_id or "",
            prompts=processed_prompts,
        )

        # バッチ処理実行
        batch_result = processor.process_batch(
            job=job,
            stop_on_error=request.stop_on_error,
        )

        # 個別結果を変換
        item_results: list[BatchItemResult] = []
        for idx, result in enumerate(batch_result.results):
            item_results.append(BatchItemResult(
                index=idx,
                success=result.success,
                prompt=result.prompt,
                image_url=result.file_path,
                error_message=result.error_message,
                generation_time_ms=result.generation_time_ms,
            ))

            # 使用量記録
            tracker.record(
                operation="generate_image",
                prompt_length=len(result.prompt),
                success=result.success,
                generation_time_ms=result.generation_time_ms,
                model=result.model_used,
                error_message=result.error_message,
            )

        # クォータ消費（成功数分）
        if batch_result.success_count > 0:
            key_manager.record_usage(api_key.key_id, batch_result.success_count)

        return BatchResponse(
            job_id=batch_result.job_id,
            total_count=batch_result.total_count,
            success_count=batch_result.success_count,
            failure_count=batch_result.failure_count,
            success_rate=batch_result.success_rate,
            total_time_ms=batch_result.total_time_ms,
            average_time_ms=batch_result.average_time_ms,
            results=item_results,
            errors=batch_result.errors + errors,
        )

    except Exception as e:
        logger.error(f"バッチ処理エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="BATCH_ERROR",
                message="バッチ処理中にエラーが発生しました",
                detail=str(e),
            ).model_dump(),
        )


@router.post(
    "/batch/estimate",
    response_model=EstimateResponse,
    tags=["Batch"],
    summary="処理時間見積もり",
    description="バッチ処理の所要時間を見積もります。",
)
async def estimate_batch_time(request: EstimateRequest) -> EstimateResponse:
    """
    処理時間見積もり

    - レート制限に基づく最小時間
    - 平均生成時間に基づく見積もり
    """
    processor = get_batch_processor()
    estimate = processor.estimate_time(request.prompt_count)

    return EstimateResponse(
        prompt_count=estimate["prompt_count"],
        rate_limit_time_seconds=estimate["rate_limit_time_seconds"],
        estimated_generation_seconds=estimate["estimated_generation_seconds"],
        total_estimated_seconds=estimate["total_estimated_seconds"],
        total_estimated_minutes=estimate["total_estimated_minutes"],
    )


# =====================
# 使用量・コスト管理
# =====================

@router.get(
    "/usage",
    response_model=UsageResponse,
    tags=["Usage"],
    summary="使用量サマリー",
    description="API使用量のサマリーを取得します。",
)
async def get_usage_summary(
    days: Optional[int] = Query(None, ge=1, le=365, description="過去N日間"),
) -> UsageResponse:
    """
    使用量サマリー取得

    - 全期間または指定期間の使用量を集計
    - コスト見積もりを含む
    """
    tracker = get_usage_tracker()
    summary = tracker.get_summary(days=days)

    return UsageResponse(
        period_start=summary.period_start,
        period_end=summary.period_end,
        total_requests=summary.total_requests,
        successful_requests=summary.successful_requests,
        failed_requests=summary.failed_requests,
        success_rate=summary.success_rate,
        total_generation_time_ms=summary.total_generation_time_ms,
        average_generation_time_ms=summary.average_generation_time_ms,
        total_estimated_cost_usd=summary.total_estimated_cost_usd,
        operations_breakdown=summary.operations_breakdown,
    )


@router.get(
    "/usage/daily",
    response_model=DailyUsageResponse,
    tags=["Usage"],
    summary="日別使用量",
    description="日別のAPI使用量を取得します。",
)
async def get_daily_usage(
    days: int = Query(30, ge=1, le=365, description="過去N日間"),
) -> DailyUsageResponse:
    """
    日別使用量取得

    - 指定期間の日別使用量を取得
    - グラフ表示やレポート作成に有用
    """
    tracker = get_usage_tracker()
    daily_data = tracker.get_daily_breakdown(days=days)

    return DailyUsageResponse(
        days=days,
        daily_data=[
            DailyUsage(
                date=d["date"],
                requests=d["requests"],
                successful=d["successful"],
                failed=d["failed"],
                total_time_ms=d["total_time_ms"],
                estimated_cost_usd=d["estimated_cost_usd"],
            )
            for d in daily_data
        ],
    )


@router.post(
    "/usage/export",
    tags=["Usage"],
    summary="レポートエクスポート",
    description="使用量レポートをJSONファイルとしてエクスポートします。",
)
async def export_usage_report(
    days: int = Query(30, ge=1, le=365, description="過去N日間"),
) -> dict:
    """
    使用量レポートエクスポート

    - JSON形式でレポートを出力
    - 経理・分析用途に有用
    """
    tracker = get_usage_tracker()
    output_path = tracker.export_report(days=days)

    return {
        "success": True,
        "message": "レポートをエクスポートしました",
        "file_path": str(output_path),
    }


# =====================
# プロンプト関連
# =====================

@router.post(
    "/prompt/validate",
    tags=["Prompt"],
    summary="プロンプト検証",
    description="プロンプトの安全性を検証します。",
)
async def validate_prompt(prompt: str = Query(..., min_length=1, max_length=2000)) -> dict:
    """
    プロンプト検証

    - 禁止キーワードチェック
    - 警告キーワードチェック
    - 改善提案
    """
    handler = get_prompt_handler()
    validation = handler.validate_and_sanitize(prompt)
    suggestions = handler.suggest_improvements(prompt)

    return {
        "is_valid": validation.is_valid,
        "sanitized_prompt": validation.sanitized_prompt,
        "blocked_reason": validation.blocked_reason,
        "warnings": validation.warnings,
        "suggestions": suggestions,
    }


@router.post(
    "/prompt/enhance",
    tags=["Prompt"],
    summary="プロンプト拡張",
    description="プロンプトを品質向上のために拡張します。",
)
async def enhance_prompt(
    prompt: str = Query(..., min_length=1, max_length=2000),
    style: Optional[str] = Query(None),
    quality_boost: bool = Query(True),
) -> dict:
    """
    プロンプト拡張

    - スタイル適用
    - 品質向上キーワード追加
    """
    handler = get_prompt_handler()
    enhanced = handler.enhance_prompt(
        prompt=prompt,
        style=style,
        quality_boost=quality_boost,
    )

    return {
        "original_prompt": prompt,
        "enhanced_prompt": enhanced,
        "style_applied": style,
        "quality_boost": quality_boost,
    }
