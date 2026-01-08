# -*- coding: utf-8 -*-
"""
VisionCraftAI - ダッシュボードテスト

ユーザーダッシュボードページとAPIのテスト
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


class TestDashboardPage:
    """ダッシュボードページのテスト"""

    def test_dashboard_page_exists(self, client):
        """ダッシュボードページが存在すること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_dashboard_page_has_login_form(self, client):
        """ダッシュボードページにログインフォームがあること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.text
        assert "loginOverlay" in content
        assert "apiKeyInput" in content
        assert "ログイン" in content

    def test_dashboard_page_has_tabs(self, client):
        """ダッシュボードページにタブがあること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.text
        assert "tab-subscription" in content
        assert "tab-usage" in content
        assert "tab-apikeys" in content
        assert "tab-credits" in content

    def test_dashboard_page_has_kpi_cards(self, client):
        """ダッシュボードページにKPIカードがあること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.text
        assert "monthlyUsed" in content
        assert "dailyUsed" in content
        assert "creditBalance" in content
        assert "apiKeyCount" in content

    def test_dashboard_page_has_plan_comparison(self, client):
        """ダッシュボードページにプラン比較表があること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.text
        assert "Free" in content
        assert "Basic" in content
        assert "Pro" in content
        assert "Enterprise" in content

    def test_dashboard_page_has_credit_packages(self, client):
        """ダッシュボードページにクレジットパッケージがあること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.text
        assert "credits_10" in content
        assert "credits_50" in content
        assert "credits_100" in content
        assert "credits_500" in content

    def test_dashboard_page_has_code_examples(self, client):
        """ダッシュボードページにコード例があること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.text
        assert "curl" in content.lower()
        assert "python" in content.lower()
        assert "X-API-Key" in content


class TestDashboardNavigation:
    """ダッシュボードナビゲーションのテスト"""

    def test_index_has_dashboard_link(self, client):
        """トップページにダッシュボードへのリンクがあること"""
        response = client.get("/")
        assert response.status_code == 200
        content = response.text
        assert "/dashboard" in content
        assert "ダッシュボード" in content

    def test_dashboard_has_logout_button(self, client):
        """ダッシュボードにログアウトボタンがあること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.text
        assert "logoutBtn" in content
        assert "ログアウト" in content

    def test_dashboard_has_api_docs_link(self, client):
        """ダッシュボードにAPIドキュメントへのリンクがあること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.text
        assert "/docs" in content


class TestDashboardModals:
    """ダッシュボードモーダルのテスト"""

    def test_dashboard_has_create_key_modal(self, client):
        """ダッシュボードにAPIキー作成モーダルがあること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.text
        assert "createKeyModal" in content
        assert "createKeyForm" in content

    def test_dashboard_has_show_key_modal(self, client):
        """ダッシュボードにAPIキー表示モーダルがあること"""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.text
        assert "showKeyModal" in content
        assert "newApiKey" in content


class TestDashboardAssets:
    """ダッシュボードアセットのテスト"""

    def test_dashboard_css_exists(self, client):
        """ダッシュボードCSSが存在すること"""
        response = client.get("/static/css/dashboard.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]

    def test_dashboard_js_exists(self, client):
        """ダッシュボードJavaScriptが存在すること"""
        response = client.get("/static/js/dashboard.js")
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]

    def test_dashboard_css_has_styles(self, client):
        """ダッシュボードCSSにスタイルが含まれていること"""
        response = client.get("/static/css/dashboard.css")
        assert response.status_code == 200
        content = response.text
        assert ".login-overlay" in content
        assert ".kpi-card" in content
        assert ".tab-btn" in content
        assert ".section-card" in content

    def test_dashboard_js_has_functions(self, client):
        """ダッシュボードJavaScriptに機能が含まれていること"""
        response = client.get("/static/js/dashboard.js")
        assert response.status_code == 200
        content = response.text
        assert "verifyAndLogin" in content
        assert "loadDashboardData" in content
        assert "switchTab" in content
        assert "loadApiKeys" in content


class TestDashboardIntegration:
    """ダッシュボード統合テスト"""

    def test_dashboard_uses_correct_api_endpoints(self, client):
        """ダッシュボードが正しいAPIエンドポイントを使用すること"""
        response = client.get("/static/js/dashboard.js")
        content = response.text
        # 必要なAPIエンドポイントが参照されていること
        assert "/auth/verify" in content
        assert "/auth/keys" in content
        assert "/auth/quota" in content
        assert "/payment/subscriptions/me" in content
        assert "/payment/credits/balance" in content
        assert "/payment/credits/transactions" in content

    def test_dashboard_handles_auth_correctly(self, client):
        """ダッシュボードが認証を正しく処理すること"""
        response = client.get("/static/js/dashboard.js")
        content = response.text
        # ローカルストレージを使用した認証状態管理
        assert "localStorage" in content
        assert "X-API-Key" in content
        assert "logout" in content
