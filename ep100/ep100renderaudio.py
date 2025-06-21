import csv
import hashlib
import os
import asyncio
import edge_tts
import tempfile
import soundfile as sf
from tts_utils import pad_array, verify_saved_file_and_size

# pip install edge_tts=7.0.2

# --- Configuration ---
csv_path = "/app/ep100 dd - Sheet1.csv"
output_dir = "/app/.translation-cache/edge-tts-audio-output"
os.makedirs(output_dir, exist_ok=True)

# -----------------------------
# Voice selection
# -----------------------------
def get_ru_voice(speaker):
    match speaker:
        case "HOST":
            return "ru-RU-SvetlanaNeural", "+0Hz"
        case "BRUCE":
            return "ru-RU-DmitryNeural", "-20Hz"
        case "DD":
            return "ru-RU-DmitryNeural", "+0Hz"
        case "SRGHMA":
            return "ru-RU-SvetlanaNeural", "+20Hz"
        case _:
            raise ValueError(f"Unknown speaker: {speaker}")

def get_ua_voice(speaker):
    match speaker:
        case "HOST":
            return "uk-UA-PolinaNeural", "+0Hz"
        case "BRUCE":
            return "uk-UA-OstapNeural", "-20Hz"
        case "DD":
            return "uk-UA-OstapNeural", "+0Hz"
        case "SRGHMA":
            return "uk-UA-PolinaNeural", "+20Hz"
        case _:
            raise ValueError(f"Unknown speaker: {speaker}")

# -----------------------------
# Utility functions
# -----------------------------
def hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def make_filename(lang: str, speaker: str, pitch: str, text: str) -> str:
    # Sanitize pitch for filename
    sanitized_pitch = pitch.replace('+', 'p').replace('-', 'm').replace('Hz', '')
    h = hash_text(text)
    return f"{lang}-{speaker}-{sanitized_pitch}-{h}.mp3"

def strip_and_split(text: str) -> list[str]:
    return [line.strip() for line in text.strip().split('\n') if line.strip()]

async def generate_and_trim_tts(text: str, voice: str, pitch: str, final_out_path: str):
    """
    Generates TTS audio, saves it to a temporary file,
    trims silence, and saves the result to the final path.
    """
    # Use a temporary file to store the initial output from edge-tts
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tmpfile:
        temp_filename = tmpfile.name

        # 1. Generate TTS and save to temporary file
        communicate = edge_tts.Communicate(text, voice, rate="+30%", pitch=pitch)
        await communicate.save(temp_filename)

        # 2. Read the audio data from the temporary file
        data, sample_rate = sf.read(temp_filename)

        # 3. Trim silence from the beginning and end of the audio data
        trimmed_data = pad_array(data, sample_rate)

        # 4. Save the trimmed audio to the final destination
        sf.write(final_out_path, trimmed_data, sample_rate)

        # 5. Verify the final file was created and is not empty
        verify_saved_file_and_size(final_out_path)


async def process_sentence(lang: str, speaker: str, text: str):
    """Processes a single sentence: generates and saves trimmed TTS audio."""
    if lang == "ru":
        voice, pitch = get_ru_voice(speaker)
    elif lang == "ua":
        voice, pitch = get_ua_voice(speaker)
    else:
        raise ValueError("Unsupported language")

    filename = make_filename(lang, speaker, pitch, text)
    out_path = os.path.join(output_dir, filename)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"✓ Skipped ({lang}): {text}")
        return False # Indicates skipped

    print(f"→ Generating ({lang}): {text}")
    await generate_and_trim_tts(text, voice, pitch, out_path)
    return True # Indicates generated

async def main():
    """Main function to read CSV and process all sentences."""
    counters = {"total": 0, "generated": 0, "skipped": 0}

    with open(csv_path, newline='', encoding='utf-8') as f:
        # Skip header if it exists
        # next(f, None)
        reader = csv.reader(f)
        tasks = []
        for row in reader:
            if len(row) != 4:
                continue

            _, speaker, ru, ua = row

            ru_sentences = strip_and_split(ru)
            ua_sentences = strip_and_split(ua)

            for sentence in ru_sentences:
                counters["total"] += 1
                try:
                    was_generated = await process_sentence("ru", speaker, sentence)
                    if was_generated:
                        counters["generated"] += 1
                    else:
                        counters["skipped"] += 1
                except Exception as e:
                    print(f"⚠️ Error (ru) for '{sentence}': {e}")

            for sentence in ua_sentences:
                counters["total"] += 1
                try:
                    was_generated = await process_sentence("ua", speaker, sentence)
                    if was_generated:
                        counters["generated"] += 1
                    else:
                        counters["skipped"] += 1
                except Exception as e:
                    print(f"⚠️ Error (ua) for '{sentence}': {e}")


    print(f"\n🎉 Done! {counters['generated']} generated, {counters['skipped']} skipped, {counters['total']} total sentences.")

if __name__ == "__main__":
    # Note: The original script was running asyncio.run in a loop, which is inefficient.
    # This revised version runs the async processing inside a single main async function.
    asyncio.run(main())
