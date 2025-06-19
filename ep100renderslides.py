import csv
import os
from PIL import Image, ImageDraw, ImageFont
import hashlib
import textwrap

# rm -frd /app/.translation-cache/edge-tts-slides-output && python ep100render-slides.py

csv_path = "/app/ep100 dd - Sheet1.csv"
slides_output_dir = "/app/.translation-cache/edge-tts-slides-output"
os.makedirs(slides_output_dir, exist_ok=True)

WIDTH, HEIGHT = 1280, 720
FONT_EN = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_RU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

speaker_colors = {
    "DD": "black",
    "HOST": "#002b00",    # black green
    "BRUCE": "#2b0000",   # black red
    "SRGHMA": "#2b0014",  # black pink
}

def hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def make_slide_filename(lang, speaker, text):
    h = hash_text(text)
    return f"{lang}-{speaker}-{h}.png"

def draw_centered(draw, text, font, y, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((WIDTH - w) / 2, y), text, font=font, fill=fill)

def get_text_size(font, text):
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    return w, h

def draw_multiline_text(draw, text, font, box, fill):
    """
    Draw multiline text centered horizontally and wrapped to fit box width.

    Args:
        draw: ImageDraw object
        text: string to draw
        font: PIL ImageFont
        box: (x0, y0, x1, y1) bounding box for text
        fill: text color
    """
    max_width = box[2] - box[0]
    max_height = box[3] - box[1]

    avg_char_width, _ = get_text_size(font, 'A')
    max_chars_per_line = max_width // avg_char_width

    lines = textwrap.wrap(text, width=int(max_chars_per_line))

    line_height = get_text_size(font, 'A')[1] + 4
    total_text_height = line_height * len(lines)

    original_size = font.size
    while total_text_height > max_height and font.size > 10:
        font = ImageFont.truetype(font.path, font.size - 2)
        avg_char_width, _ = get_text_size(font, 'A')
        max_chars_per_line = max_width // avg_char_width
        lines = textwrap.wrap(text, width=int(max_chars_per_line))
        line_height = get_text_size(font, 'A')[1] + 4
        total_text_height = line_height * len(lines)

    y_text = box[1] + (max_height - total_text_height) / 2

    for line in lines:
        w, h = get_text_size(font, line)
        x_text = box[0] + (max_width - w) / 2
        draw.text((x_text, y_text), line, font=font, fill=fill)
        y_text += line_height

def generate_slide_image(en_text, lang_text, speaker, lang, out_path):
    bg_color = speaker_colors.get(speaker, "black")
    img = Image.new("RGB", (WIDTH, HEIGHT), color=bg_color)
    draw = ImageDraw.Draw(img)

    font_en = ImageFont.truetype(FONT_EN, 50)
    font_lang = ImageFont.truetype(FONT_RU, 58)

    # Define bounding boxes
    en_box = (50, HEIGHT * 0.15, WIDTH - 50, HEIGHT * 0.50)   # upper half-ish
    lang_box = (50, HEIGHT * 0.55, WIDTH - 50, HEIGHT * 0.85) # lower half-ish

    draw_multiline_text(draw, en_text, font_en, en_box, "#cccccc")  # greyish
    draw_multiline_text(draw, lang_text, font_lang, lang_box, "white")

    img.save(out_path)

def strip_and_split(text):
    return [line.strip() for line in text.strip().split('\n') if line.strip()]

def process_slide(lang, speaker, en_text, lang_text):
    filename = make_slide_filename(lang, speaker, lang_text)
    path = os.path.join(slides_output_dir, filename)

    if os.path.exists(path):
        print(f"✓ Slide exists ({lang}): {lang_text}")
        return

    print(f"→ Generating slide ({lang}): {lang_text}")
    generate_slide_image(en_text, lang_text, speaker, lang, path)


def print_sentences(label, sentences):
    print(f"{label} ({len(sentences)} sentences):")
    for i, s in enumerate(sentences, 1):
        print(f"  {i}: {repr(s)}")

def print_aligned_sentences(en_sentences, other_sentences, label):
    max_len = max(len(en_sentences), len(other_sentences))
    print(f"\n📋 Alignment EN vs {label}:")
    for i in range(max_len):
        en = en_sentences[i] if i < len(en_sentences) else "❌ MISSING"
        other = other_sentences[i] if i < len(other_sentences) else "❌ MISSING"
        print(f"[{i+1}]")
        print(f"  EN: {repr(en)}")
        print(f"  {label}: {repr(other)}")
        print("-" * 40)

def check_sentence_counts(speaker, en_sentences, ru_sentences, ua_sentences):
    if len(ru_sentences) != len(en_sentences):
        print(f"\n⚠️ Sentence count mismatch for speaker '{speaker}' (EN vs RU):")
        print_aligned_sentences(en_sentences, ru_sentences, "RU")
        raise ValueError(f"RU sentence count {len(ru_sentences)} != EN sentence count {len(en_sentences)} for speaker {speaker}")

    if len(ua_sentences) != len(en_sentences):
        print(f"\n⚠️ Sentence count mismatch for speaker '{speaker}' (EN vs UA):")
        print_aligned_sentences(en_sentences, ua_sentences, "UA")
        raise ValueError(f"UA sentence count {len(ua_sentences)} != EN sentence count {len(en_sentences)} for speaker {speaker}")

def main():
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 4:
                continue

            en, speaker, ru, ua = row

            # Split sentences
            en_sentences = strip_and_split(en)
            ru_sentences = strip_and_split(ru)
            ua_sentences = strip_and_split(ua)

            check_sentence_counts(speaker, en_sentences, ru_sentences, ua_sentences)

            # Process slides pairwise for RU
            for en_sentence, ru_sentence in zip(en_sentences, ru_sentences):
                process_slide("ru", speaker, en_sentence, ru_sentence)

            # Process slides pairwise for UA
            for en_sentence, ua_sentence in zip(en_sentences, ua_sentences):
                process_slide("ua", speaker, en_sentence, ua_sentence)


if __name__ == "__main__":
    main()
