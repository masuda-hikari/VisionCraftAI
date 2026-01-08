/**
 * VisionCraftAI - フロントエンドJavaScript
 */

const API_BASE = '/api/v1';

// デモモード設定
let isDemoMode = true; // 初期状態はデモモード

// 通知表示
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;

    notification.textContent = message;
    notification.className = `notification ${type} show`;

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// APIキーをローカルストレージから取得
function getApiKey() {
    return localStorage.getItem('vca_api_key') || '';
}

// APIキーを保存
function setApiKey(key) {
    localStorage.setItem('vca_api_key', key);
}

// APIリクエストヘルパー
async function apiRequest(endpoint, options = {}) {
    const apiKey = getApiKey();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (apiKey) {
        headers['X-API-Key'] = apiKey;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'エラーが発生しました' }));
        throw new Error(error.message || error.detail || 'リクエストに失敗しました');
    }

    return response.json();
}

// デモモードで画像生成
async function generateDemoImage(prompt, options = {}) {
    const response = await fetch(`${API_BASE}/demo/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: prompt,
            style: options.style || null
        })
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'エラーが発生しました' }));
        throw new Error(error.message || error.detail || 'デモ生成に失敗しました');
    }

    return response.json();
}

// デモモードかどうかを判定
function shouldUseDemoMode() {
    const apiKey = getApiKey();
    return !apiKey || isDemoMode;
}

// 画像生成
async function generateImage(prompt, options = {}) {
    const btn = document.getElementById('generateBtn');
    const resultContainer = document.getElementById('resultContainer');
    const resultPlaceholder = document.getElementById('resultPlaceholder');
    const resultImage = document.getElementById('resultImage');
    const demoIndicator = document.getElementById('demoIndicator');

    if (!prompt.trim()) {
        showNotification('プロンプトを入力してください', 'error');
        return;
    }

    // ボタンを無効化
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span>生成中...';

    try {
        let result;
        const useDemo = shouldUseDemoMode();

        if (useDemo) {
            // デモモードで生成
            result = await generateDemoImage(prompt, options);

            // 結果表示（デモモード）
            if (result.image_url) {
                resultImage.src = result.image_url;
                resultImage.style.display = 'block';
                resultPlaceholder.style.display = 'none';

                // デモインジケーター表示
                if (demoIndicator) {
                    demoIndicator.style.display = 'block';
                }

                showNotification(`デモ生成完了（${result.generation_time_ms}ms）- APIキーで本格的な画像を生成！`, 'info');

                // マッチしたサンプル情報を表示
                if (result.matched_sample) {
                    console.log(`マッチしたサンプル: ${result.matched_sample}`, result.sample_info);
                }
            }
        } else {
            // 本番APIで生成
            const requestBody = {
                prompt: prompt,
                width: parseInt(options.width) || 1024,
                height: parseInt(options.height) || 1024,
                style: options.style || null
            };

            result = await apiRequest('/generate', {
                method: 'POST',
                body: JSON.stringify(requestBody)
            });

            // 結果表示
            if (result.image_base64) {
                resultImage.src = `data:image/png;base64,${result.image_base64}`;
                resultImage.style.display = 'block';
                resultPlaceholder.style.display = 'none';
                showNotification('画像を生成しました！');
            } else if (result.image_url) {
                resultImage.src = result.image_url;
                resultImage.style.display = 'block';
                resultPlaceholder.style.display = 'none';
                showNotification('画像を生成しました！');
            }

            // デモインジケーター非表示
            if (demoIndicator) {
                demoIndicator.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Generation error:', error);

        // エラー時はデモモードにフォールバック
        if (!shouldUseDemoMode()) {
            console.log('本番APIエラー、デモモードにフォールバック');
            isDemoMode = true;
            try {
                const demoResult = await generateDemoImage(prompt, options);
                if (demoResult.image_url) {
                    resultImage.src = demoResult.image_url;
                    resultImage.style.display = 'block';
                    resultPlaceholder.style.display = 'none';
                    if (demoIndicator) demoIndicator.style.display = 'block';
                    showNotification('API接続エラー: デモモードで表示しています', 'warning');
                    return;
                }
            } catch (demoError) {
                console.error('Demo fallback error:', demoError);
            }
        }

        showNotification(error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '画像を生成';
    }
}

// APIキー作成
async function createApiKey(tier = 'free', name = 'Web App') {
    try {
        const result = await fetch(`${API_BASE}/auth/keys`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tier, name })
        }).then(r => r.json());

        if (result.api_key) {
            setApiKey(result.api_key);
            showNotification('APIキーを作成しました！');
            return result.api_key;
        }
    } catch (error) {
        console.error('API Key creation error:', error);
        showNotification('APIキーの作成に失敗しました', 'error');
    }
    return null;
}

// クォータ確認
async function checkQuota() {
    try {
        const quota = await apiRequest('/auth/quota');
        return quota;
    } catch (error) {
        console.error('Quota check error:', error);
        return null;
    }
}

// プラン一覧取得
async function getPlans() {
    try {
        const plans = await fetch(`${API_BASE}/payment/plans`).then(r => r.json());
        return plans;
    } catch (error) {
        console.error('Plans fetch error:', error);
        return [];
    }
}

// サブスクリプション作成
async function createSubscription(email, planId) {
    try {
        const result = await apiRequest('/payment/subscriptions', {
            method: 'POST',
            body: JSON.stringify({ email, plan_id: planId })
        });

        if (result.checkout_url) {
            // Stripeチェックアウトにリダイレクト
            window.location.href = result.checkout_url;
        } else if (result.status === 'active') {
            showNotification('無料プランが有効化されました！');
        }

        return result;
    } catch (error) {
        console.error('Subscription error:', error);
        showNotification(error.message, 'error');
        return null;
    }
}

// デモモードUIの更新
function updateDemoModeUI() {
    const demoModeToggle = document.getElementById('demoModeToggle');
    const demoModeLabel = document.getElementById('demoModeLabel');
    const apiKey = getApiKey();

    // APIキーがあればデモモードを自動的にオフに
    if (apiKey && apiKey.startsWith('vca_')) {
        isDemoMode = false;
    }

    if (demoModeToggle) {
        demoModeToggle.checked = !isDemoMode;
    }

    if (demoModeLabel) {
        demoModeLabel.textContent = isDemoMode ? 'デモモード' : '本番モード';
    }
}

// ページ初期化
document.addEventListener('DOMContentLoaded', () => {
    // APIキー入力フィールドの初期化
    const apiKeyInput = document.getElementById('apiKeyInput');
    if (apiKeyInput) {
        apiKeyInput.value = getApiKey();
        apiKeyInput.addEventListener('change', (e) => {
            setApiKey(e.target.value);
            // APIキーが設定されたらデモモードを解除
            if (e.target.value && e.target.value.startsWith('vca_')) {
                isDemoMode = false;
                updateDemoModeUI();
            }
            showNotification('APIキーを保存しました');
        });
    }

    // デモモードトグルの初期化
    const demoModeToggle = document.getElementById('demoModeToggle');
    if (demoModeToggle) {
        demoModeToggle.addEventListener('change', (e) => {
            isDemoMode = !e.target.checked;
            updateDemoModeUI();
            showNotification(isDemoMode ? 'デモモードに切り替えました' : '本番モードに切り替えました', 'info');
        });
    }

    // 初期UI更新
    updateDemoModeUI();

    // 生成ボタンのイベント
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', () => {
            const prompt = document.getElementById('promptInput').value;
            const width = document.getElementById('widthSelect')?.value || 1024;
            const height = document.getElementById('heightSelect')?.value || 1024;
            const style = document.getElementById('styleSelect')?.value || null;

            generateImage(prompt, { width, height, style });
        });
    }

    // 新規APIキー作成ボタン
    const createKeyBtn = document.getElementById('createKeyBtn');
    if (createKeyBtn) {
        createKeyBtn.addEventListener('click', async () => {
            const key = await createApiKey();
            if (key && apiKeyInput) {
                apiKeyInput.value = key;
            }
        });
    }

    // プランボタンのイベント
    document.querySelectorAll('[data-plan]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const planId = btn.dataset.plan;
            const email = prompt('メールアドレスを入力してください:');
            if (email) {
                await createSubscription(email, planId);
            }
        });
    });

    // スムーズスクロール
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// エクスポート（モジュールとして使う場合）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generateImage,
        generateDemoImage,
        createApiKey,
        checkQuota,
        getPlans,
        createSubscription,
        updateDemoModeUI
    };
}
