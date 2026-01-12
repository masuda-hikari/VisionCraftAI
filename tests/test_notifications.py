# -*- coding: utf-8 -*-
"""
VisionCraftAI - 通知システムテスト

EmailService, NotificationManager, APIエンドポイントのテスト。
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

from src.api.app import app
from src.api.notifications.models import (
    NotificationPreference,
    NotificationType,
    EmailTemplate,
    EmailLog,
    EmailStatus,
)
from src.api.notifications.email_service import EmailService, EmailConfig
from src.api.notifications.manager import NotificationManager
from src.api.notifications.templates import get_template, get_default_templates


client = TestClient(app)


# --- モデルテスト ---
class TestNotificationModels:
    """通知モデルのテスト"""

    def test_notification_preference_defaults(self):
        """通知設定のデフォルト値テスト"""
        pref = NotificationPreference(
            user_id="user_123",
            email="test@example.com",
        )

        assert pref.marketing_emails is True
        assert pref.transactional_emails is True
        assert pref.usage_alerts is True
        assert pref.weekly_summary is True
        assert pref.monthly_report is False
        assert pref.referral_notifications is True
        assert pref.language == "ja"

    def test_notification_preference_can_receive_transactional(self):
        """トランザクションメール受信可否テスト"""
        pref = NotificationPreference(
            user_id="user_123",
            email="test@example.com",
            transactional_emails=True,
        )

        assert pref.can_receive(NotificationType.WELCOME) is True
        assert pref.can_receive(NotificationType.PAYMENT_SUCCEEDED) is True
        assert pref.can_receive(NotificationType.SUBSCRIPTION_CREATED) is True

    def test_notification_preference_can_receive_usage_alerts(self):
        """使用量アラート受信可否テスト"""
        pref = NotificationPreference(
            user_id="user_123",
            email="test@example.com",
            usage_alerts=True,
        )

        assert pref.can_receive(NotificationType.USAGE_WARNING) is True
        assert pref.can_receive(NotificationType.CREDITS_LOW) is True

        pref.usage_alerts = False
        assert pref.can_receive(NotificationType.USAGE_WARNING) is False

    def test_notification_preference_can_receive_referral(self):
        """紹介通知受信可否テスト"""
        pref = NotificationPreference(
            user_id="user_123",
            email="test@example.com",
            referral_notifications=True,
        )

        assert pref.can_receive(NotificationType.REFERRAL_REWARD) is True

        pref.referral_notifications = False
        assert pref.can_receive(NotificationType.REFERRAL_REWARD) is False

    def test_notification_preference_can_receive_weekly_summary(self):
        """週次サマリー受信可否テスト"""
        pref = NotificationPreference(
            user_id="user_123",
            email="test@example.com",
            weekly_summary=True,
        )

        assert pref.can_receive(NotificationType.WEEKLY_SUMMARY) is True

        pref.weekly_summary = False
        assert pref.can_receive(NotificationType.WEEKLY_SUMMARY) is False

    def test_email_template_render(self):
        """テンプレートレンダリングテスト"""
        template = EmailTemplate(
            template_id="test_template",
            notification_type=NotificationType.WELCOME,
            subject="Hello, {{user_name}}!",
            html_body="<p>Welcome, {{user_name}}!</p>",
            text_body="Welcome, {{user_name}}!",
        )

        subject, html, text = template.render({"user_name": "John"})

        assert subject == "Hello, John!"
        assert html == "<p>Welcome, John!</p>"
        assert text == "Welcome, John!"

    def test_email_log_state_transitions(self):
        """メールログ状態遷移テスト"""
        log = EmailLog(
            log_id="log_123",
            user_id="user_123",
            email="test@example.com",
            notification_type=NotificationType.WELCOME,
            subject="Welcome",
            template_id="welcome_ja",
        )

        assert log.status == EmailStatus.PENDING

        log.mark_sent()
        assert log.status == EmailStatus.SENT
        assert log.sent_at is not None

        log.mark_opened()
        assert log.status == EmailStatus.OPENED
        assert log.opened_at is not None

        log.mark_clicked()
        assert log.status == EmailStatus.CLICKED
        assert log.clicked_at is not None

    def test_email_log_mark_failed(self):
        """メールログ失敗マークテスト"""
        log = EmailLog(
            log_id="log_123",
            user_id="user_123",
            email="test@example.com",
            notification_type=NotificationType.WELCOME,
            subject="Welcome",
            template_id="welcome_ja",
        )

        log.mark_failed("Connection refused")

        assert log.status == EmailStatus.FAILED
        assert log.error_message == "Connection refused"
        assert log.retry_count == 1


# --- EmailServiceテスト ---
class TestEmailService:
    """メール送信サービスのテスト"""

    def test_email_config_from_env(self):
        """環境変数からの設定読み込みテスト"""
        config = EmailConfig.from_env()
        assert config is not None
        assert isinstance(config.smtp_port, int)

    def test_email_service_not_configured(self):
        """未設定時のis_configured判定テスト"""
        config = EmailConfig(
            smtp_host="",
            smtp_user="",
            smtp_password="",
            from_email="",
        )
        service = EmailService(config)

        assert service.is_configured() is False

    def test_email_service_configured(self):
        """設定済み時のis_configured判定テスト"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            from_email="noreply@example.com",
        )
        service = EmailService(config)

        assert service.is_configured() is True

    @pytest.mark.asyncio
    async def test_email_service_dev_mode(self):
        """開発モード送信テスト"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            from_email="noreply@example.com",
            enabled=False,  # 開発モード
        )
        service = EmailService(config)

        success, error = await service.send(
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>",
        )

        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_email_service_not_configured_error(self):
        """未設定時の送信エラーテスト"""
        config = EmailConfig(
            smtp_host="",
            smtp_user="",
            smtp_password="",
            from_email="",
            enabled=True,
        )
        service = EmailService(config)

        success, error = await service.send(
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>",
        )

        assert success is False
        assert "not configured" in error

    @pytest.mark.asyncio
    async def test_email_service_with_text_body(self):
        """テキスト本文付き送信テスト（開発モード）"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            from_email="noreply@example.com",
            enabled=False,  # 開発モード
        )
        service = EmailService(config)

        success, error = await service.send(
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>",
            text_body="Test plain text",
            reply_to="reply@example.com",
            metadata={"key": "value"},
        )

        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_email_service_smtp_auth_error(self):
        """SMTP認証エラーテスト"""
        import smtplib

        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            from_email="noreply@example.com",
            enabled=True,
        )
        service = EmailService(config)

        with patch.object(
            service, '_send_smtp',
            side_effect=smtplib.SMTPAuthenticationError(535, b"Auth failed")
        ):
            success, error = await service.send(
                to_email="test@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

        assert success is False
        assert "authentication" in error.lower()

    @pytest.mark.asyncio
    async def test_email_service_smtp_recipient_refused(self):
        """SMTP受信者拒否エラーテスト"""
        import smtplib

        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            from_email="noreply@example.com",
            enabled=True,
        )
        service = EmailService(config)

        with patch.object(
            service, '_send_smtp',
            side_effect=smtplib.SMTPRecipientsRefused(
                {"test@example.com": (550, b"User unknown")}
            )
        ):
            success, error = await service.send(
                to_email="test@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

        assert success is False
        assert "refused" in error.lower()

    @pytest.mark.asyncio
    async def test_email_service_smtp_exception(self):
        """SMTPエラーテスト"""
        import smtplib

        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            from_email="noreply@example.com",
            enabled=True,
        )
        service = EmailService(config)

        with patch.object(
            service, '_send_smtp',
            side_effect=smtplib.SMTPException("Connection failed")
        ):
            success, error = await service.send(
                to_email="test@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

        assert success is False
        assert "SMTP error" in error

    @pytest.mark.asyncio
    async def test_email_service_general_exception(self):
        """一般的な例外テスト"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            from_email="noreply@example.com",
            enabled=True,
        )
        service = EmailService(config)

        with patch.object(
            service, '_send_smtp',
            side_effect=Exception("Unexpected error")
        ):
            success, error = await service.send(
                to_email="test@example.com",
                subject="Test",
                html_body="<p>Test</p>",
            )

        assert success is False
        assert "Failed to send email" in error

    @pytest.mark.asyncio
    async def test_email_service_batch_send(self):
        """バッチ送信テスト（開発モード）"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="pass",
            from_email="noreply@example.com",
            enabled=False,  # 開発モード
        )
        service = EmailService(config)

        recipients = [
            ("user1@example.com", "Subject 1", "<p>Body 1</p>", "Text 1"),
            ("user2@example.com", "Subject 2", "<p>Body 2</p>", None),
        ]

        results = await service.send_batch(recipients)

        assert len(results) == 2
        assert all(success for _, success, _ in results)

    def test_email_service_connection_test_not_configured(self):
        """接続テスト（未設定）"""
        config = EmailConfig(
            smtp_host="",
            smtp_user="",
            smtp_password="",
            from_email="",
        )
        service = EmailService(config)

        success, error = service.test_connection()

        assert success is False
        assert "not configured" in error

    def test_email_service_connection_test_ssl_error(self):
        """接続テスト（SSL接続エラー）"""
        import smtplib

        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=465,
            smtp_user="user",
            smtp_password="pass",
            from_email="noreply@example.com",
            use_ssl=True,
            use_tls=False,
        )
        service = EmailService(config)

        with patch('smtplib.SMTP_SSL') as mock_smtp:
            mock_smtp.side_effect = Exception("SSL connection failed")

            success, error = service.test_connection()

        assert success is False
        assert "SSL connection failed" in error

    def test_email_service_connection_test_tls_error(self):
        """接続テスト（TLS接続エラー）"""
        import smtplib

        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="pass",
            from_email="noreply@example.com",
            use_ssl=False,
            use_tls=True,
        )
        service = EmailService(config)

        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = Exception("TLS connection failed")

            success, error = service.test_connection()

        assert success is False
        assert "TLS connection failed" in error


# --- NotificationManagerテスト ---
class TestNotificationManager:
    """通知マネージャーのテスト"""

    def test_create_default_preference(self):
        """デフォルト通知設定作成テスト"""
        manager = NotificationManager()

        pref = manager.create_default_preference(
            user_id="user_123",
            email="test@example.com",
        )

        assert pref.user_id == "user_123"
        assert pref.email == "test@example.com"
        assert pref.language == "ja"

    def test_get_preference(self):
        """通知設定取得テスト"""
        manager = NotificationManager()

        # 未作成時はNone
        assert manager.get_preference("user_123") is None

        # 作成後は取得可能
        manager.create_default_preference("user_123", "test@example.com")
        pref = manager.get_preference("user_123")

        assert pref is not None
        assert pref.user_id == "user_123"

    def test_update_preference(self):
        """通知設定更新テスト"""
        manager = NotificationManager()
        manager.create_default_preference("user_123", "test@example.com")

        updated = manager.update_preference(
            "user_123",
            weekly_summary=False,
            language="en",
        )

        assert updated is not None
        assert updated.weekly_summary is False
        assert updated.language == "en"

    def test_update_preference_not_found(self):
        """存在しないユーザーの設定更新テスト"""
        manager = NotificationManager()

        result = manager.update_preference("nonexistent", weekly_summary=False)
        assert result is None

    @pytest.mark.asyncio
    async def test_send_notification_no_preference(self):
        """設定なしユーザーへの通知送信テスト"""
        manager = NotificationManager()

        success, log_id, error = await manager.send_notification(
            user_id="user_123",
            notification_type=NotificationType.WELCOME,
            context={"user_name": "Test"},
        )

        assert success is False
        assert "not found" in error

    @pytest.mark.asyncio
    async def test_send_notification_opted_out(self):
        """オプトアウトユーザーへの通知送信テスト"""
        manager = NotificationManager()
        manager.create_default_preference("user_123", "test@example.com")
        manager.update_preference("user_123", weekly_summary=False)

        success, log_id, error = await manager.send_notification(
            user_id="user_123",
            notification_type=NotificationType.WEEKLY_SUMMARY,
            context={"user_name": "Test"},
        )

        assert success is False
        assert "opted out" in error

    @pytest.mark.asyncio
    async def test_send_notification_force(self):
        """強制送信テスト"""
        manager = NotificationManager()
        manager.create_default_preference("user_123", "test@example.com")
        manager.update_preference("user_123", weekly_summary=False)

        # 強制送信（開発モードなのでSMTPエラーなし）
        success, log_id, error = await manager.send_notification(
            user_id="user_123",
            notification_type=NotificationType.WEEKLY_SUMMARY,
            context={
                "user_name": "Test",
                "images_generated": 10,
                "credits_used": 5,
                "credits_remaining": 15,
                "weekly_highlight": "Great work!",
            },
            force=True,
        )

        assert success is True
        assert log_id is not None

    @pytest.mark.asyncio
    async def test_send_welcome(self):
        """ウェルカムメール送信テスト"""
        manager = NotificationManager()
        manager.create_default_preference("user_123", "test@example.com")

        success, log_id, error = await manager.send_welcome(
            user_id="user_123",
            user_name="Test User",
        )

        assert success is True
        assert log_id is not None

    @pytest.mark.asyncio
    async def test_send_referral_reward(self):
        """紹介報酬メール送信テスト"""
        manager = NotificationManager()
        manager.create_default_preference("user_123", "test@example.com")

        success, log_id, error = await manager.send_referral_reward(
            user_id="user_123",
            user_name="Test User",
            referred_user="Friend",
            reward_credits=5,
            total_referrals=3,
        )

        assert success is True
        assert log_id is not None

    def test_get_user_logs(self):
        """ユーザーログ取得テスト"""
        manager = NotificationManager()

        # ログがない場合は空リスト
        logs = manager.get_user_logs("user_123")
        assert logs == []

    def test_get_stats(self):
        """統計取得テスト"""
        manager = NotificationManager()

        stats = manager.get_stats()

        assert stats["total"] == 0
        assert stats["delivery_rate"] == 0

    def test_mark_opened(self):
        """開封マークテスト"""
        manager = NotificationManager()

        # 存在しないログ
        assert manager.mark_opened("nonexistent") is False

    def test_mark_clicked(self):
        """クリックマークテスト"""
        manager = NotificationManager()

        # 存在しないログ
        assert manager.mark_clicked("nonexistent") is False


# --- テンプレートテスト ---
class TestEmailTemplates:
    """メールテンプレートのテスト"""

    def test_get_default_templates(self):
        """デフォルトテンプレート取得テスト"""
        templates = get_default_templates()

        assert NotificationType.WELCOME.value in templates
        assert NotificationType.TRIAL_STARTED.value in templates
        assert NotificationType.PAYMENT_SUCCEEDED.value in templates

    def test_get_template_ja(self):
        """日本語テンプレート取得テスト"""
        template = get_template(NotificationType.WELCOME, "ja")

        assert template is not None
        assert template.language == "ja"
        assert "ようこそ" in template.subject

    def test_get_template_en(self):
        """英語テンプレート取得テスト"""
        template = get_template(NotificationType.WELCOME, "en")

        assert template is not None
        assert template.language == "en"
        assert "Welcome" in template.subject

    def test_get_template_fallback_to_ja(self):
        """存在しない言語のフォールバックテスト"""
        # TRIAL_STARTEDは日本語のみ
        template = get_template(NotificationType.TRIAL_STARTED, "fr")

        assert template is not None
        assert template.language == "ja"

    def test_get_template_not_found(self):
        """存在しないテンプレートテスト"""
        # MONTHLY_REPORTテンプレートは未実装
        template = get_template(NotificationType.MONTHLY_REPORT, "ja")

        assert template is None


# --- APIエンドポイントテスト ---
class TestNotificationsAPI:
    """通知APIエンドポイントのテスト"""

    def setup_method(self):
        """テストセットアップ"""
        # テスト用APIキーを作成
        self.create_response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "pro", "name": "Notification Test"},
        )
        if self.create_response.status_code == 201:
            self.api_key = self.create_response.json()["api_key"]
            self.headers = {"X-API-Key": self.api_key}
        else:
            self.api_key = None
            self.headers = {}

    def test_get_notification_types(self):
        """通知タイプ一覧取得テスト"""
        response = client.get("/api/v1/notifications/types")

        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert len(data["types"]) > 0

        # カテゴリが含まれていることを確認
        categories = {t["category"] for t in data["types"]}
        assert "transactional" in categories
        assert "usage" in categories

    def test_get_service_status(self):
        """メールサービス状態取得テスト"""
        response = client.get("/api/v1/notifications/service/status")

        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert "enabled" in data

    def test_get_preferences_unauthenticated(self):
        """未認証での通知設定取得テスト"""
        response = client.get("/api/v1/notifications/preferences")

        assert response.status_code == 401

    def test_get_preferences(self):
        """通知設定取得テスト"""
        if not self.api_key:
            pytest.skip("API key creation failed")

        response = client.get(
            "/api/v1/notifications/preferences",
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert "marketing_emails" in data

    def test_update_preferences(self):
        """通知設定更新テスト"""
        if not self.api_key:
            pytest.skip("API key creation failed")

        response = client.patch(
            "/api/v1/notifications/preferences",
            headers=self.headers,
            json={
                "weekly_summary": False,
                "language": "en",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["weekly_summary"] is False
        assert data["language"] == "en"

    def test_get_logs(self):
        """送信ログ取得テスト"""
        if not self.api_key:
            pytest.skip("API key creation failed")

        response = client.get(
            "/api/v1/notifications/logs",
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data

    def test_get_stats(self):
        """統計取得テスト"""
        if not self.api_key:
            pytest.skip("API key creation failed")

        response = client.get(
            "/api/v1/notifications/stats",
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "delivery_rate" in data

    def test_track_open(self):
        """開封トラッキングテスト"""
        response = client.get("/api/v1/notifications/track/open/test_log_id")

        # 1x1 GIF画像が返される
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/gif"

    def test_track_click(self):
        """クリックトラッキングテスト"""
        response = client.get(
            "/api/v1/notifications/track/click/test_log_id",
            params={"url": "https://example.com"},
            follow_redirects=False,
        )

        # リダイレクトが返される
        assert response.status_code == 302
        assert response.headers["location"] == "https://example.com"


class TestNotificationsAPIAdmin:
    """管理者用通知APIテスト"""

    def setup_method(self):
        """テストセットアップ"""
        # Enterprise（管理者）APIキーを作成
        self.create_response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "enterprise", "name": "Admin Notification Test"},
        )
        if self.create_response.status_code == 201:
            self.api_key = self.create_response.json()["api_key"]
            self.headers = {"X-API-Key": self.api_key}
        else:
            self.api_key = None
            self.headers = {}

    def test_send_notification_admin_only(self):
        """管理者のみ通知送信可能テスト"""
        # 非管理者用キー
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Non-admin"},
        )
        if response.status_code != 201:
            pytest.skip("API key creation failed")

        non_admin_key = response.json()["api_key"]

        send_response = client.post(
            "/api/v1/notifications/send",
            headers={"X-API-Key": non_admin_key},
            json={
                "user_id": "test_user",
                "notification_type": "welcome",
                "context": {"user_name": "Test"},
            },
        )

        assert send_response.status_code == 403

    def test_get_all_stats_admin_only(self):
        """管理者のみ全体統計取得可能テスト"""
        # 非管理者用キー
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Non-admin Stats"},
        )
        if response.status_code != 201:
            pytest.skip("API key creation failed")

        non_admin_key = response.json()["api_key"]

        stats_response = client.get(
            "/api/v1/notifications/stats/all",
            headers={"X-API-Key": non_admin_key},
        )

        assert stats_response.status_code == 403

    def test_get_all_stats(self):
        """管理者による全体統計取得テスト"""
        if not self.api_key:
            pytest.skip("API key creation failed")

        response = client.get(
            "/api/v1/notifications/stats/all",
            headers=self.headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data


class TestUnsubscribe:
    """配信停止テスト"""

    def test_unsubscribe_user_not_found(self):
        """存在しないユーザーの配信停止テスト"""
        response = client.post(
            "/api/v1/notifications/unsubscribe",
            json={"user_id": "nonexistent"},
        )

        assert response.status_code == 404

    def test_unsubscribe_no_changes(self):
        """変更なしの配信停止テスト"""
        # 設定を作成
        from src.api.notifications.manager import get_notification_manager
        manager = get_notification_manager()
        manager.create_default_preference("unsub_test", "test@example.com")

        response = client.post(
            "/api/v1/notifications/unsubscribe",
            json={"user_id": "unsub_test"},
        )

        assert response.status_code == 200
        assert "変更はありません" in response.json()["message"]

    def test_unsubscribe_all(self):
        """全配信停止テスト"""
        from src.api.notifications.manager import get_notification_manager
        manager = get_notification_manager()
        manager.create_default_preference("unsub_all_test", "test@example.com")

        response = client.post(
            "/api/v1/notifications/unsubscribe",
            json={"user_id": "unsub_all_test", "unsubscribe_all": True},
        )

        assert response.status_code == 200
        assert "全て" in response.json()["message"]

        # 設定が更新されたことを確認
        pref = manager.get_preference("unsub_all_test")
        assert pref.marketing_emails is False
        assert pref.weekly_summary is False

    def test_unsubscribe_specific_types(self):
        """特定タイプの配信停止テスト"""
        from src.api.notifications.manager import get_notification_manager
        manager = get_notification_manager()
        manager.create_default_preference("unsub_type_test", "test@example.com")

        response = client.post(
            "/api/v1/notifications/unsubscribe",
            json={
                "user_id": "unsub_type_test",
                "notification_types": ["weekly_summary", "monthly_report"],
            },
        )

        assert response.status_code == 200
        assert "2種類" in response.json()["message"]

        # 設定が更新されたことを確認
        pref = manager.get_preference("unsub_type_test")
        assert pref.weekly_summary is False
        assert pref.monthly_report is False

    def test_unsubscribe_usage_alerts(self):
        """使用量アラート配信停止テスト"""
        from src.api.notifications.manager import get_notification_manager
        manager = get_notification_manager()
        manager.create_default_preference("unsub_usage_test", "test@example.com")

        response = client.post(
            "/api/v1/notifications/unsubscribe",
            json={
                "user_id": "unsub_usage_test",
                "notification_types": ["usage_warning", "credits_low"],
            },
        )

        assert response.status_code == 200

        pref = manager.get_preference("unsub_usage_test")
        assert pref.usage_alerts is False

    def test_unsubscribe_referral(self):
        """紹介通知配信停止テスト"""
        from src.api.notifications.manager import get_notification_manager
        manager = get_notification_manager()
        manager.create_default_preference("unsub_ref_test", "test@example.com")

        response = client.post(
            "/api/v1/notifications/unsubscribe",
            json={
                "user_id": "unsub_ref_test",
                "notification_types": ["referral_signed_up"],
            },
        )

        assert response.status_code == 200

        pref = manager.get_preference("unsub_ref_test")
        assert pref.referral_notifications is False


class TestNotificationRoutesErrorCases:
    """通知ルートのエラーケーステスト（カバレッジ向上）"""

    def test_get_log_detail_not_found(self):
        """存在しないログ詳細取得で404"""
        # APIキー作成
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Log Test"},
        )
        if response.status_code != 201:
            pytest.skip("API key creation failed")

        api_key = response.json()["api_key"]

        log_response = client.get(
            "/api/v1/notifications/logs/nonexistent_log_id",
            headers={"X-API-Key": api_key},
        )

        assert log_response.status_code == 404
        assert "not found" in log_response.json()["detail"].lower()

    def test_get_log_detail_access_denied(self):
        """他ユーザーのログ詳細取得で403"""
        from src.api.notifications.manager import get_notification_manager
        from src.api.notifications.models import EmailLog, EmailStatus

        manager = get_notification_manager()

        # 他ユーザーのログを作成
        log = EmailLog(
            log_id="test_log_403",
            user_id="other_user",
            email="other@example.com",
            notification_type="welcome",
            subject="Test",
            template_id="welcome",
        )
        manager._logs["test_log_403"] = log

        # APIキー作成
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Access Test"},
        )
        if response.status_code != 201:
            pytest.skip("API key creation failed")

        api_key = response.json()["api_key"]

        log_response = client.get(
            "/api/v1/notifications/logs/test_log_403",
            headers={"X-API-Key": api_key},
        )

        assert log_response.status_code == 403
        assert "denied" in log_response.json()["detail"].lower()

    def test_send_notification_admin_success(self):
        """管理者による通知送信成功テスト"""
        # Enterprise（管理者）APIキー作成
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "enterprise", "name": "Admin Send Test"},
        )
        if response.status_code != 201:
            pytest.skip("API key creation failed")

        api_key = response.json()["api_key"]

        # 対象ユーザーの設定を作成
        from src.api.notifications.manager import get_notification_manager
        manager = get_notification_manager()
        manager.create_default_preference("target_user", "target@example.com")

        # 通知送信
        send_response = client.post(
            "/api/v1/notifications/send",
            headers={"X-API-Key": api_key},
            json={
                "user_id": "target_user",
                "notification_type": "welcome",
                "context": {"user_name": "Test User"},
            },
        )

        assert send_response.status_code == 200
        data = send_response.json()
        # 開発モードなのでログIDは生成されるがメールは送信されない
        assert "success" in data

    def test_send_test_email_admin(self):
        """管理者によるテストメール送信テスト"""
        # Enterprise（管理者）APIキー作成
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "enterprise", "name": "Test Email Admin"},
        )
        if response.status_code != 201:
            pytest.skip("API key creation failed")

        api_key = response.json()["api_key"]

        # テストメール送信
        send_response = client.post(
            "/api/v1/notifications/test",
            headers={"X-API-Key": api_key},
            json={
                "email": "test@example.com",
                "notification_type": "welcome",
                "context": {"extra": "data"},
            },
        )

        assert send_response.status_code == 200
        data = send_response.json()
        assert "success" in data

    def test_send_test_email_non_admin(self):
        """非管理者によるテストメール送信で403"""
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "Non-admin Test Email"},
        )
        if response.status_code != 201:
            pytest.skip("API key creation failed")

        api_key = response.json()["api_key"]

        send_response = client.post(
            "/api/v1/notifications/test",
            headers={"X-API-Key": api_key},
            json={
                "email": "test@example.com",
                "notification_type": "welcome",
                "context": {},
            },
        )

        assert send_response.status_code == 403

    def test_update_preferences_creates_default(self):
        """設定が存在しない場合の更新でデフォルト作成テスト"""
        # 新しいAPIキー作成（設定が存在しない状態）
        response = client.post(
            "/api/v1/auth/keys",
            json={"tier": "basic", "name": "New Pref User"},
        )
        if response.status_code != 201:
            pytest.skip("API key creation failed")

        api_key = response.json()["api_key"]

        # 設定更新（デフォルト作成が行われる）
        update_response = client.patch(
            "/api/v1/notifications/preferences",
            headers={"X-API-Key": api_key},
            json={"weekly_summary": False},
        )

        assert update_response.status_code == 200
        data = update_response.json()
        assert data["weekly_summary"] is False

    def test_track_open(self):
        """メール開封トラッキングテスト"""
        response = client.get("/api/v1/notifications/track/open/test_log_id")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/gif"

    def test_track_click(self):
        """リンククリックトラッキングテスト"""
        response = client.get(
            "/api/v1/notifications/track/click/test_log_id?url=https://example.com",
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers["location"] == "https://example.com"
