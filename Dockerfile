# VisionCraftAI - 本番用Dockerfile
# Python 3.12 ベースイメージ

FROM python:3.14-slim AS base

# 環境変数設定
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# システム依存パッケージインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# ビルドステージ
FROM base AS builder

# 依存関係インストール
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install build && \
    pip install .

# 本番ステージ
FROM base AS production

# 非rootユーザー作成
RUN useradd --create-home --shell /bin/bash appuser

# 依存関係をビルダーからコピー
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリケーションコードをコピー
COPY --chown=appuser:appuser . .

# 出力ディレクトリ作成
RUN mkdir -p /app/outputs /app/data && \
    chown -R appuser:appuser /app/outputs /app/data

# 非rootユーザーに切り替え
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# ポート公開
EXPOSE 8000

# 起動コマンド
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
