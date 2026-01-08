# -*- coding: utf-8 -*-
"""
VisionCraftAI - APIスキーマ定義

Pydanticベースのリクエストおよびレスポンススキーマを定義します。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class GenerateRequest(BaseModel):
    """画像生成リクエスト"""
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="画像生成プロンプト",
        examples=["A beautiful sunset over mountains"],
    )
    style: Optional[str] = Field(
        None,
        description="スタイル (photorealistic, anime, watercolor, oil_painting, digital_art, sketch)",
        examples=["photorealistic"],
    )
    quality_boost: bool = Field(
        True,
        description="品質向上キーワードを自動追加",
    )
    width: Optional[int] = Field(
        None,
        ge=64,
        le=4096,
        description="画像幅（64-4096）",
    )
    height: Optional[int] = Field(
        None,
        ge=64,
        le=4096,
        description="画像高さ（64-4096）",
    )

    @field_validator("style")
    @classmethod
    def validate_style(cls, v: Optional[str]) -> Optional[str]:
        """スタイルを検証"""
        valid_styles = {
            "photorealistic", "anime", "watercolor",
            "oil_painting", "digital_art", "sketch"
        }
        if v is not None and v.lower() not in valid_styles:
            raise ValueError(f"無効なスタイル: {v}。有効値: {valid_styles}")
        return v.lower() if v else None


class GenerateResponse(BaseModel):
    """画像生成レスポンス"""
    success: bool = Field(..., description="生成成功かどうか")
    image_url: Optional[str] = Field(None, description="生成画像のURL")
    image_base64: Optional[str] = Field(None, description="Base64エンコードされた画像データ")
    prompt: str = Field(..., description="使用されたプロンプト")
    enhanced_prompt: Optional[str] = Field(None, description="拡張後のプロンプト")
    generation_time_ms: int = Field(..., description="生成時間（ミリ秒）")
    model_used: str = Field(..., description="使用されたモデル名")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    warnings: list[str] = Field(default_factory=list, description="警告メッセージリスト")
    suggestions: list[str] = Field(default_factory=list, description="プロンプト改善提案")


class BatchPromptItem(BaseModel):
    """バッチ処理の個別プロンプト"""
    prompt: str = Field(..., min_length=1, max_length=2000)
    style: Optional[str] = None
    quality_boost: bool = True


class BatchRequest(BaseModel):
    """バッチ処理リクエスト"""
    prompts: list[BatchPromptItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="プロンプトリスト（最大100件）",
    )
    job_id: Optional[str] = Field(
        None,
        description="ジョブID（省略時は自動生成）",
    )
    stop_on_error: bool = Field(
        False,
        description="エラー時に停止するか",
    )


class BatchItemResult(BaseModel):
    """バッチ処理の個別結果"""
    index: int
    success: bool
    prompt: str
    image_url: Optional[str] = None
    error_message: Optional[str] = None
    generation_time_ms: int = 0


class BatchResponse(BaseModel):
    """バッチ処理レスポンス"""
    job_id: str = Field(..., description="ジョブID")
    total_count: int = Field(..., description="総リクエスト数")
    success_count: int = Field(..., description="成功数")
    failure_count: int = Field(..., description="失敗数")
    success_rate: float = Field(..., description="成功率（%）")
    total_time_ms: int = Field(..., description="総処理時間（ミリ秒）")
    average_time_ms: float = Field(..., description="平均処理時間（ミリ秒）")
    results: list[BatchItemResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class UsageResponse(BaseModel):
    """使用量レスポンス"""
    period_start: str = Field(..., description="集計期間開始")
    period_end: str = Field(..., description="集計期間終了")
    total_requests: int = Field(..., description="総リクエスト数")
    successful_requests: int = Field(..., description="成功リクエスト数")
    failed_requests: int = Field(..., description="失敗リクエスト数")
    success_rate: float = Field(..., description="成功率（%）")
    total_generation_time_ms: int = Field(..., description="総生成時間")
    average_generation_time_ms: float = Field(..., description="平均生成時間")
    total_estimated_cost_usd: float = Field(..., description="推定総コスト（USD）")
    operations_breakdown: dict[str, int] = Field(default_factory=dict)


class DailyUsage(BaseModel):
    """日別使用量"""
    date: str
    requests: int
    successful: int
    failed: int
    total_time_ms: int
    estimated_cost_usd: float


class DailyUsageResponse(BaseModel):
    """日別使用量レスポンス"""
    days: int = Field(..., description="集計日数")
    daily_data: list[DailyUsage] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str = Field(..., description="サービス状態")
    version: str = Field(..., description="APIバージョン")
    timestamp: str = Field(..., description="レスポンス時刻")
    api_connection: Optional[bool] = Field(None, description="API接続状態")
    api_message: Optional[str] = Field(None, description="API接続メッセージ")


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーメッセージ")
    detail: Optional[str] = Field(None, description="詳細情報")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="エラー発生時刻",
    )


class EstimateRequest(BaseModel):
    """処理時間見積もりリクエスト"""
    prompt_count: int = Field(..., ge=1, le=1000, description="プロンプト数")


class EstimateResponse(BaseModel):
    """処理時間見積もりレスポンス"""
    prompt_count: int
    rate_limit_time_seconds: float
    estimated_generation_seconds: float
    total_estimated_seconds: float
    total_estimated_minutes: float
