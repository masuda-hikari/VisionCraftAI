/**
 * VisionCraftAI - 画像ライトボックス・プレビュー機能
 * 生成画像の拡大表示・ダウンロード・共有機能
 */

class ImageLightbox {
    constructor() {
        this.isOpen = false;
        this.currentImage = null;
        this.overlay = null;
        this.init();
    }

    /**
     * ライトボックスUIを初期化
     */
    init() {
        // オーバーレイ要素を作成
        this.overlay = document.createElement('div');
        this.overlay.className = 'lightbox-overlay';
        this.overlay.innerHTML = `
            <div class="lightbox-container">
                <button class="lightbox-close" aria-label="閉じる">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                <div class="lightbox-content">
                    <img class="lightbox-image" src="" alt="拡大画像">
                </div>
                <div class="lightbox-info">
                    <p class="lightbox-prompt"></p>
                    <div class="lightbox-meta">
                        <span class="lightbox-size"></span>
                        <span class="lightbox-time"></span>
                    </div>
                </div>
                <div class="lightbox-actions">
                    <button class="lightbox-btn lightbox-download" aria-label="ダウンロード">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        <span>ダウンロード</span>
                    </button>
                    <button class="lightbox-btn lightbox-copy" aria-label="リンクをコピー">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        <span>コピー</span>
                    </button>
                    <button class="lightbox-btn lightbox-share" aria-label="共有">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="18" cy="5" r="3"></circle>
                            <circle cx="6" cy="12" r="3"></circle>
                            <circle cx="18" cy="19" r="3"></circle>
                            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
                        </svg>
                        <span>共有</span>
                    </button>
                    <button class="lightbox-btn lightbox-fullscreen" aria-label="フルスクリーン">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <polyline points="9 21 3 21 3 15"></polyline>
                            <line x1="21" y1="3" x2="14" y2="10"></line>
                            <line x1="3" y1="21" x2="10" y2="14"></line>
                        </svg>
                        <span>全画面</span>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(this.overlay);

        // イベントリスナーを設定
        this.setupEventListeners();
    }

    /**
     * イベントリスナーを設定
     */
    setupEventListeners() {
        // 閉じるボタン
        this.overlay.querySelector('.lightbox-close').addEventListener('click', () => this.close());

        // オーバーレイクリックで閉じる
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.close();
            }
        });

        // ESCキーで閉じる
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // ダウンロードボタン
        this.overlay.querySelector('.lightbox-download').addEventListener('click', () => this.download());

        // コピーボタン
        this.overlay.querySelector('.lightbox-copy').addEventListener('click', () => this.copyToClipboard());

        // 共有ボタン
        this.overlay.querySelector('.lightbox-share').addEventListener('click', () => this.share());

        // フルスクリーンボタン
        this.overlay.querySelector('.lightbox-fullscreen').addEventListener('click', () => this.toggleFullscreen());
    }

    /**
     * ライトボックスを開く
     * @param {Object} imageData - 画像データ
     */
    open(imageData) {
        if (!imageData || !imageData.src) return;

        this.currentImage = imageData;

        // 画像を設定
        const img = this.overlay.querySelector('.lightbox-image');
        img.src = imageData.src;
        img.alt = imageData.prompt || '生成画像';

        // 情報を設定
        const promptEl = this.overlay.querySelector('.lightbox-prompt');
        promptEl.textContent = imageData.prompt || '';

        const sizeEl = this.overlay.querySelector('.lightbox-size');
        sizeEl.textContent = imageData.size || '';

        const timeEl = this.overlay.querySelector('.lightbox-time');
        timeEl.textContent = imageData.time ? `生成時間: ${imageData.time}ms` : '';

        // 表示
        this.overlay.classList.add('active');
        this.isOpen = true;
        document.body.style.overflow = 'hidden';
    }

    /**
     * ライトボックスを閉じる
     */
    close() {
        this.overlay.classList.remove('active');
        this.isOpen = false;
        document.body.style.overflow = '';

        // フルスクリーンを解除
        if (document.fullscreenElement) {
            document.exitFullscreen();
        }
    }

    /**
     * 画像をダウンロード
     */
    async download() {
        if (!this.currentImage || !this.currentImage.src) return;

        try {
            const response = await fetch(this.currentImage.src);
            const blob = await response.blob();

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `visioncraftai_${Date.now()}.png`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showToast('画像をダウンロードしました');
        } catch (error) {
            console.error('Download error:', error);
            this.showToast('ダウンロードに失敗しました', 'error');
        }
    }

    /**
     * 画像をクリップボードにコピー
     */
    async copyToClipboard() {
        if (!this.currentImage || !this.currentImage.src) return;

        try {
            const response = await fetch(this.currentImage.src);
            const blob = await response.blob();

            await navigator.clipboard.write([
                new ClipboardItem({
                    [blob.type]: blob
                })
            ]);

            this.showToast('画像をクリップボードにコピーしました');
        } catch (error) {
            // クリップボードAPIが使えない場合はURLをコピー
            try {
                await navigator.clipboard.writeText(this.currentImage.src);
                this.showToast('画像URLをコピーしました');
            } catch (e) {
                console.error('Copy error:', e);
                this.showToast('コピーに失敗しました', 'error');
            }
        }
    }

    /**
     * 画像を共有
     */
    async share() {
        if (!this.currentImage) return;

        const shareData = {
            title: 'VisionCraftAI - AI生成画像',
            text: this.currentImage.prompt || 'VisionCraftAIで生成した画像',
            url: window.location.href
        };

        if (navigator.share) {
            try {
                // 画像を直接共有（対応ブラウザのみ）
                if (navigator.canShare && this.currentImage.src.startsWith('data:')) {
                    const response = await fetch(this.currentImage.src);
                    const blob = await response.blob();
                    const file = new File([blob], 'visioncraftai.png', { type: 'image/png' });

                    if (navigator.canShare({ files: [file] })) {
                        await navigator.share({
                            files: [file],
                            ...shareData
                        });
                        return;
                    }
                }

                await navigator.share(shareData);
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error('Share error:', error);
                }
            }
        } else {
            // Web Share APIが使えない場合はURLをコピー
            await this.copyToClipboard();
        }
    }

    /**
     * フルスクリーン切り替え
     */
    toggleFullscreen() {
        const container = this.overlay.querySelector('.lightbox-container');

        if (!document.fullscreenElement) {
            container.requestFullscreen().catch(err => {
                console.error('Fullscreen error:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    /**
     * トースト通知を表示
     * @param {string} message - メッセージ
     * @param {string} type - タイプ (success/error)
     */
    showToast(message, type = 'success') {
        // 既存の通知関数を使用
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            console.log(`[${type}] ${message}`);
        }
    }
}

// 画像ギャラリー管理クラス
class ImageGallery {
    constructor() {
        this.images = [];
        this.maxImages = 50;
        this.storageKey = 'vca_gallery';
        this.lightbox = new ImageLightbox();
        this.init();
    }

    /**
     * ギャラリーを初期化
     */
    init() {
        // ローカルストレージから履歴を読み込み
        this.loadFromStorage();
    }

    /**
     * 画像を追加
     * @param {Object} imageData - 画像データ
     */
    addImage(imageData) {
        const image = {
            id: Date.now(),
            src: imageData.src,
            prompt: imageData.prompt,
            size: imageData.size,
            time: imageData.time,
            style: imageData.style,
            createdAt: new Date().toISOString()
        };

        this.images.unshift(image);

        // 最大数を超えたら古いものを削除
        if (this.images.length > this.maxImages) {
            this.images = this.images.slice(0, this.maxImages);
        }

        this.saveToStorage();
        this.render();

        return image;
    }

    /**
     * 画像を削除
     * @param {number} id - 画像ID
     */
    removeImage(id) {
        this.images = this.images.filter(img => img.id !== id);
        this.saveToStorage();
        this.render();
    }

    /**
     * 全ての画像をクリア
     */
    clearAll() {
        this.images = [];
        this.saveToStorage();
        this.render();
    }

    /**
     * ローカルストレージに保存
     */
    saveToStorage() {
        try {
            // base64画像は大きいので、最新10件のみ保存
            const toSave = this.images.slice(0, 10).map(img => ({
                ...img,
                // サムネイル用に縮小（実際の画像はキャッシュに依存）
                src: img.src
            }));
            localStorage.setItem(this.storageKey, JSON.stringify(toSave));
        } catch (e) {
            console.warn('Gallery save error:', e);
        }
    }

    /**
     * ローカルストレージから読み込み
     */
    loadFromStorage() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            if (saved) {
                this.images = JSON.parse(saved);
            }
        } catch (e) {
            console.warn('Gallery load error:', e);
        }
    }

    /**
     * ギャラリーUIをレンダリング
     */
    render() {
        const container = document.getElementById('galleryContainer');
        if (!container) return;

        if (this.images.length === 0) {
            container.innerHTML = `
                <div class="gallery-empty">
                    <p>生成した画像がここに表示されます</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="gallery-header">
                <h3>生成履歴</h3>
                <button class="gallery-clear" id="galleryClearBtn">クリア</button>
            </div>
            <div class="gallery-grid">
                ${this.images.map(img => `
                    <div class="gallery-item" data-id="${img.id}">
                        <img src="${img.src}" alt="${img.prompt || '生成画像'}" loading="lazy">
                        <div class="gallery-item-overlay">
                            <button class="gallery-item-view" aria-label="拡大表示">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="11" cy="11" r="8"></circle>
                                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                                    <line x1="11" y1="8" x2="11" y2="14"></line>
                                    <line x1="8" y1="11" x2="14" y2="11"></line>
                                </svg>
                            </button>
                            <button class="gallery-item-delete" aria-label="削除">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3 6 5 6 21 6"></polyline>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // イベントリスナーを設定
        this.setupGalleryEvents();
    }

    /**
     * ギャラリーのイベントリスナーを設定
     */
    setupGalleryEvents() {
        const container = document.getElementById('galleryContainer');
        if (!container) return;

        // クリアボタン
        const clearBtn = container.querySelector('#galleryClearBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (confirm('すべての生成履歴を削除しますか？')) {
                    this.clearAll();
                }
            });
        }

        // 各アイテム
        container.querySelectorAll('.gallery-item').forEach(item => {
            const id = parseInt(item.dataset.id);
            const image = this.images.find(img => img.id === id);

            // 拡大表示
            item.querySelector('.gallery-item-view')?.addEventListener('click', (e) => {
                e.stopPropagation();
                if (image) {
                    this.lightbox.open(image);
                }
            });

            // 削除
            item.querySelector('.gallery-item-delete')?.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeImage(id);
            });

            // 画像クリックでも拡大
            item.querySelector('img')?.addEventListener('click', () => {
                if (image) {
                    this.lightbox.open(image);
                }
            });
        });
    }
}

// グローバルインスタンス
let imageGallery = null;

// DOMContentLoaded時に初期化
document.addEventListener('DOMContentLoaded', () => {
    imageGallery = new ImageGallery();
    imageGallery.render();
});

// エクスポート
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ImageLightbox, ImageGallery };
}
