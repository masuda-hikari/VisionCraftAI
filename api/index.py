# Vercel Serverless Function エントリーポイント
# FastAPIアプリをVercelにデプロイするためのラッパー

import os
import sys

# パスを追加してsrcモジュールをインポート可能にする
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 環境変数設定（Vercel用デフォルト）
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("STRIPE_TEST_MODE", "true")

from src.api.app import app

# Vercel Serverless Function用のハンドラー
# Vercelは 'app' という名前のASGIアプリを自動検出
handler = app
