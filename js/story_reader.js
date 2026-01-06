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

            // 動画の自動再生制御（Intersection Observer）をセットアップ
            setupVideoObserver();
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
                video.play().catch(e => console.log("Autoplay blocked:", e));
            } else {
                // 画面から出た -> 一時停止
                video.pause();
            }
        });
    }, options);

    videos.forEach(video => {
        observer.observe(video);
        // 初期設定：音ミュート、インライン再生（スマホ用）
        video.muted = true;
        video.playsInline = true;
    });
}
