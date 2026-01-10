/**
 * VisionCraftAI - SNS共有・バイラル機能
 * Twitter/Facebook/LINE等へのワンクリック共有
 */

class ShareManager {
    constructor() {
        this.serviceName = 'VisionCraftAI';
        this.siteUrl = window.location.origin;
        this.hashtags = ['VisionCraftAI', 'AI画像生成', 'AIart'];
    }

    /**
     * 共有URL生成
     * @param {string} platform - プラットフォーム名
     * @param {Object} options - 共有オプション
     * @returns {string} 共有URL
     */
    getShareUrl(platform, options = {}) {
        const text = options.text || 'VisionCraftAIで画像を生成しました！';
        const url = options.url || window.location.href;
        const hashtags = options.hashtags || this.hashtags;

        switch (platform) {
            case 'twitter':
                return `https://twitter.com/intent/tweet?` +
                    `text=${encodeURIComponent(text)}` +
                    `&url=${encodeURIComponent(url)}` +
                    `&hashtags=${encodeURIComponent(hashtags.join(','))}`;

            case 'facebook':
                return `https://www.facebook.com/sharer/sharer.php?` +
                    `u=${encodeURIComponent(url)}` +
                    `&quote=${encodeURIComponent(text)}`;

            case 'line':
                return `https://social-plugins.line.me/lineit/share?` +
                    `url=${encodeURIComponent(url)}` +
                    `&text=${encodeURIComponent(text)}`;

            case 'linkedin':
                return `https://www.linkedin.com/sharing/share-offsite/?` +
                    `url=${encodeURIComponent(url)}`;

            case 'pinterest':
                return `https://pinterest.com/pin/create/button/?` +
                    `url=${encodeURIComponent(url)}` +
                    `&description=${encodeURIComponent(text)}` +
                    `&media=${encodeURIComponent(options.imageUrl || '')}`;

            case 'reddit':
                return `https://www.reddit.com/submit?` +
                    `url=${encodeURIComponent(url)}` +
                    `&title=${encodeURIComponent(text)}`;

            case 'telegram':
                return `https://t.me/share/url?` +
                    `url=${encodeURIComponent(url)}` +
                    `&text=${encodeURIComponent(text)}`;

            case 'whatsapp':
                return `https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`;

            default:
                return url;
        }
    }

    /**
     * 共有ウィンドウを開く
     * @param {string} platform - プラットフォーム名
     * @param {Object} options - 共有オプション
     */
    openShare(platform, options = {}) {
        const url = this.getShareUrl(platform, options);
        const width = 600;
        const height = 400;
        const left = (window.innerWidth - width) / 2;
        const top = (window.innerHeight - height) / 2;

        window.open(
            url,
            `share_${platform}`,
            `width=${width},height=${height},left=${left},top=${top},menubar=no,toolbar=no,status=no`
        );
    }

    /**
     * ネイティブ共有（Web Share API）
     * @param {Object} options - 共有オプション
     * @returns {Promise<boolean>} 成功したかどうか
     */
    async nativeShare(options = {}) {
        if (!navigator.share) {
            return false;
        }

        const shareData = {
            title: options.title || this.serviceName,
            text: options.text || 'VisionCraftAIで画像を生成しました！',
            url: options.url || window.location.href
        };

        // 画像ファイルがあれば追加
        if (options.imageBlob && navigator.canShare) {
            const file = new File([options.imageBlob], 'visioncraftai.png', { type: 'image/png' });
            if (navigator.canShare({ files: [file] })) {
                shareData.files = [file];
            }
        }

        try {
            await navigator.share(shareData);
            return true;
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Native share error:', error);
            }
            return false;
        }
    }

    /**
     * 共有テキストを生成
     * @param {Object} imageData - 画像データ
     * @returns {string} 共有テキスト
     */
    generateShareText(imageData) {
        const promptPreview = imageData.prompt ?
            (imageData.prompt.length > 50 ? imageData.prompt.substring(0, 50) + '...' : imageData.prompt) :
            '';

        return promptPreview ?
            `「${promptPreview}」\nVisionCraftAIで生成しました！` :
            'VisionCraftAIでAI画像を生成しました！';
    }

    /**
     * 共有モーダルを表示
     * @param {Object} imageData - 画像データ
     */
    showShareModal(imageData) {
        // 既存のモーダルを削除
        const existing = document.getElementById('shareModal');
        if (existing) {
            existing.remove();
        }

        const shareText = this.generateShareText(imageData);
        const shareUrl = window.location.href;

        const modal = document.createElement('div');
        modal.id = 'shareModal';
        modal.className = 'share-modal-overlay';
        modal.innerHTML = `
            <div class="share-modal">
                <button class="share-modal-close" aria-label="閉じる">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                <h3 class="share-modal-title">画像を共有</h3>

                <div class="share-preview">
                    <img src="${imageData.src}" alt="共有画像" class="share-preview-image">
                    <p class="share-preview-prompt">${imageData.prompt || ''}</p>
                </div>

                <div class="share-buttons">
                    <button class="share-btn share-btn-twitter" data-platform="twitter" aria-label="Twitterで共有">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                        </svg>
                        <span>Twitter</span>
                    </button>
                    <button class="share-btn share-btn-facebook" data-platform="facebook" aria-label="Facebookで共有">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                        </svg>
                        <span>Facebook</span>
                    </button>
                    <button class="share-btn share-btn-line" data-platform="line" aria-label="LINEで共有">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.346 0 .627.285.627.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/>
                        </svg>
                        <span>LINE</span>
                    </button>
                    <button class="share-btn share-btn-pinterest" data-platform="pinterest" aria-label="Pinterestで共有">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.269 1.045-1.004 2.352-1.498 3.146 1.123.345 2.306.535 3.55.535 6.607 0 11.985-5.365 11.985-11.987C23.97 5.39 18.592.026 11.985.026L12.017 0z"/>
                        </svg>
                        <span>Pinterest</span>
                    </button>
                </div>

                <div class="share-link-section">
                    <label>リンクをコピー</label>
                    <div class="share-link-input">
                        <input type="text" value="${shareUrl}" readonly id="shareLinkInput">
                        <button class="share-link-copy" id="shareLinkCopy" aria-label="リンクをコピー">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                        </button>
                    </div>
                </div>

                ${navigator.share ? `
                <button class="share-native-btn" id="shareNativeBtn">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="18" cy="5" r="3"></circle>
                        <circle cx="6" cy="12" r="3"></circle>
                        <circle cx="18" cy="19" r="3"></circle>
                        <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                        <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
                    </svg>
                    その他の方法で共有
                </button>
                ` : ''}
            </div>
        `;

        document.body.appendChild(modal);

        // イベントリスナーを設定
        this.setupModalEvents(modal, imageData, shareText, shareUrl);

        // 表示アニメーション
        requestAnimationFrame(() => {
            modal.classList.add('active');
        });
    }

    /**
     * モーダルのイベントリスナーを設定
     * @param {HTMLElement} modal - モーダル要素
     * @param {Object} imageData - 画像データ
     * @param {string} shareText - 共有テキスト
     * @param {string} shareUrl - 共有URL
     */
    setupModalEvents(modal, imageData, shareText, shareUrl) {
        // 閉じるボタン
        modal.querySelector('.share-modal-close').addEventListener('click', () => {
            this.closeShareModal();
        });

        // オーバーレイクリックで閉じる
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeShareModal();
            }
        });

        // ESCキーで閉じる
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                this.closeShareModal();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);

        // SNS共有ボタン
        modal.querySelectorAll('.share-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const platform = btn.dataset.platform;
                this.openShare(platform, {
                    text: shareText,
                    url: shareUrl,
                    imageUrl: imageData.src
                });

                // 共有イベントを記録（分析用）
                this.trackShare(platform);
            });
        });

        // リンクコピーボタン
        const copyBtn = modal.querySelector('#shareLinkCopy');
        if (copyBtn) {
            copyBtn.addEventListener('click', async () => {
                const input = modal.querySelector('#shareLinkInput');
                try {
                    await navigator.clipboard.writeText(input.value);
                    this.showToast('リンクをコピーしました');
                    copyBtn.classList.add('copied');
                    setTimeout(() => copyBtn.classList.remove('copied'), 2000);
                } catch (error) {
                    // フォールバック
                    input.select();
                    document.execCommand('copy');
                    this.showToast('リンクをコピーしました');
                }
            });
        }

        // ネイティブ共有ボタン
        const nativeBtn = modal.querySelector('#shareNativeBtn');
        if (nativeBtn) {
            nativeBtn.addEventListener('click', async () => {
                const success = await this.nativeShare({
                    title: this.serviceName,
                    text: shareText,
                    url: shareUrl
                });
                if (success) {
                    this.closeShareModal();
                }
            });
        }
    }

    /**
     * 共有モーダルを閉じる
     */
    closeShareModal() {
        const modal = document.getElementById('shareModal');
        if (modal) {
            modal.classList.remove('active');
            setTimeout(() => modal.remove(), 300);
        }
    }

    /**
     * 共有イベントを記録
     * @param {string} platform - プラットフォーム名
     */
    trackShare(platform) {
        // Google Analytics等への送信（実装時）
        console.log(`Share tracked: ${platform}`);

        // カスタムイベント発火
        window.dispatchEvent(new CustomEvent('vca-share', {
            detail: { platform }
        }));
    }

    /**
     * トースト通知を表示
     * @param {string} message - メッセージ
     */
    showToast(message) {
        if (typeof showNotification === 'function') {
            showNotification(message, 'success');
        }
    }
}

// グローバルインスタンス
const shareManager = new ShareManager();

// エクスポート
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ShareManager, shareManager };
}
