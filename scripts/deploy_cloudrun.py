#!/usr/bin/env python3
"""
Cloud Run デプロイスクリプト

VisionCraftAI を Google Cloud Run にデプロイするための自動化スクリプト。
Docker イメージのビルド、プッシュ、Cloud Run へのデプロイを行う。

使用方法:
    python scripts/deploy_cloudrun.py --project YOUR_PROJECT_ID

前提条件:
    - gcloud CLI がインストール・認証済み
    - Docker がインストール済み
    - setup_gcloud.py が実行済み
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


class CloudRunDeployer:
    """Cloud Run デプロイクラス"""

    def __init__(
        self,
        project_id: str,
        region: str = "us-central1",
        service_name: str = "visioncraftai",
        memory: str = "2Gi",
        cpu: str = "2",
        min_instances: int = 0,
        max_instances: int = 10,
    ):
        self.project_id = project_id
        self.region = region
        self.service_name = service_name
        self.memory = memory
        self.cpu = cpu
        self.min_instances = min_instances
        self.max_instances = max_instances

        self.image_name = f"gcr.io/{project_id}/{service_name}"
        self.project_root = Path(__file__).parent.parent

    def run_command(
        self, cmd: list[str], check: bool = True, cwd: Optional[Path] = None
    ) -> subprocess.CompletedProcess:
        """コマンド実行"""
        print(f"  実行: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd or self.project_root
        )
        if check and result.returncode != 0:
            print(f"  エラー: {result.stderr}")
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )
        return result

    def check_prerequisites(self) -> bool:
        """前提条件確認"""
        print("\n[1/6] 前提条件確認...")

        # gcloud確認
        result = self.run_command(["gcloud", "--version"], check=False)
        if result.returncode != 0:
            print("  ✗ gcloud CLI が見つかりません")
            return False
        print("  ✓ gcloud CLI")

        # Docker確認
        result = self.run_command(["docker", "--version"], check=False)
        if result.returncode != 0:
            print("  ✗ Docker が見つかりません")
            return False
        print("  ✓ Docker")

        # Dockerfile確認
        dockerfile = self.project_root / "Dockerfile"
        if not dockerfile.exists():
            print("  ✗ Dockerfile が見つかりません")
            return False
        print("  ✓ Dockerfile")

        # 認証確認
        result = self.run_command(
            ["gcloud", "auth", "list", "--format=json"], check=False
        )
        if result.returncode != 0:
            print("  ✗ gcloud 認証が必要です")
            return False
        print("  ✓ gcloud 認証")

        return True

    def configure_docker(self) -> bool:
        """Docker認証設定"""
        print("\n[2/6] Docker 認証設定...")

        result = self.run_command(
            ["gcloud", "auth", "configure-docker", "--quiet"], check=False
        )

        if result.returncode != 0:
            print("  ✗ Docker 認証設定失敗")
            return False

        print("  ✓ Docker 認証設定完了")
        return True

    def build_image(self) -> bool:
        """Dockerイメージビルド"""
        print("\n[3/6] Docker イメージビルド...")
        print(f"  イメージ: {self.image_name}")

        result = self.run_command(
            [
                "docker",
                "build",
                "-t",
                self.image_name,
                "-f",
                "Dockerfile",
                ".",
            ],
            check=False,
            cwd=self.project_root,
        )

        if result.returncode != 0:
            print("  ✗ ビルド失敗")
            print(result.stderr)
            return False

        print("  ✓ ビルド完了")
        return True

    def push_image(self) -> bool:
        """イメージプッシュ"""
        print("\n[4/6] Docker イメージプッシュ...")
        print(f"  プッシュ先: {self.image_name}")

        result = self.run_command(["docker", "push", self.image_name], check=False)

        if result.returncode != 0:
            print("  ✗ プッシュ失敗")
            return False

        print("  ✓ プッシュ完了")
        return True

    def load_env_vars(self) -> dict[str, str]:
        """環境変数読み込み"""
        env_vars = {}
        env_file = self.project_root / ".env"

        if env_file.exists():
            print("  .env ファイルから環境変数を読み込み中...")
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        # 機密情報はSecret Managerで管理推奨
                        if key not in [
                            "GOOGLE_APPLICATION_CREDENTIALS",
                            "STRIPE_SECRET_KEY",
                            "STRIPE_WEBHOOK_SECRET",
                        ]:
                            env_vars[key] = value

        # デフォルト環境変数
        env_vars.setdefault("ENVIRONMENT", "production")
        env_vars.setdefault("GOOGLE_CLOUD_PROJECT", self.project_id)
        env_vars.setdefault("GOOGLE_CLOUD_REGION", self.region)

        return env_vars

    def deploy_service(self) -> bool:
        """Cloud Run デプロイ"""
        print("\n[5/6] Cloud Run デプロイ...")

        # 環境変数準備
        env_vars = self.load_env_vars()
        env_str = ",".join(f"{k}={v}" for k, v in env_vars.items())

        cmd = [
            "gcloud",
            "run",
            "deploy",
            self.service_name,
            f"--image={self.image_name}",
            f"--region={self.region}",
            f"--project={self.project_id}",
            f"--memory={self.memory}",
            f"--cpu={self.cpu}",
            f"--min-instances={self.min_instances}",
            f"--max-instances={self.max_instances}",
            "--platform=managed",
            "--allow-unauthenticated",
            "--port=8000",
            "--timeout=300",
            f"--set-env-vars={env_str}",
        ]

        result = self.run_command(cmd, check=False)

        if result.returncode != 0:
            print("  ✗ デプロイ失敗")
            return False

        print("  ✓ デプロイ完了")
        return True

    def get_service_url(self) -> Optional[str]:
        """サービスURL取得"""
        print("\n[6/6] サービス情報取得...")

        result = self.run_command(
            [
                "gcloud",
                "run",
                "services",
                "describe",
                self.service_name,
                f"--region={self.region}",
                f"--project={self.project_id}",
                "--format=json",
            ],
            check=False,
        )

        if result.returncode != 0:
            print("  ✗ サービス情報取得失敗")
            return None

        try:
            service_info = json.loads(result.stdout)
            url = service_info.get("status", {}).get("url")
            if url:
                print(f"  ✓ サービスURL: {url}")
                return url
        except json.JSONDecodeError:
            pass

        return None

    def print_summary(self, url: Optional[str]):
        """サマリー表示"""
        print("\n" + "=" * 60)
        print("デプロイ完了！")
        print("=" * 60)

        if url:
            print(f"\n🌐 サービスURL: {url}")
            print(f"📖 API ドキュメント: {url}/docs")
            print(f"🏠 ランディングページ: {url}/")

        print("\n次のステップ:")
        print("-" * 40)
        print("1. Secret Manager で機密情報を設定:")
        print(
            f"   gcloud secrets create stripe-secret-key --data-file=-"
        )
        print(
            f"   gcloud secrets create stripe-webhook-secret --data-file=-"
        )
        print(
            f"   gcloud secrets create google-credentials --data-file=credentials/service-account.json"
        )
        print("\n2. Cloud Run にシークレットをマウント:")
        print(f"   gcloud run services update {self.service_name} \\")
        print(f"     --region={self.region} \\")
        print("     --set-secrets=STRIPE_SECRET_KEY=stripe-secret-key:latest")
        print("\n3. カスタムドメイン設定:")
        print(
            f"   gcloud run domain-mappings create --service={self.service_name} "
            f"--domain=YOUR_DOMAIN --region={self.region}"
        )
        print("\n4. Stripe Webhook設定:")
        print(f"   エンドポイント: {url}/api/v1/payment/webhook")
        print()

    def deploy(self) -> bool:
        """デプロイ実行"""
        print("=" * 60)
        print("VisionCraftAI - Cloud Run デプロイ")
        print("=" * 60)
        print(f"プロジェクト: {self.project_id}")
        print(f"リージョン: {self.region}")
        print(f"サービス名: {self.service_name}")

        steps = [
            self.check_prerequisites,
            self.configure_docker,
            self.build_image,
            self.push_image,
            self.deploy_service,
        ]

        for step in steps:
            if not step():
                print("\n✗ デプロイ失敗")
                return False

        url = self.get_service_url()
        self.print_summary(url)

        return True


def main():
    parser = argparse.ArgumentParser(
        description="VisionCraftAI Cloud Run デプロイ"
    )
    parser.add_argument(
        "--project",
        "-p",
        required=True,
        help="Google Cloud プロジェクトID",
    )
    parser.add_argument(
        "--region",
        "-r",
        default="us-central1",
        help="Cloud Run リージョン（デフォルト: us-central1）",
    )
    parser.add_argument(
        "--service",
        "-s",
        default="visioncraftai",
        help="Cloud Run サービス名（デフォルト: visioncraftai）",
    )
    parser.add_argument(
        "--memory",
        default="2Gi",
        help="メモリ割り当て（デフォルト: 2Gi）",
    )
    parser.add_argument(
        "--cpu",
        default="2",
        help="CPU割り当て（デフォルト: 2）",
    )
    parser.add_argument(
        "--min-instances",
        type=int,
        default=0,
        help="最小インスタンス数（デフォルト: 0）",
    )
    parser.add_argument(
        "--max-instances",
        type=int,
        default=10,
        help="最大インスタンス数（デフォルト: 10）",
    )

    args = parser.parse_args()

    deployer = CloudRunDeployer(
        project_id=args.project,
        region=args.region,
        service_name=args.service,
        memory=args.memory,
        cpu=args.cpu,
        min_instances=args.min_instances,
        max_instances=args.max_instances,
    )

    success = deployer.deploy()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
