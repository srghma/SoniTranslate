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
tts_output_dir = "/app/.translation-cache/edge-tts-audio-output"
slides_output_dir = "/app/.translation-cache/edge-tts-slides-output"
clips_cache_dir = "/app/.translation-cache/edge-tts-clips-output"
video_output_dir = "/home/srghma/Videos"  # Directory for output videos
LANGS = ["ru", "ua"]
WIDTH, HEIGHT = 1280, 720
FRAME_RATE = 25  # <<< NEW: Standard frame rate for all clips

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
    The hash includes the content (lang, speaker, text), video dimensions, frame rate,
    and the file hashes of the source audio and slide image.
    """
    slide_path = get_slide_path(lang, speaker, text)
    audio_path = get_audio_path(lang, speaker, text)

    # <<< MODIFIED: Added FRAME_RATE to the hash to ensure cache invalidation
    hash_input = f"{lang}:{speaker}:{text}:{WIDTH}:{HEIGHT}:{FRAME_RATE}"

    slide_hash = get_file_hash(slide_path)
    audio_hash = get_file_hash(audio_path)

    if slide_hash:
        hash_input += f":slide:{slide_hash}"
    if audio_hash:
        hash_input += f":audio:{audio_hash}"

    clip_hash = hashlib.md5(hash_input.encode()).hexdigest()
    return os.path.join(clips_cache_dir, f"clip_{lang}_{clip_hash}.mp4")


# <<< NEW: Helper function to get audio duration using ffprobe
def get_audio_duration(audio_path):
    """Gets the duration of an audio file in seconds using ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        print(f"❌ Error getting duration for {os.path.basename(audio_path)}: {e}")
        return None


# <<< MODIFIED: This function is the core of the fix.
def create_video_with_ffmpeg(image_path, audio_path, output_path):
    """
    Creates a video clip with a proper video stream (not single-frame),
    making it suitable for fast concatenation.
    """
    # 1. Get the exact audio duration to set the clip length
    duration = get_audio_duration(audio_path)
    if duration is None:
        return False  # Cannot proceed without duration

    cmd = [
        'ffmpeg', '-y',
        '-loop', '1',              # Loop the input image to create a continuous stream
        '-i', image_path,
        '-i', audio_path,
        '-c:v', 'libx264',
        '-tune', 'stillimage',     # Optimize libx264 for static images
        '-c:a', 'aac',
        '-pix_fmt', 'yuv420p',
        '-r', str(FRAME_RATE),     # Set a standard frame rate
        '-vf', f'scale={WIDTH}:{HEIGHT}',
        '-t', str(duration),       # Set the exact output duration to match the audio
        output_path
    ]
    # Note: We replaced '-shortest' with '-loop 1', '-r', and '-t <duration>'.

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
        # This message is now more informative for debugging.
        # print(f"💾 Using cached {lang} clip: {os.path.basename(cached_clip_path)}")
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

    max_workers = os.cpu_count()
    print(f"⚙️ Submitting {len(sentence_data)} clip creation jobs to {max_workers} parallel workers...")

    futures = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        for speaker, _, lang_texts in sentence_data:
            text = lang_texts[lang]
            future = executor.submit(get_or_create_clip, lang, speaker, text)
            futures.append(future)

    valid_clips = []
    print(f"\n⏳ Waiting for {len(futures)} clip jobs to complete...")
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        try:
            clip_path = future.result()
            if clip_path:
                valid_clips.append(clip_path)
            # The list 'valid_clips' will be out of order here, but the concat file will be created later from an ordered list.
        except Exception as e:
            print(f"❌ A clip creation task failed with an exception: {e}")
    
    # Re-create the ordered list of clips now that all futures are complete.
    # This ensures the final video is in the correct sequence.
    ordered_valid_clips = []
    for future in futures:
        if future.done() and not future.cancelled() and future.exception() is None:
            clip_path = future.result()
            if clip_path:
                ordered_valid_clips.append(clip_path)

    if not ordered_valid_clips:
        print(f"❌ No valid clips were created for {lang.upper()}. Aborting video creation.")
        return False

    print(f"\n📊 {lang.upper()}: Assembling final video from {len(ordered_valid_clips)} clips.")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        concat_file = f.name
        for clip_path in ordered_valid_clips:
            f.write(f"file '{os.path.abspath(clip_path)}'\n")

    # Concatenate all videos using the generated file list.
    # This should now work reliably and quickly.
    concat_cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c', 'copy', # Fast copy, no re-encoding.
        video_output_path
    ]

    try:
        print(f"Running fast concat command: {' '.join(concat_cmd)}")
        subprocess.run(concat_cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        print(f"🎬 {lang.upper()} video saved to: {video_output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {lang.upper()} concatenation with stream copy failed. This shouldn't happen with the new clips.")
        print(f"ffmpeg error: {e.stderr}")
        # The fallback is kept just in case, but it should not be needed anymore.
        fallback_cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p',
            video_output_path
        ]
        try:
            print("Retrying with full re-encoding...")
            subprocess.run(fallback_cmd, capture_output=True, text=True, check=True, encoding='utf-8')
            print(f"🎬 {lang.upper()} video saved to: {video_output_path} (with re-encoding)")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"❌ Final {lang.upper()} concatenation failed even with re-encoding.")
            print(f"ffmpeg error: {e2.stderr}")
            return False
    finally:
        os.unlink(concat_file)


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
