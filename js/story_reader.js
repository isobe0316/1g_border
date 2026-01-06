document.addEventListener('DOMContentLoaded', () => {
    // URLパラメータからファイル名を取得 (?file=...)
    const urlParams = new URLSearchParams(window.location.search);
    const fileName = urlParams.get('file');
    const contentArea = document.getElementById('content-area');
    const titleElement = document.getElementById('story-title');

    if (!fileName) {
        contentArea.innerHTML = '<p class="error">ファイルが指定されていません。</p>';
        return;
    }

    // Markdownファイルをフェッチ
    fetch(fileName)
        .then(response => {
            if (!response.ok) throw new Error('File not found');
            return response.text();
        })
        .then(markdown => {
            // Marked.jsの設定（HTMLタグを許可）
            marked.setOptions({
                headerIds: false,
                mangle: false
            });

            // MarkdownをHTMLに変換して表示
            contentArea.innerHTML = marked.parse(markdown);

            // タイトルを設定（最初のH1タグの中身を取得）
            const h1 = contentArea.querySelector('h1');
            if (h1) {
                titleElement.textContent = h1.textContent;
                document.title = h1.textContent + " - ストーリーリーダー";
            }

            // 動画のセットアップ
            setupVideos();
        })
        .catch(error => {
            console.error('Error:', error);
            contentArea.innerHTML = `<p class="error">ストーリーの読み込みに失敗しました。<br>${error.message}</p>`;
        });
});

/**
 * 動画が画面内に入った時だけ再生する処理
 */
function setupVideoObserver() {
    // 旧関数名を使っている場合もあるため、新しい実装を用意
}

/**
 * 動画の設定と制御
 */
function setupVideos() {
    const videos = document.querySelectorAll('video');
    
    // オプション: 画面の50%が見えたら反応
    const options = {
        root: null,
        rootMargin: '0px',
        threshold: 0.5
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            const video = entry.target;
            
            if (entry.isIntersecting) {
                // 画面に入った -> 再生
                // ※音声を出すにはユーザー操作が必要なため、まずはミュートで再生を試みる
                video.muted = true; 
                video.play().catch(e => console.log("Autoplay blocked:", e));
            } else {
                // 画面から出た -> 一時停止
                video.pause();
            }
        });
    }, options);

    videos.forEach(video => {
        // コントローラーを表示（これでユーザーが音量操作できる）
        video.controls = true;
        
        // 初期設定：ミュート、インライン再生
        video.muted = true;
        video.playsInline = true;
        
        // 自動再生の監視を開始
        observer.observe(video);
    });
}
