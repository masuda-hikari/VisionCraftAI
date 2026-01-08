# -*- coding: utf-8 -*-
"""
VisionCraftAI - FastAPIアプリケーション

メインのFastAPIアプリケーションを定義します。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router
from src.api.auth.routes import router as auth_router
from src.utils.config import Config

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    logger.info("VisionCraftAI API サーバー起動中...")
    config = Config.from_env()
    is_valid, errors = config.validate()

    if not is_valid:
        logger.warning(f"設定に問題があります: {errors}")
    else:
        logger.info("設定検証完了")

    yield

    # 終了時
    logger.info("VisionCraftAI API サーバー終了")


# FastAPIアプリケーション初期化
app = FastAPI(
    title="VisionCraftAI API",
    description="""
    ## AI画像生成プラットフォーム API

    Google Gemini モデルを活用した高品質AI画像生成サービス。

    ### 主な機能
    - **画像生成**: プロンプトから高品質な画像を生成
    - **バッチ処理**: 複数のプロンプトを一括処理
    - **使用量管理**: API使用量とコストを追跡

    ### 認証
    X-API-Key ヘッダーまたは Authorization: Bearer でAPIキーを送信してください。

    ### プラン
    - **Free**: 月5生成、512x512まで
    - **Basic**: 月100枚、1024x1024まで ($9.99/月)
    - **Pro**: 月500枚、2048x2048まで、優先処理 ($29.99/月)
    - **Enterprise**: 無制限、4096x4096まで (要見積)

    ### レート制限
    - 1分あたり60リクエスト
    - バッチ処理では自動的にレート制限を管理
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS設定（開発用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# グローバル例外ハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """グローバル例外ハンドラー"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "内部エラーが発生しました",
            "detail": str(exc) if Config.from_env().debug else None,
        },
    )


# ルーター登録
app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


# ルートエンドポイント
@app.get("/", tags=["Root"])
async def root():
    """
    ルートエンドポイント

    API情報を返します。
    """
    return {
        "name": "VisionCraftAI API",
        "version": "0.1.0",
        "description": "AI画像生成プラットフォーム",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    開発サーバーを起動

    Args:
        host: ホスト名
        port: ポート番号
        reload: ホットリロード有効化
    """
    import uvicorn
    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    run_server(reload=True)
