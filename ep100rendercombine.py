import csv
import os
import hashlib
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import ImageFont
from ep100renderslides import strip_and_split, make_slide_filename
from ep100renderaudio import make_filename, get_ru_voice, get_ua_voice, output_dir as tts_output_dir
from moviepy.config import check

check()

# Paths
csv_path = "/app/ep100 dd - Sheet1.csv"
slides_output_dir = "/app/.translation-cache/edge-tts-slides-output"
video_output_path = "/app/ep100-compiled.mp4"

# Constants
LANGS = ["ru", "ua"]
DURATION_PER_CHAR = 0.05  # fallback duration if audio not found

# Video dimensions
WIDTH, HEIGHT = 1280, 720

# Load font for fallback duration estimation
FONT_RU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(FONT_RU, 58)

def is_valid_audio_file(path: str) -> bool:
    return os.path.exists(path) and os.path.getsize(path) > 1000  # 1KB minimum

def hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_sentences():
    data = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 4:
                continue
            en, speaker, ru, ua = row
            en_lines = strip_and_split(en)
            ru_lines = strip_and_split(ru)
            ua_lines = strip_and_split(ua)

            if not (len(en_lines) == len(ru_lines) == len(ua_lines)):
                print(f"❌ Sentence mismatch for speaker {speaker}")
                continue

            for en_line, ru_line, ua_line in zip(en_lines, ru_lines, ua_lines):
                data.append((speaker, en_line, {"ru": ru_line, "ua": ua_line}))
    return data

def get_audio_path(lang, speaker, text):
    get_voice = get_ru_voice if lang == "ru" else get_ua_voice
    _, pitch = get_voice(speaker)
    filename = make_filename(lang, speaker, pitch, text)
    return os.path.join(tts_output_dir, filename)

def get_slide_path(lang, speaker, text):
    filename = make_slide_filename(lang, speaker, text)
    return os.path.join(slides_output_dir, filename)

def make_clip(image_path, audio_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Missing image: {image_path}")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Missing audio: {audio_path}")

    if not is_valid_audio_file(audio_path):
        raise ValueError(f"Invalid audio file: {audio_path}")

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    img_clip = ImageClip(image_path).with_duration(duration).resized((WIDTH, HEIGHT)).with_audio(audio)

    return img_clip

def build_video():
    all_clips = []

    for speaker, en_text, lang_texts in load_sentences():
        for lang in LANGS:
            slide_path = get_slide_path(lang, speaker, lang_texts[lang])
            audio_path = get_audio_path(lang, speaker, lang_texts[lang])
            clip = make_clip(slide_path, audio_path)
            all_clips.append(clip)

    if not all_clips:
        print("❌ No clips generated")
        return

    final_video = concatenate_videoclips(all_clips, method="compose")
    final_video.write_videofile(video_output_path, fps=24, codec="libx264", audio_codec="aac")
    print(f"🎬 Video saved to: {video_output_path}")

if __name__ == "__main__":
    build_video()
