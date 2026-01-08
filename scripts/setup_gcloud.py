#!/usr/bin/env python3
"""
Google Cloud セットアップスクリプト

VisionCraftAI の Google Cloud 環境をセットアップするための自動化スクリプト。
サービスアカウント作成、API有効化、認証情報の設定を行う。

使用方法:
    python scripts/setup_gcloud.py --project YOUR_PROJECT_ID

前提条件:
    - gcloud CLI がインストールされていること
    - gcloud auth login が完了していること
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


class GCloudSetup:
    """Google Cloud セットアップクラス"""

    # 必要なAPIリスト
    REQUIRED_APIS = [
        "aiplatform.googleapis.com",  # Vertex AI
        "generativelanguage.googleapis.com",  # Gemini API
        "storage.googleapis.com",  # Cloud Storage
        "secretmanager.googleapis.com",  # Secret Manager
    ]

    # サービスアカウントに付与するロール
    SERVICE_ACCOUNT_ROLES = [
        "roles/aiplatform.user",  # Vertex AI 使用権限
        "roles/storage.objectViewer",  # Storage 読み取り
        "roles/secretmanager.secretAccessor",  # Secret Manager 読み取り
    ]

    def __init__(self, project_id: str, region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        self.service_account_name = "visioncraftai-service"
        self.service_account_email = f"{self.service_account_name}@{project_id}.iam.gserviceaccount.com"
        self.credentials_dir = Path(__file__).parent.parent / "credentials"
        self.credentials_file = self.credentials_dir / "service-account.json"

    def run_command(self, cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """コマンド実行"""
        print(f"  実行: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"  エラー: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        return result

    def check_gcloud_installed(self) -> bool:
        """gcloud CLI インストール確認"""
        print("\n[1/7] gcloud CLI 確認...")
        try:
            result = self.run_command(["gcloud", "--version"], check=False)
            if result.returncode == 0:
                print("  ✓ gcloud CLI インストール済み")
                return True
            else:
                print("  ✗ gcloud CLI が見つかりません")
                print("  インストール: https://cloud.google.com/sdk/docs/install")
                return False
        except FileNotFoundError:
            print("  ✗ gcloud CLI が見つかりません")
            print("  インストール: https://cloud.google.com/sdk/docs/install")
            return False

    def check_auth(self) -> bool:
        """認証状態確認"""
        print("\n[2/7] 認証状態確認...")
        result = self.run_command(["gcloud", "auth", "list", "--format=json"], check=False)
        if result.returncode != 0:
            print("  ✗ 認証されていません")
            print("  実行: gcloud auth login")
            return False

        accounts = json.loads(result.stdout)
        active = [a for a in accounts if a.get("status") == "ACTIVE"]
        if not active:
            print("  ✗ アクティブなアカウントがありません")
            print("  実行: gcloud auth login")
            return False

        print(f"  ✓ 認証済み: {active[0].get('account')}")
        return True

    def set_project(self) -> bool:
        """プロジェクト設定"""
        print(f"\n[3/7] プロジェクト設定: {self.project_id}...")

        # プロジェクト存在確認
        result = self.run_command(
            ["gcloud", "projects", "describe", self.project_id, "--format=json"],
            check=False
        )
        if result.returncode != 0:
            print(f"  ✗ プロジェクト '{self.project_id}' が見つかりません")
            return False

        # プロジェクト設定
        self.run_command(["gcloud", "config", "set", "project", self.project_id])
        print(f"  ✓ プロジェクト設定完了")
        return True

    def enable_apis(self) -> bool:
        """必要なAPI有効化"""
        print("\n[4/7] API 有効化...")

        for api in self.REQUIRED_APIS:
            print(f"  有効化中: {api}")
            result = self.run_command(
                ["gcloud", "services", "enable", api, f"--project={self.project_id}"],
                check=False
            )
            if result.returncode != 0:
                print(f"  ✗ {api} の有効化に失敗")
                return False
            print(f"    ✓ {api}")

        print("  ✓ 全API有効化完了")
        return True

    def create_service_account(self) -> bool:
        """サービスアカウント作成"""
        print(f"\n[5/7] サービスアカウント作成: {self.service_account_name}...")

        # 既存確認
        result = self.run_command(
            ["gcloud", "iam", "service-accounts", "describe", self.service_account_email, f"--project={self.project_id}"],
            check=False
        )

        if result.returncode == 0:
            print("  ✓ サービスアカウント既存")
        else:
            # 作成
            result = self.run_command([
                "gcloud", "iam", "service-accounts", "create", self.service_account_name,
                f"--project={self.project_id}",
                "--display-name=VisionCraftAI Service Account",
                "--description=VisionCraftAI画像生成サービス用サービスアカウント"
            ], check=False)

            if result.returncode != 0:
                print("  ✗ サービスアカウント作成失敗")
                return False
            print("  ✓ サービスアカウント作成完了")

        return True

    def grant_roles(self) -> bool:
        """ロール付与"""
        print("\n[6/7] ロール付与...")

        for role in self.SERVICE_ACCOUNT_ROLES:
            print(f"  付与中: {role}")
            result = self.run_command([
                "gcloud", "projects", "add-iam-policy-binding", self.project_id,
                f"--member=serviceAccount:{self.service_account_email}",
                f"--role={role}",
                "--condition=None"
            ], check=False)

            if result.returncode != 0 and "already exists" not in result.stderr:
                print(f"  警告: {role} の付与でエラー（既に存在する可能性）")
            else:
                print(f"    ✓ {role}")

        print("  ✓ ロール付与完了")
        return True

    def create_key(self) -> bool:
        """サービスアカウントキー作成"""
        print("\n[7/7] 認証情報ファイル作成...")

        # ディレクトリ作成
        self.credentials_dir.mkdir(parents=True, exist_ok=True)

        # .gitignore確認
        gitignore_path = self.credentials_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text("*\n!.gitignore\n", encoding="utf-8")
            print("  ✓ .gitignore 作成")

        # 既存キー削除確認
        if self.credentials_file.exists():
            print(f"  既存のキーファイルが存在: {self.credentials_file}")
            response = input("  上書きしますか？ (y/N): ")
            if response.lower() != "y":
                print("  スキップ")
                return True
            self.credentials_file.unlink()

        # キー作成
        result = self.run_command([
            "gcloud", "iam", "service-accounts", "keys", "create",
            str(self.credentials_file),
            f"--iam-account={self.service_account_email}",
            f"--project={self.project_id}"
        ], check=False)

        if result.returncode != 0:
            print("  ✗ キー作成失敗")
            return False

        print(f"  ✓ 認証情報保存: {self.credentials_file}")
        return True

    def create_env_file(self):
        """環境変数設定の案内"""
        print("\n" + "=" * 60)
        print("セットアップ完了！")
        print("=" * 60)
        print("\n次のステップ:")
        print("\n1. .env ファイルに以下を追加:")
        print("-" * 40)
        print(f'GOOGLE_APPLICATION_CREDENTIALS="{self.credentials_file.absolute()}"')
        print(f'GOOGLE_CLOUD_PROJECT="{self.project_id}"')
        print(f'GOOGLE_CLOUD_REGION="{self.region}"')
        print("-" * 40)
        print("\n2. API接続テスト:")
        print("   python -c \"from src.generator.gemini_client import GeminiClient; print(GeminiClient().generate_image('test'))\"")
        print("\n3. サーバー起動:")
        print("   python -m src.api.app")
        print()

    def setup(self) -> bool:
        """セットアップ実行"""
        print("=" * 60)
        print("VisionCraftAI - Google Cloud セットアップ")
        print("=" * 60)
        print(f"プロジェクト: {self.project_id}")
        print(f"リージョン: {self.region}")

        steps = [
            self.check_gcloud_installed,
            self.check_auth,
            self.set_project,
            self.enable_apis,
            self.create_service_account,
            self.grant_roles,
            self.create_key,
        ]

        for step in steps:
            if not step():
                print("\n✗ セットアップ失敗")
                return False

        self.create_env_file()
        return True


def main():
    parser = argparse.ArgumentParser(
        description="VisionCraftAI Google Cloud セットアップ"
    )
    parser.add_argument(
        "--project", "-p",
        required=True,
        help="Google Cloud プロジェクトID"
    )
    parser.add_argument(
        "--region", "-r",
        default="us-central1",
        help="Google Cloud リージョン（デフォルト: us-central1）"
    )

    args = parser.parse_args()

    setup = GCloudSetup(args.project, args.region)
    success = setup.setup()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
