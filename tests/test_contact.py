# -*- coding: utf-8 -*-
"""
VisionCraftAI - お問い合わせAPIテスト

お問い合わせ機能のテストを行います。
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


class TestContactSubmit:
    """お問い合わせ送信テスト"""

    def test_submit_contact_success(self, client):
        """正常なお問い合わせ送信"""
        response = client.post(
            "/api/v1/contact",
            json={
                "name": "山田太郎",
                "email": "yamada@example.com",
                "category": "general",
                "subject": "サービスについての質問",
                "message": "サービスの利用方法について教えてください。APIの使い方がわかりません。",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "ticket_id" in data
        assert data["ticket_id"].startswith("VCA-")

    def test_submit_contact_with_company(self, client):
        """会社名付きお問い合わせ"""
        response = client.post(
            "/api/v1/contact",
            json={
                "name": "鈴木一郎",
                "email": "suzuki@company.co.jp",
                "company": "株式会社テスト",
                "category": "enterprise",
                "subject": "Enterpriseプランについて",
                "message": "Enterpriseプランの詳細と見積もりをいただきたいです。月間1000枚程度の利用を想定しています。",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True

    def test_submit_contact_with_api_key(self, client):
        """APIキー付きお問い合わせ"""
        response = client.post(
            "/api/v1/contact",
            json={
                "name": "テストユーザー",
                "email": "test@example.com",
                "category": "technical",
                "subject": "技術的な問題",
                "message": "画像生成時にエラーが発生します。エラーコード500が返されます。調査をお願いします。",
                "api_key": "vca_test123.abc456",
            },
        )
        assert response.status_code == 201

    def test_submit_contact_missing_name(self, client):
        """名前なしエラー"""
        response = client.post(
            "/api/v1/contact",
            json={
                "email": "test@example.com",
                "category": "general",
                "subject": "テスト",
                "message": "テストメッセージです。10文字以上必要です。",
            },
        )
        assert response.status_code == 422

    def test_submit_contact_invalid_email(self, client):
        """無効なメールアドレス"""
        response = client.post(
            "/api/v1/contact",
            json={
                "name": "テスト",
                "email": "invalid-email",
                "category": "general",
                "subject": "テスト",
                "message": "テストメッセージです。10文字以上必要です。",
            },
        )
        assert response.status_code == 422

    def test_submit_contact_invalid_category(self, client):
        """無効なカテゴリ"""
        response = client.post(
            "/api/v1/contact",
            json={
                "name": "テスト",
                "email": "test@example.com",
                "category": "invalid_category",
                "subject": "テスト",
                "message": "テストメッセージです。10文字以上必要です。",
            },
        )
        assert response.status_code == 422

    def test_submit_contact_short_message(self, client):
        """短すぎるメッセージ"""
        response = client.post(
            "/api/v1/contact",
            json={
                "name": "テスト",
                "email": "test@example.com",
                "category": "general",
                "subject": "テスト",
                "message": "短い",
            },
        )
        assert response.status_code == 422

    def test_submit_contact_all_categories(self, client):
        """全カテゴリのテスト"""
        categories = [
            "general",
            "technical",
            "billing",
            "enterprise",
            "partnership",
            "bug",
            "feature",
            "other",
        ]
        for category in categories:
            response = client.post(
                "/api/v1/contact",
                json={
                    "name": "テスト",
                    "email": "test@example.com",
                    "category": category,
                    "subject": f"{category}のテスト",
                    "message": f"{category}カテゴリでのお問い合わせテストです。",
                },
            )
            assert response.status_code == 201, f"カテゴリ {category} でエラー"


class TestContactCategories:
    """カテゴリ一覧テスト"""

    def test_get_categories(self, client):
        """カテゴリ一覧取得"""
        response = client.get("/api/v1/contact/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 8

        # 必須カテゴリの確認
        category_ids = [c["id"] for c in data["categories"]]
        assert "general" in category_ids
        assert "enterprise" in category_ids
        assert "technical" in category_ids

    def test_categories_have_labels(self, client):
        """カテゴリにラベルがある"""
        response = client.get("/api/v1/contact/categories")
        data = response.json()
        for category in data["categories"]:
            assert "id" in category
            assert "label" in category
            assert len(category["label"]) > 0


class TestContactPages:
    """ページ表示テスト"""

    def test_terms_page(self, client):
        """利用規約ページ"""
        response = client.get("/terms", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "利用規約" in response.text

    def test_privacy_page(self, client):
        """プライバシーポリシーページ"""
        response = client.get("/privacy", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "プライバシーポリシー" in response.text

    def test_contact_page(self, client):
        """お問い合わせページ"""
        response = client.get("/contact", headers={"Accept": "text/html"})
        assert response.status_code == 200
        assert "お問い合わせ" in response.text


class TestContactValidation:
    """バリデーションテスト"""

    def test_name_max_length(self, client):
        """名前の最大長"""
        response = client.post(
            "/api/v1/contact",
            json={
                "name": "あ" * 101,  # 100文字超過
                "email": "test@example.com",
                "category": "general",
                "subject": "テスト",
                "message": "テストメッセージです。10文字以上必要です。",
            },
        )
        assert response.status_code == 422

    def test_subject_max_length(self, client):
        """件名の最大長"""
        response = client.post(
            "/api/v1/contact",
            json={
                "name": "テスト",
                "email": "test@example.com",
                "category": "general",
                "subject": "あ" * 201,  # 200文字超過
                "message": "テストメッセージです。10文字以上必要です。",
            },
        )
        assert response.status_code == 422

    def test_message_max_length(self, client):
        """メッセージの最大長"""
        response = client.post(
            "/api/v1/contact",
            json={
                "name": "テスト",
                "email": "test@example.com",
                "category": "general",
                "subject": "テスト",
                "message": "あ" * 5001,  # 5000文字超過
            },
        )
        assert response.status_code == 422

    def test_too_many_urls_in_message(self, client):
        """メッセージ内のURL過多"""
        message_with_many_urls = "テストです。" + " ".join(
            [f"https://example{i}.com" for i in range(6)]
        )
        response = client.post(
            "/api/v1/contact",
            json={
                "name": "テスト",
                "email": "test@example.com",
                "category": "general",
                "subject": "テスト",
                "message": message_with_many_urls,
            },
        )
        assert response.status_code == 422
