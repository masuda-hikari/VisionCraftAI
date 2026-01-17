#!/usr/bin/env python3
"""
Cloudflare Tunnel 自動セットアップスクリプト

Cloudflare Tunnelを使用してローカルデモサーバーを無料でインターネットに公開します。

使用方法:
    1. Cloudflare アカウントを作成（無料）: https://dash.cloudflare.com/sign-up
    2. このスクリプトを実行:
       python scripts/setup_cloudflare_tunnel.py

機能:
    - cloudflared の自動インストール確認
    - トンネルの自動作成
    - デモサーバーの自動起動
    - 公開URL の表示

代替手段（cloudflared が利用できない場合）:
    - localtunnel: npm install -g localtunnel && lt --port 8000
    - serveo.net: ssh -R 80:localhost:8000 serveo.net
"""

import subprocess
import sys
import platform
import urllib.request
import zipfile
import os
from pathlib import Path


def check_cloudflared_installed() -> bool:
    """cloudflaredがインストールされているか確認"""
    try:
        result = subprocess.run(
            ["cloudflared", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_cloudflared_windows():
    """Windows用cloudflaredをダウンロード・インストール"""
    print("cloudflared をダウンロード中...")

    # Windowsバイナリをダウンロード
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    bin_dir = Path("bin")
    bin_dir.mkdir(exist_ok=True)

    cloudflared_path = bin_dir / "cloudflared.exe"

    try:
        urllib.request.urlretrieve(url, cloudflared_path)
        print(f"✓ cloudflared をダウンロードしました: {cloudflared_path}")
        return str(cloudflared_path)
    except Exception as e:
        print(f"✗ ダウンロードに失敗しました: {e}")
        return None


def install_cloudflared():
    """cloudflaredをインストール"""
    system = platform.system()

    if system == "Windows":
        return install_cloudflared_windows()
    elif system == "Darwin":  # macOS
        print("macOSの場合は以下のコマンドでインストールしてください:")
        print("  brew install cloudflare/cloudflare/cloudflared")
        return None
    elif system == "Linux":
        print("Linuxの場合は以下のコマンドでインストールしてください:")
        print("  wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64")
        print("  chmod +x cloudflared-linux-amd64")
        print("  sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared")
        return None
    else:
        print(f"未対応のOS: {system}")
        return None


def show_alternative_methods():
    """代替公開方法を表示"""
    print("\n" + "="*60)
    print("  代替公開方法")
    print("="*60)
    print("\n【方法1】localtunnel（Node.js必要）")
    print("  1. npm install -g localtunnel")
    print("  2. python -m src.api.app &")
    print("  3. lt --port 8000")
    print("")
    print("【方法2】serveo.net（SSHトンネル）")
    print("  1. python -m src.api.app &")
    print("  2. ssh -R 80:localhost:8000 serveo.net")
    print("")
    print("【方法3】ngrok（無料枠60分/月）")
    print("  1. https://ngrok.com/ でアカウント作成")
    print("  2. ngrok authtoken YOUR_TOKEN")
    print("  3. python -m src.api.app &")
    print("  4. ngrok http 8000")
    print("")
    print("【方法4】GitHub Pages + Vercel（推奨・完全無料）")
    print("  1. GitHubリポジトリをPublicに変更")
    print("  2. https://vercel.com でGitHub連携")
    print("  3. 自動デプロイ（vercel.json設定済み）")
    print("="*60)


def main():
    """メイン処理"""
    print("="*60)
    print("  VisionCraftAI - Cloudflare Tunnel セットアップ")
    print("="*60)

    # cloudflared 確認
    cloudflared_cmd = "cloudflared"

    if not check_cloudflared_installed():
        print("\n[警告] cloudflared がインストールされていません")
        print("自動インストールを試みます...\n")

        installed_path = install_cloudflared()
        if installed_path:
            cloudflared_cmd = installed_path
        else:
            print("\n✗ 自動インストールに失敗しました")
            show_alternative_methods()
            return 1

    print("\n✓ cloudflared が利用可能です")

    # デモサーバー起動確認
    print("\n[Step 1] デモサーバー起動")
    print("-" * 60)
    print("別のターミナルで以下を実行してください:")
    print("  python -m src.api.app")
    print("")
    input("デモサーバーを起動したら Enter を押してください...")

    # Cloudflare Tunnel 起動
    print("\n[Step 2] Cloudflare Tunnel 起動")
    print("-" * 60)
    print("Cloudflare Tunnel を起動します...")
    print("公開URLが表示されます（数秒お待ちください）\n")

    try:
        # トンネル起動（http://localhost:8000 を公開）
        subprocess.run(
            [cloudflared_cmd, "tunnel", "--url", "http://localhost:8000"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"\n✗ トンネル起動に失敗しました: {e}")
        show_alternative_methods()
        return 1
    except KeyboardInterrupt:
        print("\n\nトンネルを終了しました")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
