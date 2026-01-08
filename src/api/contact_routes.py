# -*- coding: utf-8 -*-
"""
VisionCraftAI - お問い合わせAPIルート

お問い合わせフォームのAPIエンドポイントを提供します。
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["Contact"])

# お問い合わせデータ保存ディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONTACTS_DIR = BASE_DIR / "data" / "contacts"


class ContactRequest(BaseModel):
    """お問い合わせリクエストスキーマ"""

    name: str = Field(..., min_length=1, max_length=100, description="お名前")
    email: EmailStr = Field(..., description="メールアドレス")
    company: Optional[str] = Field(None, max_length=200, description="会社名")
    category: str = Field(
        ...,
        description="お問い合わせ種別",
    )
    subject: str = Field(..., min_length=1, max_length=200, description="件名")
    message: str = Field(..., min_length=10, max_length=5000, description="お問い合わせ内容")
    api_key: Optional[str] = Field(None, max_length=100, description="APIキー（任意）")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """カテゴリのバリデーション"""
        valid_categories = [
            "general",
            "technical",
            "billing",
            "enterprise",
            "partnership",
            "bug",
            "feature",
            "other",
        ]
        if v not in valid_categories:
            raise ValueError(f"無効なカテゴリです。有効な値: {', '.join(valid_categories)}")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """メッセージのバリデーション（スパム対策）"""
        # 過度なURL検出
        url_count = len(re.findall(r"https?://", v))
        if url_count > 5:
            raise ValueError("メッセージ内のURLが多すぎます")
        return v


class ContactResponse(BaseModel):
    """お問い合わせレスポンススキーマ"""

    success: bool = True
    message: str = "お問い合わせを受け付けました"
    ticket_id: str = Field(..., description="チケットID")


@router.post(
    "",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="お問い合わせ送信",
    description="お問い合わせフォームからの送信を受け付けます",
)
async def submit_contact(contact: ContactRequest) -> ContactResponse:
    """
    お問い合わせを受け付けて保存

    Args:
        contact: お問い合わせ内容

    Returns:
        ContactResponse: 受付確認
    """
    # チケットID生成
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    ticket_id = f"VCA-{timestamp}-{hash(contact.email) % 10000:04d}"

    # データ保存
    try:
        CONTACTS_DIR.mkdir(parents=True, exist_ok=True)

        contact_data = {
            "ticket_id": ticket_id,
            "timestamp": datetime.now().isoformat(),
            "name": contact.name,
            "email": contact.email,
            "company": contact.company,
            "category": contact.category,
            "subject": contact.subject,
            "message": contact.message,
            "api_key_provided": bool(contact.api_key),
            "status": "new",
        }

        # JSONファイルとして保存
        import json

        contact_file = CONTACTS_DIR / f"{ticket_id}.json"
        with open(contact_file, "w", encoding="utf-8") as f:
            json.dump(contact_data, f, ensure_ascii=False, indent=2)

        logger.info(f"お問い合わせ受付: {ticket_id} - {contact.category} - {contact.email}")

    except Exception as e:
        logger.error(f"お問い合わせ保存エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="お問い合わせの保存に失敗しました",
        )

    return ContactResponse(
        success=True,
        message="お問い合わせを受け付けました。2-3営業日以内にご返信いたします。",
        ticket_id=ticket_id,
    )


@router.get(
    "/categories",
    summary="お問い合わせカテゴリ一覧",
    description="利用可能なお問い合わせカテゴリの一覧を返します",
)
async def get_categories():
    """お問い合わせカテゴリ一覧を取得"""
    return {
        "categories": [
            {"id": "general", "label": "一般的なご質問"},
            {"id": "technical", "label": "技術的なご質問"},
            {"id": "billing", "label": "料金・お支払いについて"},
            {"id": "enterprise", "label": "Enterpriseプランのご相談"},
            {"id": "partnership", "label": "パートナーシップ・提携"},
            {"id": "bug", "label": "不具合報告"},
            {"id": "feature", "label": "機能リクエスト"},
            {"id": "other", "label": "その他"},
        ]
    }
