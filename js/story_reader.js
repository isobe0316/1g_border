document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const fileName = urlParams.get('file');
    
    // 要素取得
    const bgContainer = document.getElementById('background-container');
    const subtitleBox = document.getElementById('subtitle-box');
    const subtitleText = document.getElementById('subtitle-text');
    const startOverlay = document.getElementById('start-overlay');
    const bgm = document.getElementById('bgm');
    const autoBtn = document.getElementById('auto-btn');

    // 状態管理
    let storyData = []; 
    let currentIndex = 0;
    let isAutoMode = false;
    let autoTimer = null;
    let isPlaying = false;
    let voiceMap = null; // VOICE_MAP を読み込む
    let voiceMapIndex = 0; // 次に使う音声のインデックス
    let currentAudio = null;
    let bgmFadeInterval = null;

    // 初期化
    if (fileName) {
        loadStory(fileName);
    }

    // イベントリスナー
    startOverlay.addEventListener('click', startStory);
    
    // 画面クリックで次へ
    document.getElementById('screen').addEventListener('click', (e) => {
        if (!isPlaying) return;
        if (e.target.closest('.controls')) return; 
        
        if (isAutoMode) {
            stopAutoMode();
        } else {
            nextScene();
        }
    });

    autoBtn.addEventListener('click', toggleAutoMode);

    async function loadStory(file) {
        try {
            const res = await fetch(file);
            const text = await res.text();
            storyData = parseMarkdownToScenes(text);
            preloadMedia(0);
            // VOICE_MAP がグローバルにあれば読み込む
            if (typeof VOICE_MAP !== 'undefined') {
                voiceMap = VOICE_MAP;
            }
        } catch (e) {
            console.error(e);
            subtitleText.textContent = "ストーリーの読み込みに失敗しました。";
        }
    }

    // Markdownパーサー（BGMタグ対応版）
    function parseMarkdownToScenes(markdown) {
        const lines = markdown.split('\n');
        const data = [];
        
        // デフォルト背景
        data.push({ type: 'media', tag: '<img src="assets/bg_foodtruck_anime.jpg">' });

        lines.forEach(line => {
            line = line.trim();
            if (!line) return;

            // 1. 画像/動画タグ (<img...> <video...>)
            if (line.match(/<(img|video)[^>]*>/)) {
                data.push({ type: 'media', tag: line });
            } 
            // 2. BGMトリガータグ (<div class="bgm-trigger" ...>)
            else if (line.includes('class="bgm-trigger"')) {
                // data-src属性からファイル名抽出
                const match = line.match(/data-src="([^"]+)"/);
                if (match) {
                    data.push({ type: 'bgm', src: match[1] });
                }
            }
            // 3. テキスト（注釈やタグ以外）
            else if (!line.startsWith('#') && !line.startsWith('---') && !line.startsWith('<')) {
                data.push({ type: 'text', text: line });
            }
        });
        return data;
    }

    function startStory() {
        startOverlay.classList.add('hidden');
        subtitleBox.classList.remove('hidden');
        isPlaying = true;
        
        // 初期BGM設定（もしタグがなければOPを流す）
        if (bgm.src === "") {
            bgm.src = "assets/op_theme_1g.mp3";
        }
        bgm.volume = 0.3;
        bgm.play().catch(e => console.log("BGM error:", e));

        renderScene();
    }

    function renderScene() {
        if (currentIndex >= storyData.length) {
            subtitleText.textContent = "End";
            return;
        }

        const item = storyData[currentIndex];

        // --- 演出系（Media, BGM）は処理して即次へ ---
        if (item.type === 'media') {
            updateBackground(item.tag);
            currentIndex++;
            renderScene(); 
        } 
        else if (item.type === 'bgm') {
            changeBGM(item.src);
            currentIndex++;
            renderScene();
        } 
        // --- テキスト系は表示して待機 ---
        else if (item.type === 'text') {
            subtitleText.textContent = item.text;
            // まず既存の再生中音声を止める
            stopAllVoices();

            // 音声マップがある場合はファイル再生を優先
            if (voiceMap && voiceMap[voiceMapIndex]) {
                const entry = voiceMap[voiceMapIndex];
                voiceMapIndex++;
                const audio = new Audio(entry.file);
                currentAudio = audio;
                audio.volume = 1.0;
                audio.onended = () => {
                    currentAudio = null;
                    if (isAutoMode) {
                        autoTimer = setTimeout(nextScene, 1000);
                    }
                };
                audio.play().catch(err => {
                    // 再生失敗なら TTS にフォールバック
                    console.warn('Audio play failed, falling back to TTS:', err);
                    speak(item.text, () => {
                        if (isAutoMode) autoTimer = setTimeout(nextScene, 1000);
                    });
                });
            } else {
                // TTSで読み上げ
                speak(item.text, () => {
                    if (isAutoMode) {
                        autoTimer = setTimeout(nextScene, 1000);
                    }
                });
                // もしvoiceMapが存在していればインデックスを進める
                if (voiceMap) voiceMapIndex++;
            }
        }
    }

    function nextScene() {
        // シーン移行の際は再生中の音を確実に止める
        stopAllVoices();
        currentIndex++;
        renderScene();
    }

    // 背景切り替え
    function updateBackground(htmlTag) {
        const div = document.createElement('div');
        div.innerHTML = htmlTag;
        const newMedia = div.firstChild;
        if (!newMedia) return;

        newMedia.classList.add('active');
        if (newMedia.tagName === 'VIDEO') {
            newMedia.muted = true;
            newMedia.loop = true;
            newMedia.autoplay = true;
            newMedia.playsInline = true;
            newMedia.play().catch(e => {});
        }

        bgContainer.appendChild(newMedia);

        const oldMedias = Array.from(bgContainer.children);
        if (oldMedias.length > 1) {
            for (let i = 0; i < oldMedias.length - 1; i++) {
                const old = oldMedias[i];
                old.classList.remove('active');
                setTimeout(() => {
                    if (old.parentNode) old.parentNode.removeChild(old);
                }, 1000);
            }
        }
    }

    // BGM切り替え機能（クロスフェード風）
    function changeBGM(src) {
        // 同じ曲なら何もしない
        if (bgm.src && bgm.src.includes(src)) return;

        // 既存のフェード中止
        if (bgmFadeInterval) {
            clearInterval(bgmFadeInterval);
            bgmFadeInterval = null;
        }

        // フェードアウト処理
        const targetVol = 0.3;
        const step = 0.05;
        bgmFadeInterval = setInterval(() => {
            try {
                if (bgm.volume > step) {
                    bgm.volume = Math.max(0, bgm.volume - step);
                } else {
                    clearInterval(bgmFadeInterval);
                    bgmFadeInterval = null;
                    // 曲変更
                    try { bgm.pause(); } catch (e) {}
                    bgm.src = src;
                    bgm.volume = 0;
                    bgm.play().catch(e => console.log("BGM Play Error:", e));
                    // フェードイン
                    const fadeIn = setInterval(() => {
                        try {
                            if (bgm.volume < targetVol - 0.01) {
                                bgm.volume = Math.min(targetVol, bgm.volume + step);
                            } else {
                                clearInterval(fadeIn);
                            }
                        } catch (e) { clearInterval(fadeIn); }
                    }, 100);
                }
            } catch (e) {
                clearInterval(bgmFadeInterval);
                bgmFadeInterval = null;
            }
        }, 100);
    }

    // 読み上げ (TTS)
    function speak(text, onEndCallback) {
        window.speechSynthesis.cancel();
        
        // タグ除去
        const cleanText = text.replace(/<[^>]*>/g, '');
        if (!cleanText) {
            if(onEndCallback) onEndCallback();
            return;
        }

        const uttr = new SpeechSynthesisUtterance(cleanText);
        uttr.lang = 'ja-JP';
        uttr.rate = 1.0;

        if (cleanText.includes('「')) {
            if (cleanText.match(/(です|ます|先輩|店長)/)) {
                uttr.pitch = 1.2; // 梨奈
            } else {
                uttr.pitch = 0.8; // 阿久斗
            }
        } else {
            uttr.pitch = 1.0;
            uttr.rate = 1.1;
        }

        uttr.onend = onEndCallback;
        
        // タイムアウト対策
        const timeout = setTimeout(() => {
            if(onEndCallback) onEndCallback();
        }, (cleanText.length * 200) + 2000); 

        uttr.onend = () => {
            clearTimeout(timeout);
            if(onEndCallback) onEndCallback();
        };

        window.speechSynthesis.speak(uttr);
    }

    function stopAllVoices() {
        // stop any audio element
        if (currentAudio) {
            try {
                currentAudio.pause();
                currentAudio.currentTime = 0;
                try { currentAudio.src = ''; } catch (e) {}
            } catch (e) {}
            currentAudio = null;
        }
        // stop speechSynthesis
        try { window.speechSynthesis.cancel(); } catch (e) {}
        // clear auto-timer so we don't trigger unexpected nextScene()
        try { clearTimeout(autoTimer); autoTimer = null; } catch (e) {}
    }

    function toggleAutoMode(e) {
        e.stopPropagation();
        isAutoMode = !isAutoMode;
        autoBtn.classList.toggle('active');
        if (isAutoMode) {
            if (!window.speechSynthesis.speaking) nextScene();
        } else {
            clearTimeout(autoTimer);
        }
    }

    function stopAutoMode() {
        isAutoMode = false;
        autoBtn.classList.remove('active');
        clearTimeout(autoTimer);
    }

    function preloadMedia(index) {
        // 省略
    }
});
