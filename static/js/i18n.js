/**
 * VisionCraftAI - 多言語対応 (i18n) モジュール
 * 対応言語: 日本語 (ja), 英語 (en)
 */

const i18n = {
    // 現在の言語
    currentLang: 'ja',

    // 翻訳データ
    translations: {
        ja: {
            // ナビゲーション
            'nav.features': '特徴',
            'nav.pricing': '料金',
            'nav.demo': 'デモ',
            'nav.docs': 'API Docs',
            'nav.dashboard': 'ダッシュボード',
            'nav.cta': '無料で試す',

            // ヒーローセクション
            'hero.title.1': 'AIで',
            'hero.title.2': '想像',
            'hero.title.3': 'を',
            'hero.title.4': '創造',
            'hero.title.5': 'する',
            'hero.subtitle': '最先端AI技術を活用した画像生成プラットフォーム。テキストプロンプトから高品質な画像を瞬時に生成。',
            'hero.cta.primary': '無料で画像を生成',
            'hero.cta.secondary': 'APIドキュメント',

            // 特徴セクション
            'features.title': 'なぜVisionCraftAI?',
            'features.subtitle': 'プロフェッショナルからホビーストまで、あらゆるニーズに応える機能',
            'features.speed.title': '高速生成',
            'features.speed.desc': 'AIによる高速な画像生成。数秒で高品質な画像をお届けします。',
            'features.quality.title': '高品質出力',
            'features.quality.desc': '最大4096x4096の高解像度に対応。商用利用可能な品質を実現します。',
            'features.api.title': '柔軟なAPI',
            'features.api.desc': 'RESTful APIで簡単統合。バッチ処理やWebhookにも対応しています。',
            'features.security.title': '安全・安心',
            'features.security.desc': '不適切コンテンツの自動フィルタリング。プロンプト検証で安全な画像生成を保証。',
            'features.usage.title': '使用量管理',
            'features.usage.desc': 'リアルタイムの使用量トラッキング。コスト管理も簡単にできます。',
            'features.pricing.title': '柔軟な料金体系',
            'features.pricing.desc': '無料プランから始めて、ニーズに合わせてアップグレード。クレジット購入も可能。',

            // 料金セクション
            'pricing.title': 'シンプルな料金プラン',
            'pricing.subtitle': '無料で始めて、必要に応じてアップグレード',
            'pricing.monthly': '月額',
            'pricing.yearly': '年額',
            'pricing.save': '2ヶ月分お得！',
            'pricing.popular': '人気',
            'pricing.off': '% OFF',
            'pricing.perMonth': '/月',

            // Freeプラン
            'pricing.free.name': 'Free',
            'pricing.free.desc': '個人利用・お試しに最適',
            'pricing.free.feature1': '月5枚まで生成',
            'pricing.free.feature2': '最大512x512解像度',
            'pricing.free.feature3': '基本的なスタイル',
            'pricing.free.feature4': 'コミュニティサポート',
            'pricing.free.cta': '無料で始める',

            // Basicプラン
            'pricing.basic.name': 'Basic',
            'pricing.basic.desc': '個人クリエイター向け',
            'pricing.basic.feature1': '月100枚まで生成',
            'pricing.basic.feature2': '最大1024x1024解像度',
            'pricing.basic.feature3': '全スタイル利用可能',
            'pricing.basic.feature4': 'メールサポート',
            'pricing.basic.feature5': 'APIアクセス',
            'pricing.basic.cta': 'Basic を選択',

            // Proプラン
            'pricing.pro.name': 'Pro',
            'pricing.pro.desc': 'プロフェッショナル向け',
            'pricing.pro.feature1': '月500枚まで生成',
            'pricing.pro.feature2': '最大2048x2048解像度',
            'pricing.pro.feature3': '優先処理キュー',
            'pricing.pro.feature4': 'バッチ処理（50枚同時）',
            'pricing.pro.feature5': '優先サポート',
            'pricing.pro.cta': 'Pro を選択',

            // Enterpriseプラン
            'pricing.enterprise.name': 'Enterprise',
            'pricing.enterprise.desc': 'ビジネス・大規模利用',
            'pricing.enterprise.feature1': '無制限生成',
            'pricing.enterprise.feature2': '最大4096x4096解像度',
            'pricing.enterprise.feature3': '専用APIエンドポイント',
            'pricing.enterprise.feature4': 'SLA保証',
            'pricing.enterprise.feature5': '専任サポート担当',
            'pricing.enterprise.cta': 'お問い合わせ',

            // デモセクション
            'demo.title': '今すぐ試してみよう',
            'demo.subtitle': 'プロンプトを入力して、AIが生成する画像を体験',
            'demo.apikey.label': 'APIキー（オプション）',
            'demo.apikey.placeholder': 'vca_xxxxxxxx.xxxxxxxx',
            'demo.apikey.help': 'APIキーがない場合は',
            'demo.apikey.create': '無料キーを作成',
            'demo.apikey.or': 'するか、デモモードでお試しいただけます。',
            'demo.prompt.label': 'プロンプト',
            'demo.prompt.placeholder': '例: 桜が咲く日本庭園の夕暮れ、フォトリアリスティック、4K',
            'demo.style.none': 'スタイルなし',
            'demo.style.photo': 'フォトリアリスティック',
            'demo.style.artistic': 'アーティスティック',
            'demo.style.anime': 'アニメ調',
            'demo.style.digital': 'デジタルアート',
            'demo.generate': '画像を生成',
            'demo.generating': '生成中...',
            'demo.result.placeholder': '生成された画像がここに表示されます',
            'demo.result.expand': '拡大',
            'demo.result.download': '保存',
            'demo.result.share': '共有',

            // 共有機能
            'share.modal.title': '画像を共有',
            'share.copy.link': 'リンクをコピー',
            'share.copy.success': 'リンクをコピーしました',
            'share.copy.image': '画像をクリップボードにコピーしました',
            'share.other': 'その他の方法で共有',
            'share.text': 'VisionCraftAIで画像を生成しました！',

            // フッター
            'footer.brand.desc': '最先端のAI技術で、あなたの創造性を解放します。テキストから画像へ、想像を現実に。',
            'footer.product': 'プロダクト',
            'footer.resources': 'リソース',
            'footer.support': 'サポート',
            'footer.docs': 'ドキュメント',
            'footer.reference': 'API Reference',
            'footer.tutorial': 'チュートリアル',
            'footer.sample': 'サンプルコード',
            'footer.help': 'ヘルプセンター',
            'footer.contact': 'お問い合わせ',
            'footer.terms': '利用規約',
            'footer.privacy': 'プライバシーポリシー',
            'footer.copyright': '© 2026 VisionCraftAI. All rights reserved.',

            // 通知メッセージ
            'notification.apikey.saved': 'APIキーを保存しました',
            'notification.apikey.created': 'APIキーを作成しました！',
            'notification.apikey.failed': 'APIキーの作成に失敗しました',
            'notification.generate.success': '画像を生成しました！',
            'notification.generate.demo': 'デモ生成完了 - APIキーで本格的な画像を生成！',
            'notification.generate.error': '生成に失敗しました',
            'notification.prompt.empty': 'プロンプトを入力してください',
            'notification.download.success': '画像をダウンロードしました',
            'notification.download.failed': 'ダウンロードに失敗しました',
            'notification.no.image': '表示する画像がありません',
            'notification.mode.demo': 'デモモードに切り替えました',
            'notification.mode.live': '本番モードに切り替えました',

            // その他
            'common.email.prompt': 'メールアドレスを入力してください:'
        },

        en: {
            // ナビゲーション
            'nav.features': 'Features',
            'nav.pricing': 'Pricing',
            'nav.demo': 'Demo',
            'nav.docs': 'API Docs',
            'nav.dashboard': 'Dashboard',
            'nav.cta': 'Try Free',

            // ヒーローセクション
            'hero.title.1': 'Turn ',
            'hero.title.2': 'Imagination',
            'hero.title.3': ' into ',
            'hero.title.4': 'Creation',
            'hero.title.5': ' with AI',
            'hero.subtitle': 'State-of-the-art AI-powered image generation platform. Create high-quality images from text prompts instantly.',
            'hero.cta.primary': 'Generate Images Free',
            'hero.cta.secondary': 'API Documentation',

            // 特徴セクション
            'features.title': 'Why VisionCraftAI?',
            'features.subtitle': 'Features that meet every need, from professionals to hobbyists',
            'features.speed.title': 'Fast Generation',
            'features.speed.desc': 'AI-powered fast image generation. Get high-quality images in seconds.',
            'features.quality.title': 'High Quality Output',
            'features.quality.desc': 'Support up to 4096x4096 resolution. Commercial-grade quality.',
            'features.api.title': 'Flexible API',
            'features.api.desc': 'Easy integration with RESTful API. Supports batch processing and webhooks.',
            'features.security.title': 'Safe & Secure',
            'features.security.desc': 'Automatic inappropriate content filtering. Prompt validation ensures safe image generation.',
            'features.usage.title': 'Usage Management',
            'features.usage.desc': 'Real-time usage tracking. Easy cost management.',
            'features.pricing.title': 'Flexible Pricing',
            'features.pricing.desc': 'Start free and upgrade as needed. Credit purchase available.',

            // 料金セクション
            'pricing.title': 'Simple Pricing Plans',
            'pricing.subtitle': 'Start free and upgrade when you need more',
            'pricing.monthly': 'Monthly',
            'pricing.yearly': 'Yearly',
            'pricing.save': 'Save 2 months!',
            'pricing.popular': 'Popular',
            'pricing.off': '% OFF',
            'pricing.perMonth': '/mo',

            // Freeプラン
            'pricing.free.name': 'Free',
            'pricing.free.desc': 'Perfect for personal use & trial',
            'pricing.free.feature1': 'Up to 5 images/month',
            'pricing.free.feature2': 'Max 512x512 resolution',
            'pricing.free.feature3': 'Basic styles',
            'pricing.free.feature4': 'Community support',
            'pricing.free.cta': 'Start Free',

            // Basicプラン
            'pricing.basic.name': 'Basic',
            'pricing.basic.desc': 'For individual creators',
            'pricing.basic.feature1': 'Up to 100 images/month',
            'pricing.basic.feature2': 'Max 1024x1024 resolution',
            'pricing.basic.feature3': 'All styles available',
            'pricing.basic.feature4': 'Email support',
            'pricing.basic.feature5': 'API access',
            'pricing.basic.cta': 'Choose Basic',

            // Proプラン
            'pricing.pro.name': 'Pro',
            'pricing.pro.desc': 'For professionals',
            'pricing.pro.feature1': 'Up to 500 images/month',
            'pricing.pro.feature2': 'Max 2048x2048 resolution',
            'pricing.pro.feature3': 'Priority queue',
            'pricing.pro.feature4': 'Batch processing (50 at once)',
            'pricing.pro.feature5': 'Priority support',
            'pricing.pro.cta': 'Choose Pro',

            // Enterpriseプラン
            'pricing.enterprise.name': 'Enterprise',
            'pricing.enterprise.desc': 'For business & large scale',
            'pricing.enterprise.feature1': 'Unlimited generation',
            'pricing.enterprise.feature2': 'Max 4096x4096 resolution',
            'pricing.enterprise.feature3': 'Dedicated API endpoint',
            'pricing.enterprise.feature4': 'SLA guarantee',
            'pricing.enterprise.feature5': 'Dedicated support',
            'pricing.enterprise.cta': 'Contact Us',

            // デモセクション
            'demo.title': 'Try It Now',
            'demo.subtitle': 'Enter a prompt and experience AI-generated images',
            'demo.apikey.label': 'API Key (Optional)',
            'demo.apikey.placeholder': 'vca_xxxxxxxx.xxxxxxxx',
            'demo.apikey.help': 'No API key?',
            'demo.apikey.create': 'Create free key',
            'demo.apikey.or': ' or try demo mode.',
            'demo.prompt.label': 'Prompt',
            'demo.prompt.placeholder': 'e.g. A serene Japanese garden with cherry blossoms at sunset, photorealistic, 4K',
            'demo.style.none': 'No style',
            'demo.style.photo': 'Photorealistic',
            'demo.style.artistic': 'Artistic',
            'demo.style.anime': 'Anime',
            'demo.style.digital': 'Digital Art',
            'demo.generate': 'Generate Image',
            'demo.generating': 'Generating...',
            'demo.result.placeholder': 'Generated image will appear here',
            'demo.result.expand': 'Expand',
            'demo.result.download': 'Download',
            'demo.result.share': 'Share',

            // 共有機能
            'share.modal.title': 'Share Image',
            'share.copy.link': 'Copy Link',
            'share.copy.success': 'Link copied',
            'share.copy.image': 'Image copied to clipboard',
            'share.other': 'More sharing options',
            'share.text': 'Generated with VisionCraftAI!',

            // フッター
            'footer.brand.desc': 'Unleash your creativity with cutting-edge AI technology. From text to image, imagination to reality.',
            'footer.product': 'Product',
            'footer.resources': 'Resources',
            'footer.support': 'Support',
            'footer.docs': 'Documentation',
            'footer.reference': 'API Reference',
            'footer.tutorial': 'Tutorials',
            'footer.sample': 'Sample Code',
            'footer.help': 'Help Center',
            'footer.contact': 'Contact',
            'footer.terms': 'Terms of Service',
            'footer.privacy': 'Privacy Policy',
            'footer.copyright': '© 2026 VisionCraftAI. All rights reserved.',

            // 通知メッセージ
            'notification.apikey.saved': 'API key saved',
            'notification.apikey.created': 'API key created!',
            'notification.apikey.failed': 'Failed to create API key',
            'notification.generate.success': 'Image generated!',
            'notification.generate.demo': 'Demo complete - Use API key for full images!',
            'notification.generate.error': 'Generation failed',
            'notification.prompt.empty': 'Please enter a prompt',
            'notification.download.success': 'Image downloaded',
            'notification.download.failed': 'Download failed',
            'notification.no.image': 'No image to display',
            'notification.mode.demo': 'Switched to demo mode',
            'notification.mode.live': 'Switched to live mode',

            // その他
            'common.email.prompt': 'Enter your email address:'
        }
    },

    /**
     * 翻訳を取得
     */
    t(key) {
        const lang = this.currentLang;
        return this.translations[lang]?.[key] || this.translations['ja']?.[key] || key;
    },

    /**
     * 言語を設定
     */
    setLang(lang) {
        if (this.translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('vca_lang', lang);
            this.updatePageContent();
            this.updateHtmlLang();
            return true;
        }
        return false;
    },

    /**
     * html要素のlang属性を更新
     */
    updateHtmlLang() {
        document.documentElement.lang = this.currentLang;
    },

    /**
     * ブラウザの言語設定から初期言語を決定
     */
    detectLanguage() {
        // 保存された言語設定を優先
        const saved = localStorage.getItem('vca_lang');
        if (saved && this.translations[saved]) {
            return saved;
        }

        // ブラウザの言語設定
        const browserLang = navigator.language || navigator.userLanguage;
        if (browserLang.startsWith('ja')) {
            return 'ja';
        }
        return 'en';
    },

    /**
     * 初期化
     */
    init() {
        this.currentLang = this.detectLanguage();
        this.updateHtmlLang();
        this.updatePageContent();
        this.initLanguageSwitcher();
    },

    /**
     * ページ内の翻訳対象要素を更新
     */
    updatePageContent() {
        // data-i18n属性を持つ要素を翻訳
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = this.t(key);
        });

        // data-i18n-placeholder属性を持つ要素のplaceholderを翻訳
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.t(key);
        });

        // data-i18n-aria属性を持つ要素のaria-labelを翻訳
        document.querySelectorAll('[data-i18n-aria]').forEach(el => {
            const key = el.getAttribute('data-i18n-aria');
            el.setAttribute('aria-label', this.t(key));
        });

        // 特別な処理が必要な要素
        this.updateSpecialElements();
    },

    /**
     * 特別な処理が必要な要素を更新
     */
    updateSpecialElements() {
        // ヒーローのタイトル（spanを含む）
        const heroTitle = document.getElementById('hero-title');
        if (heroTitle) {
            heroTitle.innerHTML = `
                ${this.t('hero.title.1')}<span>${this.t('hero.title.2')}</span>${this.t('hero.title.3')}<span>${this.t('hero.title.4')}</span>${this.t('hero.title.5')}
            `;
        }

        // 月額/年額の単位
        const priceSpans = document.querySelectorAll('.price span');
        priceSpans.forEach(span => {
            if (span.textContent.includes('/')) {
                span.textContent = this.t('pricing.perMonth');
            }
        });

        // 言語切り替えボタンのアクティブ状態
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.lang === this.currentLang);
        });
    },

    /**
     * 言語切り替えUIを初期化
     */
    initLanguageSwitcher() {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const lang = btn.dataset.lang;
                if (lang) {
                    this.setLang(lang);
                }
            });
        });
    }
};

// グローバルに公開
window.i18n = i18n;

// DOMロード後に初期化
document.addEventListener('DOMContentLoaded', () => {
    i18n.init();
});
