import os
import re
import asyncio
import edge_tts

# ==========================================
# ⚙️ 設定エリア
# ==========================================
INPUT_FILE = "sequel/story_ep1.md"
OUTPUT_DIR = "assets/voices"
VOICE_MAPPING_FILE = "assets/voice_map.js"

# ボイス設定 (Microsoft Edge Online Voices)
# 視聴可能: https://speech.microsoft.com/portal/voicegallery
VOICE_AKUTO = "ja-JP-KeitaNeural"   # 男性：阿久斗・ナレーション
VOICE_RINA = "ja-JP-NanamiNeural"   # 女性：梨奈

async def generate_voices():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Markdown読み込み
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    voice_map = []
    voice_index = 0
    tasks = []

    print("音声生成を開始します...")

    for line in lines:
        text = line.strip()
        
        # 空行、タグ、見出し等はスキップ
        if not text or text.startswith(("#", "---", "<", "![", "[", ">")):
            # 引用符 "> " で始まる行はセリフとして処理したいが、
            # 現在のMarkdownでは "> " は引用ブロックとして使われているため除去
            if text.startswith("> "):
                text = text[2:]
            else:
                continue

        # 画像/動画タグやBGMタグもスキップ
        if "class=" in text or ".jpg" in text or ".mp4" in text:
            continue

        # 話者判定ロジック
        voice = VOICE_AKUTO
        if "「" in text:
            # 梨奈っぽい語尾や呼びかけ
            if re.search(r"(先輩|店長|です|ます|ね|よ)", text):
                voice = VOICE_RINA
            # 明確に阿久斗っぽい場合（俺、だ、だろう）は上書き
            if re.search(r"(俺|だ$|だろう|ないか$)", text):
                voice = VOICE_AKUTO
        else:
            # 地の文は阿久斗（ナレーション）
            voice = VOICE_AKUTO

        # ファイル名設定
        filename = f"voice_{voice_index:03d}.mp3"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # マッピングデータに追加 (テキストの一部をキーにするなど工夫もできるが、今回は順序依存)
        voice_map.append({
            "index": voice_index,
            "text": text[:20], # 確認用
            "file": f"{OUTPUT_DIR}/{filename}"
        })

        # 生成タスク追加
        communicate = edge_tts.Communicate(text, voice)
        tasks.append(communicate.save(filepath))
        
        print(f"  [{voice_index}] 生成予約: {text[:15]}... ({voice})")
        voice_index += 1

    # 一括生成実行
    print(f"{len(tasks)} 個の音声を生成中...")
    await asyncio.gather(*tasks)

    # マッピングファイルをJSとして保存（Webアプリから読み込むため）
    js_content = f"const VOICE_MAP = {str(voice_map)};"
    with open(VOICE_MAPPING_FILE, "w", encoding="utf-8") as f:
        f.write(js_content)

    print("完了しました！")
    print(f"  音声ファイル: {OUTPUT_DIR}")
    print(f"  マップファイル: {VOICE_MAPPING_FILE}")

if __name__ == "__main__":
    asyncio.run(generate_voices())
