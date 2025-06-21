import csv
import os
import subprocess
import tempfile
import hashlib
import concurrent.futures
from ep100renderslides import strip_and_split, make_slide_filename
from ep100renderaudio import make_filename, get_ru_voice, get_ua_voice

# Paths and constants
csv_path = "/app/ep100 dd - Sheet1.csv"
tts_output_dir = "/app/.translation-cache/edge-tts-audio-fixed-output"
slides_output_dir = "/app/.translation-cache/edge-tts-slides-output"
clips_cache_dir = "/app/.translation-cache/edge-tts-clips-output"
video_output_dir = "/home/srghma/Videos"  # Directory for output videos
LANGS = ["ru", "ua"]
WIDTH, HEIGHT = 1280, 720

# Ensure cache directory exists
os.makedirs(clips_cache_dir, exist_ok=True)


def load_sentences():
    """Loads and parses sentence data from the CSV file."""
    data = []
    try:
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
                    print(f"❌ Line count mismatch for speaker {speaker}, skipping row.")
                    continue
                for en_line, ru_line, ua_line in zip(en_lines, ru_lines, ua_lines):
                    data.append((speaker, en_line, {"ru": ru_line, "ua": ua_line}))
    except FileNotFoundError:
        print(f"❌ Error: CSV file not found at {csv_path}")
        return None
    return data


def get_audio_path(lang, speaker, text):
    """Constructs the full path to an audio file."""
    get_voice = get_ru_voice if lang == "ru" else get_ua_voice
    voice, pitch = get_voice(speaker)
    filename = make_filename(lang, speaker, pitch, text)
    return os.path.join(tts_output_dir, filename)


def get_slide_path(lang, speaker, text):
    """Constructs the full path to a slide image file."""
    filename = make_slide_filename(lang, speaker, text)
    return os.path.join(slides_output_dir, filename)


def get_file_hash(filepath):
    """Calculates the MD5 hash of a file, returning None if the file doesn't exist."""
    if not os.path.exists(filepath):
        return None
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_clip_cache_path(lang, speaker, text):
    """
    Generates a unique, deterministic cache filename for a clip based on its dependencies.
    The hash includes the content (lang, speaker, text), video dimensions,
    and the file hashes of the source audio and slide image.
    """
    slide_path = get_slide_path(lang, speaker, text)
    audio_path = get_audio_path(lang, speaker, text)

    hash_input = f"{lang}:{speaker}:{text}:{WIDTH}:{HEIGHT}"

    slide_hash = get_file_hash(slide_path)
    audio_hash = get_file_hash(audio_path)

    if slide_hash:
        hash_input += f":slide:{slide_hash}"
    if audio_hash:
        hash_input += f":audio:{audio_hash}"

    clip_hash = hashlib.md5(hash_input.encode()).hexdigest()
    return os.path.join(clips_cache_dir, f"clip_{lang}_{clip_hash}.mp4")


def create_video_with_ffmpeg(image_path, audio_path, output_path):
    """Creates a video clip from a single image and audio file using ffmpeg."""
    cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', image_path,
        '-i', audio_path,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-shortest',
        '-pix_fmt', 'yuv420p',
        '-vf', f'scale={WIDTH}:{HEIGHT}',
        output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ffmpeg error while creating {os.path.basename(output_path)}:\n{e.stderr}")
        return False


def get_or_create_clip(lang, speaker, text):
    """
    Main worker function. Checks for a cached clip and creates it if it doesn't exist
    or if its source files have changed. This is the function run in parallel.
    """
    cached_clip_path = get_clip_cache_path(lang, speaker, text)

    # 1. Check if a valid cached clip already exists.
    if os.path.exists(cached_clip_path):
        print(f"💾 Using cached {lang} clip: {os.path.basename(cached_clip_path)}")
        return cached_clip_path

    # 2. If not cached, check for source files.
    slide_path = get_slide_path(lang, speaker, text)
    audio_path = get_audio_path(lang, speaker, text)
    if not os.path.exists(slide_path):
        print(f"❌ Missing slide for {lang}: {os.path.basename(slide_path)}")
        return None
    if not os.path.exists(audio_path):
        print(f"❌ Missing audio for {lang}: {os.path.basename(audio_path)}")
        return None

    # 3. Create new clip.
    print(f"🔨 Creating new {lang} clip for text: '{text[:30]}...'")
    if create_video_with_ffmpeg(slide_path, audio_path, cached_clip_path):
        print(f"✅ Cached {lang} clip: {os.path.basename(cached_clip_path)}")
        return cached_clip_path
    else:
        print(f"❌ Failed to create {lang} clip for text: '{text[:30]}...'")
        return None


def build_video_for_language(lang):
    """
    Builds the final concatenated video for a specific language by creating
    individual clips in parallel.
    """
    sentence_data = load_sentences()
    if not sentence_data:
        return False

    video_output_path = os.path.join(video_output_dir, f"ep100-compiled-{lang}.mp4")

    # Use a ProcessPoolExecutor to run clip creation in parallel.
    # It will use up to the number of CPU cores on the machine.
    max_workers = os.cpu_count()
    print(f"⚙️ Submitting {len(sentence_data)} clip creation jobs to {max_workers} parallel workers...")

    futures = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        for speaker, _, lang_texts in sentence_data:
            text = lang_texts[lang]
            # Submit the job to the pool. It will run get_or_create_clip in a separate process.
            future = executor.submit(get_or_create_clip, lang, speaker, text)
            futures.append(future)

    # Collect the results. futures are in the original submission order.
    # future.result() will wait for each specific job to complete, ensuring
    # the final `valid_clips` list is in the correct sequence.
    valid_clips = []
    print(f"\n⏳ Waiting for {len(futures)} clip jobs to complete...")
    for i, future in enumerate(futures):
        try:
            clip_path = future.result()
            if clip_path:
                valid_clips.append(clip_path)
            else:
                # This handles cases where get_or_create_clip returned None (e.g., missing source file).
                print(f"↪️ Skipping clip #{i+1} for {lang.upper()} (task completed but no valid path returned).")
        except Exception as e:
            print(f"❌ Clip #{i+1} for {lang.upper()} failed with an exception: {e}")

    if not valid_clips:
        print(f"❌ No valid clips were created for {lang.upper()}. Aborting video creation.")
        return False

    print(f"\n📊 {lang.upper()}: Assembling final video from {len(valid_clips)} clips.")

    # Create a temporary file for ffmpeg's concat demuxer.
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        concat_file = f.name
        for clip_path in valid_clips:
            # Use single quotes to handle potential spaces or special characters in paths.
            f.write(f"file '{os.path.abspath(clip_path)}'\n")

    # Concatenate all videos using the generated file list.
    concat_cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c', 'copy', # Fast copy, no re-encoding.
        video_output_path
    ]

    try:
        print(f"ffmpeg concat command: {' '.join(concat_cmd)}")
        subprocess.run(concat_cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        print(f"🎬 {lang.upper()} video saved to: {video_output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {lang.upper()} concatenation with stream copy failed. Retrying with re-encoding.")
        print(f"ffmpeg error: {e.stderr}")

        # Fallback: re-encode if stream copy fails (e.g., due to format inconsistencies).
        fallback_cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-pix_fmt', 'yuv420p',
            video_output_path
        ]
        try:
            subprocess.run(fallback_cmd, capture_output=True, text=True, check=True, encoding='utf-8')
            print(f"🎬 {lang.upper()} video saved to: {video_output_path} (with re-encoding)")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"❌ Final {lang.upper()} concatenation failed even with re-encoding.")
            print(f"ffmpeg error: {e2.stderr}")
            return False
    finally:
        os.unlink(concat_file) # Clean up the temporary file.


def build_videos_for_all_languages():
    """Main function to orchestrate the build process for all specified languages."""
    print("🎬 Starting video creation for all languages...")
    print(f"📁 Clips will be cached in: {clips_cache_dir}")

    for lang in LANGS:
        print(f"\n{'='*15} Processing {lang.upper()} video {'='*15}")
        success = build_video_for_language(lang)
        if success:
            print(f"✅ {lang.upper()} video completed successfully.")
        else:
            print(f"❌ {lang.upper()} video creation failed.")

    print("\n🎉 All video processing finished!")


if __name__ == "__main__":
    build_videos_for_all_languages()
    # subprocess.run("cp /app/ep100-compiled-* /home/srghma/Videos", capture_output=True, text=True, check=True, encoding='utf-8')
