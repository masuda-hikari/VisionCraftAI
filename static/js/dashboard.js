/**
 * VisionCraftAI - ダッシュボード JavaScript
 * ユーザーダッシュボードの機能を提供
 */

// API Base URL
const API_BASE = '/api/v1';

// ローカルストレージキー
const STORAGE_KEY = 'vca_api_key';

// 現在のAPIキー
let currentApiKey = null;

// DOM要素
const loginOverlay = document.getElementById('loginOverlay');
const dashboardMain = document.getElementById('dashboardMain');
const loginForm = document.getElementById('loginForm');
const apiKeyInput = document.getElementById('apiKeyInput');
const logoutBtn = document.getElementById('logoutBtn');
const notification = document.getElementById('notification');

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    // 保存されたAPIキーがあれば自動ログイン
    const savedKey = localStorage.getItem(STORAGE_KEY);
    if (savedKey) {
        currentApiKey = savedKey;
        verifyAndLogin(savedKey);
    }

    // イベントリスナー設定
    setupEventListeners();
});

/**
 * イベントリスナーの設定
 */
function setupEventListeners() {
    // ログインフォーム
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const apiKey = apiKeyInput.value.trim();
        if (apiKey) {
            await verifyAndLogin(apiKey);
        }
    });

    // ログアウト
    logoutBtn.addEventListener('click', logout);

    // タブ切り替え
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });

    // APIキー作成
    document.getElementById('createApiKeyBtn')?.addEventListener('click', showCreateKeyModal);
    document.getElementById('cancelCreateKey')?.addEventListener('click', hideCreateKeyModal);
    document.getElementById('createKeyForm')?.addEventListener('submit', createApiKey);
    document.getElementById('closeShowKeyModal')?.addEventListener('click', hideShowKeyModal);
    document.getElementById('copyKeyBtn')?.addEventListener('click', copyNewKey);

    // クレジットパッケージ購入
    document.querySelectorAll('.credit-package button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const pkg = e.target.closest('.credit-package');
            if (pkg) {
                purchaseCredits(pkg.dataset.package);
            }
        });
    });
}

/**
 * APIキーを検証してログイン
 */
async function verifyAndLogin(apiKey) {
    try {
        const response = await fetch(`${API_BASE}/auth/verify`, {
            headers: { 'X-API-Key': apiKey }
        });

        if (!response.ok) {
            throw new Error('無効なAPIキーです');
        }

        const data = await response.json();

        // ログイン成功
        currentApiKey = apiKey;
        localStorage.setItem(STORAGE_KEY, apiKey);

        // UI更新
        loginOverlay.style.display = 'none';
        dashboardMain.style.display = 'block';

        // ダッシュボードデータ読み込み
        await loadDashboardData();

        showNotification('ログインしました', 'success');
    } catch (error) {
        showNotification(error.message, 'error');
        localStorage.removeItem(STORAGE_KEY);
    }
}

/**
 * ログアウト
 */
function logout() {
    currentApiKey = null;
    localStorage.removeItem(STORAGE_KEY);
    loginOverlay.style.display = 'flex';
    dashboardMain.style.display = 'none';
    apiKeyInput.value = '';
    showNotification('ログアウトしました', 'success');
}

/**
 * タブ切り替え
 */
function switchTab(tabId) {
    // タブボタン更新
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });

    // タブコンテンツ更新
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabId}`);
    });

    // タブ固有のデータ読み込み
    switch (tabId) {
        case 'usage':
            loadUsageData();
            break;
        case 'apikeys':
            loadApiKeys();
            break;
        case 'credits':
            loadCreditData();
            break;
    }
}

/**
 * ダッシュボードデータの読み込み
 */
async function loadDashboardData() {
    try {
        // 並列でデータ取得
        const [keyInfo, quota, subscription, creditBalance] = await Promise.all([
            fetchApi('/auth/keys/me'),
            fetchApi('/auth/quota'),
            fetchApi('/payment/subscriptions/me'),
            fetchApi('/payment/credits/balance')
        ]);

        // ユーザー情報更新
        updateUserInfo(keyInfo, subscription);

        // KPIカード更新
        updateKpiCards(quota, creditBalance);

        // サブスクリプション情報更新
        updateSubscriptionInfo(subscription);

    } catch (error) {
        console.error('ダッシュボードデータ取得エラー:', error);
    }
}

/**
 * ユーザー情報の更新
 */
function updateUserInfo(keyInfo, subscription) {
    const tierBadge = document.getElementById('tierBadge');
    const userId = document.getElementById('userId');

    if (tierBadge && keyInfo) {
        const tier = keyInfo.tier || 'free';
        tierBadge.textContent = tier.charAt(0).toUpperCase() + tier.slice(1);
        tierBadge.className = `tier-badge ${tier}`;
    }

    if (userId && keyInfo) {
        userId.textContent = keyInfo.key_id ? `ID: ${keyInfo.key_id.substring(0, 12)}...` : '';
    }
}

/**
 * KPIカードの更新
 */
function updateKpiCards(quota, creditBalance) {
    if (quota) {
        // 月間使用量
        document.getElementById('monthlyUsed').textContent = quota.monthly_used || 0;
        document.getElementById('monthlyLimit').textContent = `/ ${quota.monthly_limit || '-'} 枚`;
        const monthlyProgress = quota.monthly_limit ? (quota.monthly_used / quota.monthly_limit) * 100 : 0;
        document.getElementById('monthlyProgress').style.width = `${Math.min(monthlyProgress, 100)}%`;

        // 日間使用量
        document.getElementById('dailyUsed').textContent = quota.daily_used || 0;
        document.getElementById('dailyLimit').textContent = `/ ${quota.daily_limit || '-'} 枚`;
        const dailyProgress = quota.daily_limit ? (quota.daily_used / quota.daily_limit) * 100 : 0;
        document.getElementById('dailyProgress').style.width = `${Math.min(dailyProgress, 100)}%`;
    }

    if (creditBalance) {
        // クレジット残高
        document.getElementById('creditBalance').textContent = creditBalance.total_balance || 0;
        document.getElementById('bonusCredits').textContent = `ボーナス: ${creditBalance.bonus_balance || 0}`;
    }
}

/**
 * サブスクリプション情報の更新
 */
function updateSubscriptionInfo(subscription) {
    if (!subscription) return;

    document.getElementById('planName').textContent = subscription.plan_name || 'Free';
    document.getElementById('planStatus').textContent = subscription.is_active ? 'アクティブ' : '非アクティブ';
    document.getElementById('planStatus').style.color = subscription.is_active ? 'var(--success)' : 'var(--error)';

    // プラン詳細
    const planLimits = {
        'free': { monthly: '5枚', resolution: '512x512' },
        'basic': { monthly: '100枚', resolution: '1024x1024' },
        'pro': { monthly: '500枚', resolution: '2048x2048' },
        'enterprise': { monthly: '無制限', resolution: '4096x4096' }
    };
    const limits = planLimits[subscription.plan_id] || planLimits.free;
    document.getElementById('planMonthlyLimit').textContent = limits.monthly;
    document.getElementById('planResolution').textContent = limits.resolution;

    // 次回更新日
    if (subscription.current_period_end) {
        const date = new Date(subscription.current_period_end);
        document.getElementById('planRenewal').textContent = date.toLocaleDateString('ja-JP');
    } else {
        document.getElementById('planRenewal').textContent = '-';
    }

    // キャンセルボタン表示制御
    const cancelBtn = document.getElementById('cancelSubscriptionBtn');
    if (cancelBtn) {
        cancelBtn.style.display = subscription.plan_id !== 'free' ? 'inline-block' : 'none';
    }
}

/**
 * 使用量データの読み込み
 */
async function loadUsageData() {
    try {
        const [usage, rateLimit] = await Promise.all([
            fetchApi('/usage'),
            fetchApi('/auth/rate-limit')
        ]);

        if (usage) {
            document.getElementById('totalGenerations').textContent = usage.total_requests || 0;
            document.getElementById('successRate').textContent = usage.success_rate
                ? `${(usage.success_rate * 100).toFixed(1)}%`
                : '-';
            document.getElementById('avgResponseTime').textContent = usage.average_time
                ? `${usage.average_time.toFixed(2)}s`
                : '-';
            document.getElementById('estimatedCost').textContent = usage.total_cost
                ? `$${usage.total_cost.toFixed(2)}`
                : '-';
        }

        if (rateLimit) {
            document.getElementById('currentRequests').textContent = rateLimit.current_count || 0;
            document.getElementById('remainingRequests').textContent = rateLimit.remaining || 0;
            document.getElementById('rateLimitReset').textContent = rateLimit.reset_at
                ? new Date(rateLimit.reset_at).toLocaleTimeString('ja-JP')
                : '-';
        }
    } catch (error) {
        console.error('使用量データ取得エラー:', error);
    }
}

/**
 * APIキー一覧の読み込み
 */
async function loadApiKeys() {
    try {
        const data = await fetchApi('/auth/keys');
        const list = document.getElementById('apiKeysList');

        if (!data || !data.keys || data.keys.length === 0) {
            list.innerHTML = '<p class="no-data">APIキーがありません</p>';
            document.getElementById('apiKeyCount').textContent = '0';
            return;
        }

        document.getElementById('apiKeyCount').textContent = data.keys.length;

        list.innerHTML = data.keys.map(key => `
            <div class="api-key-item" data-key-id="${key.key_id}">
                <div class="api-key-info">
                    <div class="api-key-name">${key.name || '名前なし'}</div>
                    <div class="api-key-id">${key.key_id}</div>
                    <div class="api-key-meta">
                        <span>プラン: ${key.tier}</span>
                        <span>作成: ${new Date(key.created_at).toLocaleDateString('ja-JP')}</span>
                        ${key.last_used_at ? `<span>最終使用: ${new Date(key.last_used_at).toLocaleDateString('ja-JP')}</span>` : ''}
                    </div>
                </div>
                <div class="api-key-actions">
                    <button onclick="revokeApiKey('${key.key_id}')" class="danger">無効化</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('APIキー取得エラー:', error);
    }
}

/**
 * クレジットデータの読み込み
 */
async function loadCreditData() {
    try {
        const [balance, transactions] = await Promise.all([
            fetchApi('/payment/credits/balance'),
            fetchApi('/payment/credits/transactions?limit=20')
        ]);

        if (balance) {
            document.getElementById('creditBalanceLarge').textContent = balance.balance || 0;
            document.getElementById('bonusBalanceLarge').textContent = balance.bonus_balance || 0;
        }

        const list = document.getElementById('transactionsList');
        if (!transactions || !transactions.transactions || transactions.transactions.length === 0) {
            list.innerHTML = '<p class="no-data">取引履歴がありません</p>';
            return;
        }

        list.innerHTML = transactions.transactions.map(tx => {
            const isPositive = tx.amount > 0;
            const typeLabel = {
                'purchase': '購入',
                'bonus': 'ボーナス',
                'usage': '使用',
                'refund': '返金',
                'subscription': 'サブスクリプション'
            }[tx.transaction_type] || tx.transaction_type;

            return `
                <div class="transaction-item">
                    <div class="transaction-info">
                        <div class="transaction-type">${typeLabel}</div>
                        <div class="transaction-date">${new Date(tx.created_at).toLocaleString('ja-JP')}</div>
                    </div>
                    <div class="transaction-amount ${isPositive ? 'positive' : 'negative'}">
                        ${isPositive ? '+' : ''}${tx.amount}
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('クレジットデータ取得エラー:', error);
    }
}

/**
 * APIキー作成モーダル表示
 */
function showCreateKeyModal() {
    document.getElementById('createKeyModal').style.display = 'flex';
}

/**
 * APIキー作成モーダル非表示
 */
function hideCreateKeyModal() {
    document.getElementById('createKeyModal').style.display = 'none';
    document.getElementById('createKeyForm').reset();
}

/**
 * APIキー表示モーダル非表示
 */
function hideShowKeyModal() {
    document.getElementById('showKeyModal').style.display = 'none';
}

/**
 * 新しいAPIキーをコピー
 */
function copyNewKey() {
    const keyText = document.getElementById('newApiKey').textContent;
    navigator.clipboard.writeText(keyText).then(() => {
        showNotification('APIキーをコピーしました', 'success');
    });
}

/**
 * APIキー作成
 */
async function createApiKey(e) {
    e.preventDefault();

    const name = document.getElementById('keyName').value.trim();
    const description = document.getElementById('keyDescription').value.trim();

    try {
        const response = await fetch(`${API_BASE}/auth/keys`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': currentApiKey
            },
            body: JSON.stringify({
                tier: 'free',  // 新規キーはFreeプランで作成
                name: name || undefined,
                description: description || undefined
            })
        });

        if (!response.ok) {
            throw new Error('APIキーの作成に失敗しました');
        }

        const data = await response.json();

        // 作成モーダルを閉じて、キー表示モーダルを開く
        hideCreateKeyModal();
        document.getElementById('newApiKey').textContent = data.api_key;
        document.getElementById('showKeyModal').style.display = 'flex';

        // キー一覧を更新
        loadApiKeys();

    } catch (error) {
        showNotification(error.message, 'error');
    }
}

/**
 * APIキー無効化
 */
async function revokeApiKey(keyId) {
    if (!confirm('このAPIキーを無効化しますか？')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/keys/${keyId}`, {
            method: 'DELETE',
            headers: { 'X-API-Key': currentApiKey }
        });

        if (!response.ok) {
            throw new Error('APIキーの無効化に失敗しました');
        }

        showNotification('APIキーを無効化しました', 'success');
        loadApiKeys();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

/**
 * クレジット購入
 */
async function purchaseCredits(packageId) {
    try {
        const response = await fetch(`${API_BASE}/payment/credits/purchase`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': currentApiKey
            },
            body: JSON.stringify({ package_id: packageId })
        });

        if (!response.ok) {
            throw new Error('購入処理の開始に失敗しました');
        }

        const data = await response.json();

        // Stripe Checkoutにリダイレクト（本番環境）
        // デモ環境ではメッセージ表示
        if (data.checkout_url) {
            window.location.href = data.checkout_url;
        } else {
            showNotification('決済ページの準備中です。しばらくお待ちください。', 'success');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

/**
 * API呼び出しヘルパー
 */
async function fetchApi(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: { 'X-API-Key': currentApiKey }
    });

    if (!response.ok) {
        if (response.status === 401) {
            logout();
            throw new Error('セッションが切れました。再度ログインしてください。');
        }
        return null;
    }

    return response.json();
}

/**
 * 通知表示
 */
function showNotification(message, type = 'info') {
    notification.textContent = message;
    notification.className = `notification show ${type}`;

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// グローバル関数として公開
window.revokeApiKey = revokeApiKey;
