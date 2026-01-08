# -*- coding: utf-8 -*-
"""
VisionCraftAI - 設定管理モジュール

環境変数とアプリケーション設定を管理します。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class GeminiConfig:
    """Gemini API設定"""
    project_id: str = ""
    location: str = "us-central1"
    credentials_path: Optional[str] = None
    model_name: str = "gemini-2.0-flash-exp"  # 画像生成対応モデル

    # レート制限設定
    max_requests_per_minute: int = 60
    max_tokens_per_request: int = 8192


@dataclass
class ImageConfig:
    """画像生成設定"""
    default_width: int = 1024
    default_height: int = 1024
    output_format: str = "png"
    quality: int = 95

    # 出力ディレクトリ
    output_dir: Path = field(default_factory=lambda: Path("outputs"))


@dataclass
class ServerConfig:
    """サーバー設定"""
    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000
    cors_origins: list[str] = field(default_factory=list)  # 空=全許可（開発用）
    trusted_hosts: list[str] = field(default_factory=lambda: ["*"])


@dataclass
class Config:
    """アプリケーション全体設定"""
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    image: ImageConfig = field(default_factory=ImageConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

    # デバッグモード
    debug: bool = False

    # ログ設定
    log_level: str = "INFO"

    # 環境（development, staging, production）
    environment: str = "development"

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """
        環境変数から設定を読み込む

        Args:
            env_file: .envファイルのパス（省略時は自動検索）

        Returns:
            Config: 設定インスタンス
        """
        # .envファイルを読み込む
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Gemini設定
        gemini_config = GeminiConfig(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-exp"),
            max_requests_per_minute=int(os.getenv("GEMINI_MAX_RPM", "60")),
        )

        # 画像設定
        output_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
        image_config = ImageConfig(
            default_width=int(os.getenv("IMAGE_WIDTH", "1024")),
            default_height=int(os.getenv("IMAGE_HEIGHT", "1024")),
            output_format=os.getenv("IMAGE_FORMAT", "png"),
            quality=int(os.getenv("IMAGE_QUALITY", "95")),
            output_dir=output_dir,
        )

        # サーバー設定
        cors_origins_str = os.getenv("CORS_ORIGINS", "")
        cors_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]
        trusted_hosts_str = os.getenv("TRUSTED_HOSTS", "*")
        trusted_hosts = [h.strip() for h in trusted_hosts_str.split(",") if h.strip()]

        server_config = ServerConfig(
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", "8000")),
            cors_origins=cors_origins,
            trusted_hosts=trusted_hosts,
        )

        environment = os.getenv("ENVIRONMENT", "development")

        return cls(
            gemini=gemini_config,
            image=image_config,
            server=server_config,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            environment=environment,
        )

    def validate(self) -> tuple[bool, list[str]]:
        """
        設定の妥当性を検証

        Returns:
            tuple[bool, list[str]]: (有効かどうか, エラーメッセージリスト)
        """
        errors: list[str] = []

        # Gemini設定の検証
        if not self.gemini.project_id:
            errors.append("GOOGLE_CLOUD_PROJECT が設定されていません")

        if self.gemini.credentials_path:
            creds_path = Path(self.gemini.credentials_path)
            if not creds_path.exists():
                errors.append(f"認証ファイルが見つかりません: {self.gemini.credentials_path}")

        # 画像設定の検証
        if self.image.default_width < 64 or self.image.default_width > 4096:
            errors.append(f"画像幅が範囲外です: {self.image.default_width} (64-4096)")

        if self.image.default_height < 64 or self.image.default_height > 4096:
            errors.append(f"画像高さが範囲外です: {self.image.default_height} (64-4096)")

        return len(errors) == 0, errors

    def ensure_output_dir(self) -> Path:
        """
        出力ディレクトリを作成し、パスを返す

        Returns:
            Path: 出力ディレクトリのパス
        """
        self.image.output_dir.mkdir(parents=True, exist_ok=True)
        return self.image.output_dir
