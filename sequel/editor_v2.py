import os
from moviepy import *
import numpy as np

# ==========================================
# ⚙️ 設定エリア
# ==========================================

# 1. 素材フォルダと出力ファイル名
ASSETS_DIR = "./assets"  # 素材がある場所（同じフォルダなら "."）
OUTPUT_FILE = "1g_borderline_subtitled.mp4"

# 2. 画面サイズ (Full HD)
W, H = 1920, 1080

# 3. 日本語フォントの設定 (★重要: 環境に合わせて書き換えてください)
# Windowsの例: "C:/Windows/Fonts/meiryo.ttc" (メイリオ)
# Macの例: "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
# Linux/Colabの例: "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"
FONT_PATH = "C:/Windows/Fonts/meiryo.ttc" 

# 4. 音楽ファイル
BGM_FILE = "op_theme_1g.mp3"

# ==========================================
# 🎬 シナリオ・データ (台本)
# ==========================================
# ここにファイル名とセリフを記述します
SCENARIO = [
    {
        "type": "image",
        "file": "bg_foodtruck_anime.jpg",
        "duration": 5,
        "subtitle": "阿久斗「いいか、梨奈。飲食店の倒産理由第一位はなんだ」"
    },
    {
        "type": "video",
        "file": "visual_2_rina_open.mp4",
        "duration": None, # 動画の長さをそのまま使う場合はNone
        "subtitle": "梨奈「えーと、味がまずい？」"
    },
    {
        "type": "video",
        "file": "visual_3_steak_sizzle.mp4",
        "duration": 4, # 動画が長い場合はここで秒数を指定してカット
        "subtitle": "阿久斗「違う。どんぶり勘定による資金ショートだ」"
    },
    {
        "type": "image",
        "file": "visual_4_conflict.jpg",
        "duration": 5,
        "subtitle": "阿久斗「この1gが勝負を決める！」\n梨奈「151gじゃダメなんですか？」"
    },
    {
        "type": "video",
        "file": "visual_5_rina_tasting.mp4",
        "duration": None,
        "subtitle": "（至福の味見中...）"
    },
    {
        "type": "video",
        "file": "visual_6_sunset_ending.mp4",
        "duration": 6,
        "subtitle": "阿久斗「……計算が合わない。肉が減りすぎている」"
    },
    # タイトル画面（アニメ背景）
    {
        "type": "title_card", 
        "file": "bg_foodtruck_anime.jpg", 
        "main_title": "1gの境界線",
        "sub_title": "The 1g Border",
        "duration": 5,
        "subtitle": "" 
    },
    # エンドカード（夕暮れアニメ背景）
    {
        "type": "title_card", 
        "file": "bg_foodtruck_sunset_anime.jpg", 
        "main_title": "Coming Soon",
        "sub_title": "2026.04 Release",
        "duration": 5,
        "subtitle": ""
    }
]

# ==========================================
# 🛠️ 映像処理エンジン
# ==========================================

def fit_to_screen(clip):
    """
    どんなサイズ・縦横比の素材も 1920x1080 に美しく収める魔法の関数
    """
    if clip.w == 0 or clip.h == 0: return clip

    clip_ratio = clip.w / clip.h
    target_ratio = W / H
    
    # 縦長素材（スマホ動画など）の場合
    if clip_ratio < target_ratio:
        # 1. メイン映像: 高さを画面いっぱいに
        main = clip.resized(height=H)
        
        # 2. 背景映像: 画面幅に合わせて拡大し、暗くしてぼかす（ブラー代替処理）
        bg = clip.resized(width=W)
        bg = bg.cropped(x1=0, y1=bg.h/2 - H/2, width=W, height=H)
        bg = bg.with_effects([vfx.MultiplyColor(0.25)])  # 輝度を25%に落とす
        
        # 3. 合成
        final = CompositeVideoClip([bg, main.with_position("center")])
        final = final.with_duration(clip.duration)
        return final
        
    # 横長素材の場合
    else:
        # 高さを合わせて中央を切り抜く（パン＆スキャン）
        clip = clip.resized(height=H)
        if clip.w > W:
            clip = clip.cropped(x1=clip.w/2 - W/2, width=W, height=H)
        return clip

def add_subtitle(clip, text):
    """
    映像の下に映画風の字幕を追加する関数
    """
    if not text:
        return clip

    try:
        # 字幕テキストの作成（MoviePy 2.2.1対応）
        txt_clip = TextClip(
            text=text,
            font_size=50,
            color='white',
            font=FONT_PATH,
            stroke_color='black',
            stroke_width=2,
            method='label',
            margin=(0, 30)  # 上下に30ピクセルのマージンを追加
        )
        
        # デバッグ情報を出力
        print(f"  📝 字幕サイズ: {txt_clip.w}x{txt_clip.h}, テキスト: {text[:20]}...")
        
        # 位置合わせ（画面下部 - 大幅に上に移動）
        y_position = H - txt_clip.h - 150
        print(f"  📍 字幕位置: y={y_position}")
        txt_clip = txt_clip.with_position(('center', y_position)).with_duration(clip.duration)
        
        # 合成（サイズを明示的に指定）
        return CompositeVideoClip([clip, txt_clip], size=(W, H))
    except Exception as e:
        print(f"⚠️ 字幕エラー: {e}")
        print("ImageMagickがインストールされていないか、フォントパスが間違っている可能性があります。")
        return clip

def create_title_card(bg_file, main_title, sub_title, duration):
    """
    タイトル画面作成（MoviePy 2.2.1対応）
    """
    try:
        # 背景
        if os.path.exists(bg_file):
            bg = ImageClip(bg_file).with_duration(duration)
            bg = fit_to_screen(bg)
            # 背景を暗くする処理
            bg = bg.with_effects([vfx.MultiplyColor(0.5)])
        else:
            print(f"  ⚠️ 背景ファイルが見つかりません: {bg_file}")
            bg = ColorClip(size=(W, H), color=(40, 30, 60), duration=duration)

        clips = [bg]

        # メインタイトル（中央より少し上に配置）
        if main_title:
            txt_main = TextClip(
                text=main_title,
                font_size=120,
                color='white',
                font=FONT_PATH,
                stroke_color='black',
                stroke_width=3,
                method='label',
                margin=(0, 30)  # 上下に30ピクセルのマージンを追加
            ).with_duration(duration)
            # 中央より少し上に配置
            txt_main = txt_main.with_position(('center', H/2 - txt_main.h/2 - 50))
            txt_main = txt_main.with_effects([vfx.CrossFadeIn(1)])
            print(f"  📝 メインタイトルサイズ: {txt_main.w}x{txt_main.h}")
            clips.append(txt_main)

        # サブタイトル（メインタイトルの下に配置）
        if sub_title:
            txt_sub = TextClip(
                text=sub_title,
                font_size=50,
                color='#ffab91',
                font=FONT_PATH,
                method='label',
                margin=(0, 30)  # 上下に30ピクセルのマージンを追加
            ).with_duration(duration)
            # メインタイトルの下に配置
            txt_sub = txt_sub.with_position(('center', H/2 + 50))
            txt_sub = txt_sub.with_effects([vfx.CrossFadeIn(1.5)])
            print(f"  📝 サブタイトルサイズ: {txt_sub.w}x{txt_sub.h}")
            clips.append(txt_sub)

        # サイズを明示的に指定して合成
        return CompositeVideoClip(clips, size=(W, H))
    except Exception as e:
        print(f"⚠️ タイトル生成エラー: {e}")
        return ColorClip(size=(W, H), color=(0,0,0), duration=duration)

def main():
    print("🎬 編集プロセスを開始します...")
    
    final_clips = []
    
    for i, scene in enumerate(SCENARIO):
        print(f"[{i+1}/{len(SCENARIO)}] 処理中: {scene.get('file', 'Scene')}")
        
        clip = None
        fpath = os.path.join(ASSETS_DIR, scene.get("file", ""))
        
        # タイトルカード処理
        if scene["type"] == "title_card":
            clip = create_title_card(
                fpath,
                scene.get("main_title", ""),
                scene.get("sub_title", ""),
                scene["duration"]
            )
        
        # 素材読み込み
        else:
            try:
                if scene["type"] == "image":
                    if os.path.exists(fpath):
                        img = ImageClip(fpath).with_duration(scene["duration"])
                        clip = fit_to_screen(img)
                    else:
                        print(f"  ❌ ファイルが見つかりません: {fpath}")
                        clip = ColorClip(size=(W, H), color=(0,0,0), duration=scene["duration"])

                elif scene["type"] == "video":
                    if os.path.exists(fpath):
                        vid = VideoFileClip(fpath)
                        # 長さ調整
                        if scene["duration"]:
                            vid = vid.subclipped(0, scene["duration"])
                        clip = fit_to_screen(vid)
                    else:
                        print(f"  ❌ ファイルが見つかりません: {fpath}")
                        clip = ColorClip(size=(W, H), color=(0,0,0), duration=5)
        
            except Exception as e:
                print(f"  ⚠️ 読み込みエラー: {e}")
                continue

        if clip:
            # フェード処理（MoviePy 2.2.1対応）
            clip = clip.with_effects([vfx.CrossFadeIn(0.5), vfx.CrossFadeOut(0.5)])
            
            # 字幕追加
            if "subtitle" in scene:
                clip = add_subtitle(clip, scene["subtitle"])
            
            final_clips.append(clip)

    if not final_clips:
        print("❌ 生成できるクリップがありませんでした。")
        return

    # 全結合
    print("🔗 クリップを結合中...")
    full_video = concatenate_videoclips(final_clips, method="compose")

    # BGM追加
    bgm_path = os.path.join(ASSETS_DIR, BGM_FILE)
    if os.path.exists(bgm_path):
        print("🎵 BGMを追加中...")
        try:
            bgm = AudioFileClip(bgm_path)
            # 動画の長さに合わせてBGMをループまたはカット
            if bgm.duration < full_video.duration:
                # ループ処理
                n_loops = int(np.ceil(full_video.duration / bgm.duration))
                bgm = concatenate_audioclips([bgm] * n_loops)
                bgm = bgm.subclipped(0, full_video.duration)
            else:
                bgm = bgm.subclipped(0, full_video.duration)
            
            bgm = bgm.with_effects([afx.AudioFadeOut(3)])
            # 音量バランス（BGMは少し下げる）
            bgm = bgm.with_volume_scaled(0.6)
            full_video = full_video.with_audio(bgm)
        except Exception as e:
            print(f"BGM Error: {e}")
    else:
        print(f"⚠️ BGMファイルが見つかりません: {bgm_path}")

    # 書き出し
    print(f"💾 エンコード中... {OUTPUT_FILE}")
    full_video.write_videofile(
        OUTPUT_FILE, 
        fps=24, 
        codec='libx264', 
        audio_codec='aac',
        threads=4
    )
    print("✅ 完成しました！お疲れ様でした！")

if __name__ == "__main__":
    # ImageMagickのパス設定が必要な場合はここで指定
    # change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.0-Q16-HDRI\magick.exe"})
    main()