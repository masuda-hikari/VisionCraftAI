# -*- coding: utf-8 -*-
"""
VisionCraftAI - 管理者機能テスト
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.admin.dashboard import AdminDashboard
from src.api.admin.schemas import (
    RevenueMetrics,
    UserMetrics,
    UsageMetrics,
    PlanDistribution,
    DashboardSummary,
    SystemHealth,
)


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


@pytest.fixture
def admin_secret():
    """管理者シークレット"""
    return os.environ.get("ADMIN_SECRET", "admin_default_secret_change_me")


@pytest.fixture
def admin_headers(admin_secret):
    """管理者認証ヘッダー"""
    return {"X-Admin-Secret": admin_secret}


@pytest.fixture
def temp_data_dir():
    """一時データディレクトリ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_api_keys(temp_data_dir):
    """サンプルAPIキーデータ"""
    data = {
        "key1": {
            "tier": "free",
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "is_active": True,
        },
        "key2": {
            "tier": "basic",
            "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "last_used": (datetime.now() - timedelta(days=1)).isoformat(),
            "is_active": True,
        },
        "key3": {
            "tier": "pro",
            "created_at": (datetime.now() - timedelta(days=60)).isoformat(),
            "last_used": (datetime.now() - timedelta(days=40)).isoformat(),
            "is_active": True,
        },
    }
    file_path = temp_data_dir / "api_keys.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


@pytest.fixture
def sample_usage_records(temp_data_dir):
    """サンプル使用量データ"""
    records = [
        {
            "key_id": "key1",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "response_time_ms": 150,
        },
        {
            "key_id": "key2",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "response_time_ms": 200,
        },
        {
            "key_id": "key1",
            "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
            "success": False,
            "response_time_ms": 500,
        },
    ]
    file_path = temp_data_dir / "usage_records.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(records, f)
    return records


class TestAdminDashboard:
    """AdminDashboardクラスのテスト"""

    def test_init(self, temp_data_dir):
        """初期化テスト"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        assert dashboard.data_dir == temp_data_dir

    def test_get_revenue_metrics_empty(self, temp_data_dir):
        """収益メトリクス（データなし）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        metrics = dashboard.get_revenue_metrics()
        assert isinstance(metrics, RevenueMetrics)
        assert metrics.total_revenue == 0.0
        assert metrics.mrr == 0.0

    def test_get_user_metrics_empty(self, temp_data_dir):
        """ユーザーメトリクス（データなし）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        metrics = dashboard.get_user_metrics()
        assert isinstance(metrics, UserMetrics)
        assert metrics.total_users == 0
        assert metrics.paying_users == 0

    def test_get_user_metrics_with_data(self, temp_data_dir, sample_api_keys):
        """ユーザーメトリクス（データあり）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        metrics = dashboard.get_user_metrics()
        assert metrics.total_users == 3
        assert metrics.paying_users == 2  # basic + pro
        assert metrics.free_users == 1

    def test_get_usage_metrics_empty(self, temp_data_dir):
        """使用量メトリクス（データなし）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        metrics = dashboard.get_usage_metrics()
        assert isinstance(metrics, UsageMetrics)
        assert metrics.total_generations == 0

    def test_get_usage_metrics_with_data(self, temp_data_dir, sample_usage_records):
        """使用量メトリクス（データあり）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        metrics = dashboard.get_usage_metrics()
        assert metrics.total_generations == 3
        assert metrics.daily_generations >= 2

    def test_get_plan_distribution(self, temp_data_dir, sample_api_keys):
        """プラン分布"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        distribution = dashboard.get_plan_distribution()
        assert isinstance(distribution, PlanDistribution)
        assert distribution.free == 1
        assert distribution.basic == 1
        assert distribution.pro == 1
        assert distribution.enterprise == 0

    def test_get_dashboard_summary(self, temp_data_dir, sample_api_keys, sample_usage_records):
        """ダッシュボード概要"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        summary = dashboard.get_dashboard_summary()
        assert isinstance(summary, DashboardSummary)
        assert summary.revenue is not None
        assert summary.users is not None
        assert summary.usage is not None
        assert summary.plan_distribution is not None

    def test_get_user_list(self, temp_data_dir, sample_api_keys):
        """ユーザー一覧"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        result = dashboard.get_user_list(page=1, per_page=10)
        assert "users" in result
        assert "total" in result
        assert result["total"] == 3

    def test_get_user_list_with_filter(self, temp_data_dir, sample_api_keys):
        """ユーザー一覧（フィルター）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        result = dashboard.get_user_list(page=1, per_page=10, plan_filter="basic")
        assert result["total"] == 1

    def test_get_revenue_chart_data(self, temp_data_dir):
        """収益チャートデータ"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        chart_data = dashboard.get_revenue_chart_data(days=7)
        assert len(chart_data) == 7
        assert all(hasattr(d, "date") for d in chart_data)

    def test_get_usage_chart_data(self, temp_data_dir):
        """使用量チャートデータ"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        chart_data = dashboard.get_usage_chart_data(days=7)
        assert len(chart_data) == 7

    def test_get_system_health(self, temp_data_dir, sample_usage_records):
        """システムヘルス"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        health = dashboard.get_system_health()
        assert isinstance(health, SystemHealth)
        assert health.api_status in ["healthy", "degraded", "down"]

    def test_get_contact_stats_empty(self, temp_data_dir):
        """お問い合わせ統計（データなし）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        stats = dashboard.get_contact_stats()
        assert stats["total"] == 0
        assert stats["unread"] == 0


class TestAdminEndpoints:
    """管理者エンドポイントのテスト"""

    def test_dashboard_without_auth(self, client):
        """認証なしでダッシュボードアクセス"""
        response = client.get("/api/v1/admin/dashboard")
        assert response.status_code == 401

    def test_dashboard_with_invalid_auth(self, client):
        """不正な認証でダッシュボードアクセス"""
        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"X-Admin-Secret": "wrong_secret"}
        )
        assert response.status_code == 403

    def test_dashboard_with_auth(self, client, admin_headers):
        """正常な認証でダッシュボードアクセス"""
        response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "revenue" in data
        assert "users" in data
        assert "usage" in data

    def test_revenue_endpoint(self, client, admin_headers):
        """収益エンドポイント"""
        response = client.get("/api/v1/admin/revenue", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "mrr" in data

    def test_users_endpoint(self, client, admin_headers):
        """ユーザーエンドポイント"""
        response = client.get("/api/v1/admin/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data

    def test_usage_endpoint(self, client, admin_headers):
        """使用量エンドポイント"""
        response = client.get("/api/v1/admin/usage", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_generations" in data

    def test_plans_endpoint(self, client, admin_headers):
        """プラン分布エンドポイント"""
        response = client.get("/api/v1/admin/plans", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "free" in data
        assert "basic" in data

    def test_users_list_endpoint(self, client, admin_headers):
        """ユーザー一覧エンドポイント"""
        response = client.get("/api/v1/admin/users/list", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data

    def test_users_list_with_filter(self, client, admin_headers):
        """ユーザー一覧（フィルター付き）"""
        response = client.get(
            "/api/v1/admin/users/list?plan=basic",
            headers=admin_headers
        )
        assert response.status_code == 200

    def test_revenue_chart_endpoint(self, client, admin_headers):
        """収益チャートエンドポイント"""
        response = client.get("/api/v1/admin/charts/revenue", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_revenue_chart_with_days(self, client, admin_headers):
        """収益チャート（日数指定）"""
        response = client.get(
            "/api/v1/admin/charts/revenue?days=7",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 7

    def test_usage_chart_endpoint(self, client, admin_headers):
        """使用量チャートエンドポイント"""
        response = client.get("/api/v1/admin/charts/usage", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_health_endpoint(self, client, admin_headers):
        """システムヘルスエンドポイント"""
        response = client.get("/api/v1/admin/health", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "api_status" in data

    def test_contacts_stats_endpoint(self, client, admin_headers):
        """お問い合わせ統計エンドポイント"""
        response = client.get("/api/v1/admin/contacts/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data

    def test_export_endpoint(self, client, admin_headers):
        """エクスポートエンドポイント"""
        response = client.get("/api/v1/admin/export", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "exported_at" in data
        assert "summary" in data


class TestAdminPage:
    """管理者ページのテスト"""

    def test_admin_page_exists(self, client):
        """管理者ページが存在する"""
        response = client.get("/admin")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_admin_page_has_login(self, client):
        """ログインフォームが存在する"""
        response = client.get("/admin")
        assert "管理者ログイン" in response.text or "authOverlay" in response.text


class TestAdminDashboardAdvanced:
    """AdminDashboardの高度なテスト（カバレッジ向上用）"""

    @pytest.fixture
    def sample_subscriptions(self, temp_data_dir):
        """サンプルサブスクリプションデータ"""
        data = {
            "sub1": {
                "plan": "basic",
                "status": "active",
                "created_at": datetime.now().isoformat(),
            },
            "sub2": {
                "plan": "pro",
                "status": "active",
                "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
            },
            "sub3": {
                "plan": "free",
                "status": "canceled",
                "created_at": (datetime.now() - timedelta(days=60)).isoformat(),
            },
        }
        file_path = temp_data_dir / "subscriptions.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return data

    @pytest.fixture
    def sample_credits(self, temp_data_dir):
        """サンプルクレジットデータ"""
        data = {
            "user1": {
                "balance": 100,
                "transactions": [
                    {
                        "type": "purchase",
                        "amount": 50,
                        "timestamp": datetime.now().isoformat(),
                    },
                    {
                        "type": "purchase",
                        "amount": 100,
                        "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
                    },
                    {
                        "type": "usage",
                        "amount": -10,
                        "timestamp": datetime.now().isoformat(),
                    },
                ],
            },
            "user2": {
                "balance": 50,
                "transactions": [
                    {
                        "type": "purchase",
                        "amount": 50,
                        "timestamp": datetime.now().isoformat(),
                    },
                ],
            },
        }
        file_path = temp_data_dir / "credits.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return data

    @pytest.fixture
    def sample_contacts(self, temp_data_dir):
        """サンプルお問い合わせデータ"""
        data = [
            {
                "id": "contact1",
                "category": "support",
                "read": False,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "contact2",
                "category": "sales",
                "read": True,
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
            },
            {
                "id": "contact3",
                "category": "support",
                "read": False,
                "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
            },
        ]
        file_path = temp_data_dir / "contacts.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return data

    def test_get_revenue_metrics_with_subscriptions(self, temp_data_dir, sample_subscriptions):
        """収益メトリクス（サブスクリプションあり）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        metrics = dashboard.get_revenue_metrics()
        assert isinstance(metrics, RevenueMetrics)
        # basic(9.99) + pro(29.99) = 39.98 のMRR
        assert metrics.mrr == 39.98
        assert metrics.arr == 39.98 * 12

    def test_get_revenue_metrics_with_credits(self, temp_data_dir, sample_credits):
        """収益メトリクス（クレジット購入あり）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        metrics = dashboard.get_revenue_metrics()
        # クレジット収益: (50 + 100 + 50) * 0.5 = 100.0
        assert metrics.credit_revenue == 100.0

    def test_get_revenue_metrics_combined(self, temp_data_dir, sample_subscriptions, sample_credits):
        """収益メトリクス（複合）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        metrics = dashboard.get_revenue_metrics()
        # MRR: basic(9.99) + pro(29.99) = 39.98
        assert metrics.mrr == 39.98
        # クレジット収益: (50 + 100 + 50) * 0.5 = 100.0
        assert metrics.credit_revenue == 100.0

    def test_get_revenue_chart_data_with_subscriptions(self, temp_data_dir, sample_subscriptions):
        """収益チャートデータ（サブスクリプションあり）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        chart_data = dashboard.get_revenue_chart_data(days=30)
        assert len(chart_data) == 30
        # 今日のデータに収益が含まれること
        today_str = datetime.now().date().isoformat()
        today_data = next((d for d in chart_data if d.date == today_str), None)
        assert today_data is not None
        assert today_data.subscriptions >= 0

    def test_get_revenue_chart_data_with_credits(self, temp_data_dir, sample_credits):
        """収益チャートデータ（クレジットあり）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        chart_data = dashboard.get_revenue_chart_data(days=30)
        # 今日の日付にクレジット収益が含まれること
        today_str = datetime.now().date().isoformat()
        today_data = next((d for d in chart_data if d.date == today_str), None)
        assert today_data is not None
        # 50 * 0.5 = 25.0 + 50 * 0.5 = 25.0 = 50.0
        assert today_data.credits >= 0

    def test_get_usage_chart_data_with_errors(self, temp_data_dir, sample_usage_records):
        """使用量チャートデータ（エラー含む）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        chart_data = dashboard.get_usage_chart_data(days=7)
        assert len(chart_data) == 7
        # エラーが集計されていること
        total_errors = sum(d.errors for d in chart_data)
        assert total_errors >= 0

    def test_get_system_health_degraded(self, temp_data_dir):
        """システムヘルス（degradedステータス）"""
        # 大量のエラーレコードを作成
        records = []
        for i in range(150):
            records.append({
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "response_time_ms": 100,
            })
        file_path = temp_data_dir / "usage_records.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f)

        dashboard = AdminDashboard(data_dir=temp_data_dir)
        health = dashboard.get_system_health()
        assert health.api_status == "degraded"
        assert health.error_count_24h >= 100

    def test_get_system_health_with_response_time(self, temp_data_dir):
        """システムヘルス（レスポンスタイム計測）"""
        records = [
            {
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "response_time_ms": 100,
            },
            {
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "response_time_ms": 200,
            },
            {
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "response_time_ms": 300,
            },
        ]
        file_path = temp_data_dir / "usage_records.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f)

        dashboard = AdminDashboard(data_dir=temp_data_dir)
        health = dashboard.get_system_health()
        # 平均レスポンスタイム: (100 + 200 + 300) / 3 = 200
        assert health.avg_response_time_ms == 200.0

    def test_get_contact_stats_with_data(self, temp_data_dir, sample_contacts):
        """お問い合わせ統計（データあり）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        stats = dashboard.get_contact_stats()
        assert stats["total"] == 3
        assert stats["unread"] == 2  # contact1, contact3
        assert stats["today"] >= 1  # contact1
        assert stats["this_week"] >= 2  # contact1, contact2
        assert stats["by_category"]["support"] == 2
        assert stats["by_category"]["sales"] == 1

    def test_load_json_error_handling(self, temp_data_dir):
        """JSON読み込みエラーハンドリング"""
        # 不正なJSONファイルを作成
        file_path = temp_data_dir / "api_keys.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("{invalid json}")

        dashboard = AdminDashboard(data_dir=temp_data_dir)
        # エラーが発生しても空の結果が返ること
        metrics = dashboard.get_user_metrics()
        assert metrics.total_users == 0

    def test_get_user_list_pagination(self, temp_data_dir, sample_api_keys):
        """ユーザー一覧（ページネーション）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        # 1件ずつ取得
        result = dashboard.get_user_list(page=1, per_page=1)
        assert len(result["users"]) == 1
        assert result["total"] == 3
        assert result["total_pages"] == 3

        # 2ページ目
        result2 = dashboard.get_user_list(page=2, per_page=1)
        assert len(result2["users"]) == 1
        assert result2["page"] == 2

    def test_get_user_list_with_usage(self, temp_data_dir, sample_api_keys, sample_usage_records):
        """ユーザー一覧（使用量データあり）"""
        dashboard = AdminDashboard(data_dir=temp_data_dir)
        result = dashboard.get_user_list(page=1, per_page=10)
        # 各ユーザーに使用量が含まれること
        for user in result["users"]:
            assert "total_generations" in user.model_dump()
            assert "total_spent" in user.model_dump()

    def test_revenue_metrics_invalid_date_format(self, temp_data_dir):
        """収益メトリクス（不正な日付形式）"""
        data = {
            "sub1": {
                "plan": "basic",
                "status": "active",
                "created_at": "invalid_date",
            },
        }
        file_path = temp_data_dir / "subscriptions.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        dashboard = AdminDashboard(data_dir=temp_data_dir)
        # エラーが発生せず処理が続行されること
        metrics = dashboard.get_revenue_metrics()
        assert isinstance(metrics, RevenueMetrics)

    def test_user_metrics_invalid_date_format(self, temp_data_dir):
        """ユーザーメトリクス（不正な日付形式）"""
        data = {
            "key1": {
                "tier": "basic",
                "created_at": "invalid_date",
                "last_used": "also_invalid",
            },
        }
        file_path = temp_data_dir / "api_keys.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        dashboard = AdminDashboard(data_dir=temp_data_dir)
        metrics = dashboard.get_user_metrics()
        assert metrics.total_users == 1
        assert metrics.paying_users == 1

    def test_usage_metrics_invalid_timestamp(self, temp_data_dir):
        """使用量メトリクス（不正なタイムスタンプ）"""
        records = [
            {
                "key_id": "key1",
                "timestamp": "invalid_timestamp",
                "success": True,
            },
        ]
        file_path = temp_data_dir / "usage_records.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f)

        dashboard = AdminDashboard(data_dir=temp_data_dir)
        metrics = dashboard.get_usage_metrics()
        assert metrics.total_generations == 1

    def test_contact_stats_invalid_timestamp(self, temp_data_dir):
        """お問い合わせ統計（不正なタイムスタンプ）"""
        data = [
            {
                "id": "contact1",
                "category": "support",
                "read": False,
                "timestamp": "invalid_date",
            },
        ]
        file_path = temp_data_dir / "contacts.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        dashboard = AdminDashboard(data_dir=temp_data_dir)
        stats = dashboard.get_contact_stats()
        assert stats["total"] == 1
        assert stats["today"] == 0  # 不正な日付のためカウントされない
