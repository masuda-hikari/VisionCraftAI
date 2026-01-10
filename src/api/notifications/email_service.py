# -*- coding: utf-8 -*-
"""
VisionCraftAI - メール送信サービス

SMTP経由でメールを送信するサービス。
本番環境ではSendGrid、AWS SES、Resend等のサービスに切り替え可能。
"""

import logging
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """メール送信設定"""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    use_tls: bool = True
    use_ssl: bool = False

    # 送信元設定
    from_email: str = ""
    from_name: str = "VisionCraftAI"

    # 送信モード
    enabled: bool = True  # False = ログ出力のみ（開発用）

    @classmethod
    def from_env(cls) -> "EmailConfig":
        """環境変数から設定を読み込む"""
        return cls(
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            use_ssl=os.getenv("SMTP_USE_SSL", "false").lower() == "true",
            from_email=os.getenv("EMAIL_FROM", "noreply@visioncraft.ai"),
            from_name=os.getenv("EMAIL_FROM_NAME", "VisionCraftAI"),
            enabled=os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        )


class EmailService:
    """メール送信サービス"""

    def __init__(self, config: EmailConfig | None = None):
        """
        初期化

        Args:
            config: メール設定（省略時は環境変数から読み込み）
        """
        self.config = config or EmailConfig.from_env()

    def is_configured(self) -> bool:
        """SMTP設定が完了しているかチェック"""
        return bool(
            self.config.smtp_host
            and self.config.smtp_user
            and self.config.smtp_password
            and self.config.from_email
        )

    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
        reply_to: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None]:
        """
        メールを送信

        Args:
            to_email: 送信先メールアドレス
            subject: 件名
            html_body: HTML本文
            text_body: テキスト本文（省略時はHTMLから生成）
            reply_to: 返信先アドレス
            metadata: 追跡用メタデータ

        Returns:
            tuple[bool, str | None]: (成功/失敗, エラーメッセージ)
        """
        if not self.config.enabled:
            # 開発モード: ログ出力のみ
            logger.info(
                f"[EMAIL DEV MODE] To: {to_email}, Subject: {subject}"
            )
            return True, None

        if not self.is_configured():
            logger.warning("Email service not configured, skipping send")
            return False, "Email service not configured"

        try:
            # メッセージ作成
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            msg["To"] = to_email

            if reply_to:
                msg["Reply-To"] = reply_to

            # テキスト本文
            if text_body:
                msg.attach(MIMEText(text_body, "plain", "utf-8"))

            # HTML本文
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            # SMTP送信
            await self._send_smtp(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True, None

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {e}"
            logger.error(error_msg)
            return False, error_msg

        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"Recipient refused: {e}"
            logger.error(error_msg)
            return False, error_msg

        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {e}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Failed to send email: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    async def _send_smtp(self, msg: MIMEMultipart) -> None:
        """SMTPでメール送信（同期処理をラップ）"""
        # 本番では非同期ライブラリ（aiosmtplib）を使用推奨
        import asyncio

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._send_smtp_sync, msg)

    def _send_smtp_sync(self, msg: MIMEMultipart) -> None:
        """同期SMTP送信"""
        context = ssl.create_default_context()

        if self.config.use_ssl:
            # SSL接続
            with smtplib.SMTP_SSL(
                self.config.smtp_host,
                self.config.smtp_port,
                context=context,
            ) as server:
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)
        else:
            # TLS接続
            with smtplib.SMTP(
                self.config.smtp_host,
                self.config.smtp_port,
            ) as server:
                if self.config.use_tls:
                    server.starttls(context=context)
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.send_message(msg)

    async def send_batch(
        self,
        recipients: list[tuple[str, str, str, str | None]],
    ) -> list[tuple[str, bool, str | None]]:
        """
        バッチメール送信

        Args:
            recipients: [(to_email, subject, html_body, text_body), ...]

        Returns:
            list[tuple[str, bool, str | None]]: [(to_email, success, error), ...]
        """
        results = []

        for to_email, subject, html_body, text_body in recipients:
            success, error = await self.send(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
            results.append((to_email, success, error))

        return results

    def test_connection(self) -> tuple[bool, str | None]:
        """
        SMTP接続テスト

        Returns:
            tuple[bool, str | None]: (成功/失敗, エラーメッセージ)
        """
        if not self.is_configured():
            return False, "Email service not configured"

        try:
            context = ssl.create_default_context()

            if self.config.use_ssl:
                with smtplib.SMTP_SSL(
                    self.config.smtp_host,
                    self.config.smtp_port,
                    context=context,
                ) as server:
                    server.login(self.config.smtp_user, self.config.smtp_password)
                    server.noop()
            else:
                with smtplib.SMTP(
                    self.config.smtp_host,
                    self.config.smtp_port,
                ) as server:
                    if self.config.use_tls:
                        server.starttls(context=context)
                    server.login(self.config.smtp_user, self.config.smtp_password)
                    server.noop()

            return True, None

        except Exception as e:
            return False, str(e)
