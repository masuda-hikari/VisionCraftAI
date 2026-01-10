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

// 現在生成中の画像データ（ライトボックス連携用）
let currentGeneratedImage = null;

// 画像生成
async function generateImage(prompt, options = {}) {
    const btn = document.getElementById('generateBtn');
    const resultContainer = document.getElementById('resultContainer');
    const resultPlaceholder = document.getElementById('resultPlaceholder');
    const resultImage = document.getElementById('resultImage');
    const resultActions = document.getElementById('resultActions');
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
        const width = parseInt(options.width) || 1024;
        const height = parseInt(options.height) || 1024;

        if (useDemo) {
            // デモモードで生成
            result = await generateDemoImage(prompt, options);

            // 結果表示（デモモード）
            if (result.image_url) {
                resultImage.src = result.image_url;
                resultImage.style.display = 'block';
                resultPlaceholder.style.display = 'none';
                if (resultActions) resultActions.style.display = 'flex';

                // 画像データを保存
                currentGeneratedImage = {
                    src: result.image_url,
                    prompt: prompt,
                    size: `${width}x${height}`,
                    time: result.generation_time_ms,
                    style: options.style
                };

                // ギャラリーに追加
                if (typeof imageGallery !== 'undefined' && imageGallery) {
                    imageGallery.addImage(currentGeneratedImage);
                }

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
                width: width,
                height: height,
                style: options.style || null
            };

            result = await apiRequest('/generate', {
                method: 'POST',
                body: JSON.stringify(requestBody)
            });

            // 結果表示
            let imageSrc = null;
            if (result.image_base64) {
                imageSrc = `data:image/png;base64,${result.image_base64}`;
            } else if (result.image_url) {
                imageSrc = result.image_url;
            }

            if (imageSrc) {
                resultImage.src = imageSrc;
                resultImage.style.display = 'block';
                resultPlaceholder.style.display = 'none';
                if (resultActions) resultActions.style.display = 'flex';

                // 画像データを保存
                currentGeneratedImage = {
                    src: imageSrc,
                    prompt: prompt,
                    size: `${width}x${height}`,
                    time: result.generation_time_ms,
                    style: options.style
                };

                // ギャラリーに追加
                if (typeof imageGallery !== 'undefined' && imageGallery) {
                    imageGallery.addImage(currentGeneratedImage);
                }

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
                    if (resultActions) resultActions.style.display = 'flex';
                    if (demoIndicator) demoIndicator.style.display = 'block';

                    currentGeneratedImage = {
                        src: demoResult.image_url,
                        prompt: prompt,
                        size: `${options.width || 1024}x${options.height || 1024}`,
                        time: demoResult.generation_time_ms,
                        style: options.style
                    };

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

// 画像をダウンロード
async function downloadCurrentImage() {
    if (!currentGeneratedImage || !currentGeneratedImage.src) {
        showNotification('ダウンロードする画像がありません', 'error');
        return;
    }

    try {
        const response = await fetch(currentGeneratedImage.src);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `visioncraftai_${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showNotification('画像をダウンロードしました');
    } catch (error) {
        console.error('Download error:', error);
        showNotification('ダウンロードに失敗しました', 'error');
    }
}

// ライトボックスで表示
function viewImageInLightbox() {
    if (!currentGeneratedImage) {
        showNotification('表示する画像がありません', 'error');
        return;
    }

    if (typeof imageGallery !== 'undefined' && imageGallery && imageGallery.lightbox) {
        imageGallery.lightbox.open(currentGeneratedImage);
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

// 現在の課金間隔（グローバル状態）
let currentBillingInterval = 'monthly';

// サブスクリプション作成
async function createSubscription(email, planId) {
    try {
        const result = await apiRequest('/payment/subscriptions', {
            method: 'POST',
            body: JSON.stringify({
                email,
                plan_id: planId,
                billing_interval: currentBillingInterval
            })
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

// 価格表示を更新
function updatePricingDisplay(isYearly) {
    const priceElements = document.querySelectorAll('.pricing-card .price');
    const monthlyLabel = document.getElementById('monthlyLabel');
    const yearlyLabel = document.getElementById('yearlyLabel');
    const billingBadge = document.querySelector('.billing-badge');

    // ラベルのアクティブ状態を更新
    if (monthlyLabel) {
        monthlyLabel.classList.toggle('active', !isYearly);
    }
    if (yearlyLabel) {
        yearlyLabel.classList.toggle('active', isYearly);
    }

    // 「2ヶ月分お得」バッジの表示切替
    if (billingBadge) {
        billingBadge.classList.toggle('visible', isYearly);
    }

    // 価格を更新
    priceElements.forEach(priceEl => {
        const monthly = parseFloat(priceEl.dataset.monthly);
        const yearly = parseFloat(priceEl.dataset.yearly);

        // アニメーション効果
        priceEl.classList.add('updating');
        setTimeout(() => {
            if (isYearly) {
                if (yearly === 0) {
                    priceEl.innerHTML = '$0<span>/月</span>';
                } else {
                    // 年額を月あたりで表示
                    const monthlyEquivalent = (yearly / 12).toFixed(2);
                    const savings = Math.round((1 - (yearly / (monthly * 12))) * 100);
                    priceEl.innerHTML = `$${monthlyEquivalent}<span>/月</span>`;

                    // 節約額バッジを追加または更新
                    let savingsBadge = priceEl.parentElement.querySelector('.savings-badge');
                    if (!savingsBadge) {
                        savingsBadge = document.createElement('span');
                        savingsBadge.className = 'savings-badge';
                        priceEl.parentElement.insertBefore(savingsBadge, priceEl.nextSibling);
                    }
                    savingsBadge.textContent = `${savings}% OFF`;
                    savingsBadge.classList.add('visible');
                }
            } else {
                priceEl.innerHTML = `$${monthly}<span>/月</span>`;

                // 節約額バッジを非表示
                const savingsBadge = priceEl.parentElement.querySelector('.savings-badge');
                if (savingsBadge) {
                    savingsBadge.classList.remove('visible');
                }
            }
            priceEl.classList.remove('updating');
        }, 150);
    });

    // 課金間隔を更新
    currentBillingInterval = isYearly ? 'yearly' : 'monthly';
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

    // 月額/年額切り替えトグルの初期化
    const billingToggle = document.getElementById('billingToggle');
    if (billingToggle) {
        // 初期状態を設定（月額）
        const monthlyLabel = document.getElementById('monthlyLabel');
        if (monthlyLabel) {
            monthlyLabel.classList.add('active');
        }

        billingToggle.addEventListener('change', (e) => {
            updatePricingDisplay(e.target.checked);
        });
    }

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

    // 拡大表示ボタン
    const viewFullBtn = document.getElementById('viewFullBtn');
    if (viewFullBtn) {
        viewFullBtn.addEventListener('click', viewImageInLightbox);
    }

    // ダウンロードボタン
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadCurrentImage);
    }

    // 生成画像クリックでも拡大
    const resultImage = document.getElementById('resultImage');
    if (resultImage) {
        resultImage.addEventListener('click', viewImageInLightbox);
        resultImage.style.cursor = 'pointer';
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

            // モバイルメニューを閉じる
            const navLinks = document.getElementById('navLinks');
            const mobileMenuBtn = document.getElementById('mobileMenuBtn');
            if (navLinks && mobileMenuBtn) {
                navLinks.classList.remove('active');
                mobileMenuBtn.classList.remove('active');
            }
        });
    });

    // モバイルメニュートグル
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');

    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenuBtn.classList.toggle('active');
            navLinks.classList.toggle('active');
        });

        // メニュー外クリックで閉じる
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.navbar')) {
                mobileMenuBtn.classList.remove('active');
                navLinks.classList.remove('active');
            }
        });
    }
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
