/**
 * VisionCraftAI - Service Worker
 * オフライン対応・キャッシュ戦略・PWA機能
 */

const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `visioncraftai-${CACHE_VERSION}`;

// キャッシュするリソース
const STATIC_CACHE = [
    '/',
    '/static/css/style.css',
    '/static/css/lightbox.css',
    '/static/js/app.js',
    '/static/js/lightbox.js',
    '/terms',
    '/privacy',
    '/contact'
];

// APIパスはネットワーク優先
const API_PATHS = [
    '/api/v1/'
];

// インストール時
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_CACHE);
            })
            .then(() => {
                console.log('[SW] Installation complete');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[SW] Installation failed:', error);
            })
    );
});

// アクティブ化時（古いキャッシュを削除）
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name.startsWith('visioncraftai-') && name !== CACHE_NAME)
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[SW] Activation complete');
                return self.clients.claim();
            })
    );
});

// フェッチリクエスト処理
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // APIリクエストはネットワーク優先
    if (API_PATHS.some(path => url.pathname.startsWith(path))) {
        event.respondWith(networkFirst(event.request));
        return;
    }

    // 画像はキャッシュ優先（但し生成画像は除く）
    if (event.request.destination === 'image' && !url.pathname.includes('/api/')) {
        event.respondWith(cacheFirst(event.request));
        return;
    }

    // その他の静的リソースはキャッシュ優先
    if (event.request.method === 'GET' && !url.pathname.startsWith('/api/')) {
        event.respondWith(staleWhileRevalidate(event.request));
        return;
    }

    // それ以外はネットワークリクエスト
    event.respondWith(fetch(event.request));
});

/**
 * ネットワーク優先戦略
 * APIリクエストなど、最新データが必要な場合
 */
async function networkFirst(request) {
    try {
        const response = await fetch(request);
        return response;
    } catch (error) {
        // オフライン時はキャッシュから
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }

        // APIエラー時のフォールバック
        if (request.url.includes('/api/')) {
            return new Response(
                JSON.stringify({
                    error: 'offline',
                    message: 'オフラインです。ネットワーク接続を確認してください。'
                }),
                {
                    status: 503,
                    headers: { 'Content-Type': 'application/json' }
                }
            );
        }

        throw error;
    }
}

/**
 * キャッシュ優先戦略
 * 画像など、変更が少ないリソース
 */
async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) {
        return cached;
    }

    try {
        const response = await fetch(request);

        // 成功レスポンスをキャッシュ
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        // オフライン時のプレースホルダー画像
        return new Response(
            `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
                <rect fill="#1e293b" width="200" height="200"/>
                <text fill="#94a3b8" x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="14">
                    オフライン
                </text>
            </svg>`,
            {
                headers: { 'Content-Type': 'image/svg+xml' }
            }
        );
    }
}

/**
 * Stale-While-Revalidate戦略
 * 静的リソースで、キャッシュを返しつつバックグラウンドで更新
 */
async function staleWhileRevalidate(request) {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);

    // バックグラウンドで更新
    const fetchPromise = fetch(request)
        .then((response) => {
            if (response.ok) {
                cache.put(request, response.clone());
            }
            return response;
        })
        .catch(() => null);

    // キャッシュがあれば即座に返す
    if (cached) {
        return cached;
    }

    // キャッシュがなければネットワークから
    const response = await fetchPromise;
    if (response) {
        return response;
    }

    // オフラインフォールバック
    return offlineFallback(request);
}

/**
 * オフラインフォールバック
 */
function offlineFallback(request) {
    const url = new URL(request.url);

    // HTMLページの場合
    if (request.headers.get('Accept')?.includes('text/html')) {
        return new Response(
            `<!DOCTYPE html>
            <html lang="ja">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>オフライン - VisionCraftAI</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        font-family: 'Inter', sans-serif;
                        background: #0f172a;
                        color: #f8fafc;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                        padding: 20px;
                    }
                    .container { max-width: 400px; }
                    h1 { font-size: 2rem; margin-bottom: 16px; }
                    p { color: #94a3b8; margin-bottom: 24px; }
                    .icon { font-size: 4rem; margin-bottom: 24px; }
                    button {
                        background: linear-gradient(135deg, #6366f1, #8b5cf6);
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-size: 1rem;
                        cursor: pointer;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">📡</div>
                    <h1>オフラインです</h1>
                    <p>インターネット接続を確認してください。接続が回復したら、ページを再読み込みしてください。</p>
                    <button onclick="location.reload()">再読み込み</button>
                </div>
            </body>
            </html>`,
            {
                headers: { 'Content-Type': 'text/html; charset=utf-8' }
            }
        );
    }

    return new Response('オフライン', { status: 503 });
}

// プッシュ通知（将来の拡張用）
self.addEventListener('push', (event) => {
    if (!event.data) return;

    const data = event.data.json();

    const options = {
        body: data.body || '',
        icon: '/static/images/icon-192.png',
        badge: '/static/images/badge-72.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/'
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'VisionCraftAI', options)
    );
});

// 通知クリック
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const url = event.notification.data?.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // 既存のウィンドウがあればフォーカス
                for (const client of clientList) {
                    if (client.url === url && 'focus' in client) {
                        return client.focus();
                    }
                }
                // なければ新しいウィンドウを開く
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});

// バックグラウンド同期（将来の拡張用）
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-generation-queue') {
        event.waitUntil(syncGenerationQueue());
    }
});

async function syncGenerationQueue() {
    // オフライン時にキューに入れた生成リクエストを処理
    console.log('[SW] Syncing generation queue...');
}

console.log('[SW] Service worker loaded');
