import csv
import hashlib
import os
import asyncio
import edge_tts

csv_path = "/app/ep100 dd - Sheet1.csv"
output_dir = "/app/.translation-cache/edge-tts-audio-output"
os.makedirs(output_dir, exist_ok=True)

# -----------------------------
# Voice selection
# -----------------------------
def get_ru_voice(speaker):
    match speaker:
        case "HOST":
            return "ru-RU-SvetlanaNeural", "0%"
        case "BRUCE":
            return "ru-RU-DmitryNeural", "-100%"
        case "DD":
            return "ru-RU-DmitryNeural", "0%"
        case "SRGHMA":
            return "ru-RU-SvetlanaNeural", "+100%"
        case _:
            raise ValueError(f"Unknown speaker: {speaker}")

def get_ua_voice(speaker):
    match speaker:
        case "HOST":
            return "uk-UA-PolinaNeural", "0%"
        case "BRUCE":
            return "uk-UA-OstapNeural", "-100%"
        case "DD":
            return "uk-UA-OstapNeural", "0%"
        case "SRGHMA":
            return "uk-UA-PolinaNeural", "+100%"
        case _:
            raise ValueError(f"Unknown speaker: {speaker}")

# -----------------------------
# Utility functions
# -----------------------------
def hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def make_filename(lang: str, speaker: str, pitch: str, text: str) -> str:
    h = hash_text(f"{lang}-{text}")
    return f"{lang}-{speaker}-{pitch}-{h}.mp3"

async def generate_tts(text: str, voice: str, pitch: str, out_path: str):
    if pitch != "0%":
        ssml_text = f'<speak><prosody pitch="{pitch}">{text}</prosody></speak>'
    else:
        ssml_text = text

    communicate = edge_tts.Communicate(ssml_text, voice)
    await communicate.save(out_path)

def generate_tts_sync(text, voice, pitch, out_path):
    asyncio.run(generate_tts(text, voice, pitch, out_path))

def strip_and_split(text: str) -> list[str]:
    return [line.strip() for line in text.strip().split('\n') if line.strip()]

# -----------------------------
# Main processing
# -----------------------------
def process_sentence(lang: str, speaker: str, text: str):
    if lang == "ru":
        voice, pitch = get_ru_voice(speaker)
    elif lang == "ua":
        voice, pitch = get_ua_voice(speaker)
    else:
        raise ValueError("Unsupported language")

    filename = make_filename(lang, speaker, pitch, text)
    out_path = os.path.join(output_dir, filename)

    if os.path.exists(out_path):
        print(f"✓ Skipped ({lang}): {text}")
        return

    print(f"→ Generating ({lang}): {text}")
    generate_tts_sync(text, voice, pitch, out_path)

def process_sentences(lang, speaker, sentences, counters):
    get_voice = get_ru_voice if lang == "ru" else get_ua_voice

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        counters["total"] += 1

        try:
            pitch = get_voice(speaker)[1]
            filename = make_filename(lang, speaker, pitch, sentence)
            filepath = os.path.join(output_dir, filename)
            file_existed = os.path.exists(filepath)

            process_sentence(lang, speaker, sentence)

            if file_existed and os.path.exists(filepath):
                counters["skipped"] += 1
            else:
                counters["generated"] += 1

        except Exception as e:
            print(f"⚠️ Error ({lang}): {sentence} — {e}")

def main():
    counters = {"total": 0, "generated": 0, "skipped": 0}

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 4:
                continue

            en, speaker, ru, ua = row
            ru_sentences = strip_and_split(ru)
            ua_sentences = strip_and_split(ua)

            process_sentences("ru", speaker, ru_sentences, counters)
            process_sentences("ua", speaker, ua_sentences, counters)

    print(f"\n🎉 Done! {counters['generated']} generated, {counters['skipped']} skipped, {counters['total']} total sentences.")

if __name__ == "__main__":
    main()
