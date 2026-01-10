/**
 * VisionCraftAI - Cloudflare Workers エントリーポイント
 *
 * 注意: Cloudflare WorkersはPythonを直接サポートしないため、
 * このファイルは静的ファイル配信とAPIプロキシとして機能します。
 *
 * フルスタック機能を使用する場合は、以下のオプションを推奨:
 * 1. Cloudflare Pages + Functions
 * 2. Vercel (Python対応)
 * 3. Google Cloud Run
 */

// 静的ファイルのMIMEタイプ
const MIME_TYPES = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

// CORSヘッダー
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, X-API-Key, Authorization',
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // OPTIONSリクエスト（CORS preflight）
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: CORS_HEADERS,
      });
    }

    // 静的ファイル配信
    if (path.startsWith('/static/')) {
      return handleStaticFile(request, env, path);
    }

    // APIエンドポイント - バックエンドにプロキシ
    if (path.startsWith('/api/')) {
      return handleApiProxy(request, env, path);
    }

    // ルートパス - index.htmlを返す
    if (path === '/' || path === '/index.html') {
      return handleStaticFile(request, env, '/static/index.html');
    }

    // 404
    return new Response('Not Found', { status: 404 });
  },
};

/**
 * 静的ファイルを返す
 */
async function handleStaticFile(request, env, path) {
  try {
    // Cloudflare Pagesと連携している場合、KVまたはR2から取得
    // ここではサンプルとしてフォールバックレスポンスを返す

    const ext = path.substring(path.lastIndexOf('.'));
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    // 静的アセットがバインドされている場合
    if (env.ASSETS) {
      const response = await env.ASSETS.fetch(request);
      return new Response(response.body, {
        status: response.status,
        headers: {
          ...Object.fromEntries(response.headers),
          'Content-Type': contentType,
          'Cache-Control': 'public, max-age=31536000, immutable',
        },
      });
    }

    // フォールバック: デモHTML
    if (path === '/static/index.html' || path === '/') {
      return new Response(getDemoHtml(), {
        status: 200,
        headers: {
          'Content-Type': 'text/html',
        },
      });
    }

    return new Response('Static file not found', { status: 404 });
  } catch (error) {
    return new Response('Error loading static file', { status: 500 });
  }
}

/**
 * APIプロキシ（バックエンドが別の場所で稼働している場合）
 */
async function handleApiProxy(request, env, path) {
  // バックエンドURLが設定されている場合はプロキシ
  const backendUrl = env.BACKEND_URL || null;

  if (backendUrl) {
    const proxyUrl = new URL(path, backendUrl);
    proxyUrl.search = new URL(request.url).search;

    const proxyRequest = new Request(proxyUrl.toString(), {
      method: request.method,
      headers: request.headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : null,
    });

    const response = await fetch(proxyRequest);

    return new Response(response.body, {
      status: response.status,
      headers: {
        ...Object.fromEntries(response.headers),
        ...CORS_HEADERS,
      },
    });
  }

  // バックエンドがない場合はデモレスポンス
  if (path === '/api/v1/health') {
    return jsonResponse({ status: 'healthy', mode: 'demo', platform: 'cloudflare-workers' });
  }

  if (path === '/api/v1/demo/info') {
    return jsonResponse({
      demo_mode: true,
      platform: 'cloudflare-workers',
      message: 'VisionCraftAI Demo Mode - Cloudflare Workers',
    });
  }

  return jsonResponse({ error: 'API endpoint not available in demo mode' }, 503);
}

/**
 * JSONレスポンスヘルパー
 */
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...CORS_HEADERS,
    },
  });
}

/**
 * デモ用HTMLページ
 */
function getDemoHtml() {
  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VisionCraftAI - Cloudflare Workers Demo</title>
  <style>
    :root { --primary: #6366f1; --bg: #0f172a; --text: #f8fafc; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
    .container { text-align: center; padding: 2rem; }
    h1 { font-size: 2.5rem; background: linear-gradient(135deg, var(--primary), #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem; }
    p { color: #94a3b8; margin-bottom: 2rem; }
    .badge { display: inline-block; background: var(--primary); padding: 0.5rem 1rem; border-radius: 9999px; font-size: 0.875rem; }
    a { color: var(--primary); text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <h1>VisionCraftAI</h1>
    <p>AI Image Generation Platform</p>
    <p class="badge">Cloudflare Workers Demo</p>
    <p style="margin-top: 2rem;">
      <a href="/api/v1/health">Health Check</a> |
      <a href="/api/v1/demo/info">Demo Info</a>
    </p>
  </div>
</body>
</html>`;
}
