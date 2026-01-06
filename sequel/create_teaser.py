import os
from moviepy.editor import *
from moviepy.video.fx.all import crop, resize, fadein, fadeout

# ==========================================
# 設定エリア
# ==========================================
ASSETS_DIR = "assets"      # 素材フォルダ
OUTPUT_FILE = "kitchen_ranger_teaser.mp4"
BGM_FILE = "audio/bgm/true_ed.mp3" 

# ターゲット解像度 (Full HD)
W, H = 1920, 1080

def fit_to_screen(clip):
    """
    クリップを画面サイズ(W, H)に合わせて調整する関数
    - 横長素材: アスペクト比維持で拡大し、中央をクロップ
    - 縦長素材: 左右にブラー（ぼかし）背景を追加して横長にする
    """
    # アスペクト比を計算
    clip_ratio = clip.w / clip.h
    target_ratio = W / H
    
    if clip_ratio < target_ratio:
        # 【縦長の場合】左右に黒帯（またはブラー）を入れる
        # 1. メインの動画を高さに合わせてリサイズ
        main_content = clip.resize(height=H)
        
        # 2. 背景用に動画を拡大・ブラー処理（おしゃれに見せる）
        # 背景は画面幅に合わせてリサイズし、クロップしてブラー
        bg_content = clip.resize(width=W)
        bg_content = bg_content.crop(x1=0, y1=bg_content.h/2 - H/2, width=W, height=H)
        # MoviePyには標準でガウシアンブラーがないため、ここでは暗くする処理で代用
        # (ImageMagickが使える環境なら .fx(vfx.blur, ...) が可能)
        bg_content = bg_content.fl_image(lambda image: image * 0.3) # 輝度を30%に落とす
        
        # 3. 合成 (背景の上にメイン動画を中央配置)
        final_clip = CompositeVideoClip([bg_content, main_content.set_position("center")])
        final_clip.duration = clip.duration
        return final_clip
        
    else:
        # 【横長の場合】今まで通り、高さに合わせてリサイズして中央クロップ
        clip = clip.resize(height=H)
        if clip.w > W:
            clip = clip.crop(x1=clip.w/2 - W/2, width=W, height=H)
        return clip

def create_slide(image_path, duration=3.0, zoom_effect=True):
    """
    静止画から「動くスライド」を作成
    """
    try:
        clip = ImageClip(image_path).set_duration(duration)
        
        # 画面サイズにフィットさせる（縦長画像対策も含む）
        clip = fit_to_screen(clip)

        # ズームイン効果 (Ken Burns) - 縦長対応後のクリップに適用
        # ※CompositeVideoClipにはresize(t)が直接効かない場合があるので注意
        # ここでは簡易的に、fit_to_screenで処理されたクリップをそのまま使う
        
        clip = clip.fadein(0.5).fadeout(0.5)
        return clip
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None

def create_video_clip(video_path, duration=None):
    """
    動画素材を読み込む
    """
    try:
        clip = VideoFileClip(video_path)
        
        if duration:
            clip = clip.subclip(0, duration)
            
        # 画面サイズにフィット（縦長動画対策）
        clip = fit_to_screen(clip)
            
        clip = clip.fadein(0.5).fadeout(0.5)
        return clip
    except Exception as e:
        print(f"Error loading video {video_path}: {e}")
        return None

def main():
    print("🎬 映像生成を開始します...")
    clips = []
    
    # --- 素材リスト (ファイル名は台本に合わせて変更してください) ---
    
    # Scene 1: 背景画 (静止画)
    if os.path.exists("bg_foodtruck_anime.jpg"):
        clips.append(create_slide("bg_foodtruck_anime.jpg", duration=4.0))
    else:
         clips.append(TextClip("Scene 1: Truck", fontsize=70, color='white', size=(W,H)).set_duration(3))

    # Scene 2: 梨奈OPEN (動画)
    if os.path.exists("visual_2_rina_open.mp4"):
        clips.append(create_video_clip("visual_2_rina_open.mp4"))

    # Scene 3: ステーキ (動画) - ここが縦長でもOK
    if os.path.exists("visual_3_steak_sizzle.mp4"):
        clips.append(create_video_clip("visual_3_steak_sizzle.mp4"))
    
    # Scene 4: 攻防 (静止画)
    if os.path.exists("visual_4_conflict.jpg"):
        clips.append(create_slide("visual_4_conflict.jpg", duration=4.0))

    # Scene 5: 味見 (動画)
    if os.path.exists("visual_5_rina_tasting.mp4"):
        clips.append(create_video_clip("visual_5_rina_tasting.mp4"))
    
    # Scene 6: 夕暮れ (動画)
    if os.path.exists("visual_6_sunset_ending.mp4"):
        clips.append(create_video_clip("visual_6_sunset_ending.mp4"))

    # -------------------------------------------------
    
    if not clips:
        print("❌ 素材が見つかりませんでした。")
        return

    final_video = concatenate_videoclips(clips, method="compose")
    
    # BGM設定
    try:
        bgm_path = "audio/bgm/true_ed.mp3" 
        if os.path.exists(bgm_path):
            bgm = AudioFileClip(bgm_path).subclip(0, final_video.duration)
            bgm = bgm.audio_fadeout(2.0)
            final_video = final_video.set_audio(bgm)
    except Exception as e:
        print(f"BGM Error: {e}")

    print(f"💾 書き出し中... {OUTPUT_FILE}")
    final_video.write_videofile(OUTPUT_FILE, fps=24)
    print("✅ 完了！")

if __name__ == "__main__":
    main()