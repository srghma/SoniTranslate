import os
import glob
import copy
from itertools import chain
from tqdm import tqdm
from deep_translator import GoogleTranslator

def get_srt_files(downloads_dir):
    return glob.glob(os.path.join(downloads_dir, "**", "*.srt"), recursive=True)

def read_srt_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.readlines()

def write_srt_file(file_path, lines):
    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(lines)

def translate_batch(segments, target, chunk_size=2000, source=None):
    """
    Translate a batch of text segments into the specified language in chunks,
        respecting the character limit.

    Parameters:
    - segments (list): List of dictionaries with 'text' as a key for segment
        text.
    - target (str): Target language code.
    - chunk_size (int, optional): Maximum character limit for each translation
        chunk (default is 2000; max 5000).
    - source (str, optional): Source language code. Defaults to None.

    Returns:
    - list: Translated text segments in the target language.

    Notes:
    - Splits input segments into chunks respecting the character limit for
        translation.
    - Translates the chunks using Google Translate.
    - If chunked translation fails, switches to iterative translation using
        `translate_iterative()`.

    Example:
    segments = [{'text': 'first segment.'}, {'text': 'second segment.'}]
    translated = translate_batch(segments, 'es', chunk_size=4000, source='en')
    """

    segments_copy = copy.deepcopy(segments)

    if (
        not source
    ):
        print("No source language")
        source = "auto"

    # Get text
    text_lines = []
    for line in range(len(segments_copy)):
        text = segments_copy[line]["text"].strip()
        text_lines.append(text)

    # chunk limit
    text_merge = []
    actual_chunk = ""
    global_text_list = []
    actual_text_list = []
    for one_line in text_lines:
        one_line = " " if not one_line else one_line
        if (len(actual_chunk) + len(one_line)) <= chunk_size:
            if actual_chunk:
                actual_chunk += " ||||| "
            actual_chunk += one_line
            actual_text_list.append(one_line)
        else:
            text_merge.append(actual_chunk)
            actual_chunk = one_line
            global_text_list.append(actual_text_list)
            actual_text_list = [one_line]
    if actual_chunk:
        text_merge.append(actual_chunk)
        global_text_list.append(actual_text_list)

    # translate chunks
    progress_bar = tqdm(total=len(segments), desc="Translating")
    translator = GoogleTranslator(source=source, target=target)
    split_list = []
    try:
        for text, text_iterable in zip(text_merge, global_text_list):
            translated_line = translator.translate(text.strip())
            split_text = translated_line.split("|||||")
            if len(split_text) == len(text_iterable):
                progress_bar.update(len(split_text))
            else:
                print(
                    "Chunk fixing iteratively. Len chunk: "
                    f"{len(split_text)}, expected: {len(text_iterable)}"
                )
                split_text = []
                for txt_iter in text_iterable:
                    translated_txt = translator.translate(txt_iter.strip())
                    split_text.append(translated_txt)
                    progress_bar.update(1)
            split_list.append(split_text)
        progress_bar.close()
    except Exception as error:
        progress_bar.close()
        print(str(error))
        print(
            "The translation in chunks failed, switching to iterative."
            " Related: too many request"
        )  # use proxy or less chunk size
        return translate_iterative(segments, target, source)

    # un chunk
    translated_lines = list(chain.from_iterable(split_list))

    return verify_translate(
        segments, segments_copy, translated_lines, target, source
    )

def translate_srt(file_path):
    lines = read_srt_file(file_path)
    segments = [{"text": line} for line in lines if line.strip() and not line.strip().isdigit()]
    translated_texts = translate_batch(segments, "km", chunk_size=2000, source="en")
    translated_lines = []
    idx = 0
    for line in lines:
        if line.strip() and not line.strip().isdigit():
            translated_lines.append(translated_texts[idx] + "\n")
            idx += 1
        else:
            translated_lines.append(line)
    translated_file_path = file_path.replace(".srt", ".khmer.srt")
    write_srt_file(translated_file_path, translated_lines)
    print(f"Translated file saved: {translated_file_path}")

def main():
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    # srt_files = get_srt_files(downloads_dir)
    srt_files = [
      "/home/srghma/Downloads/The Naked Gun Trilogy [1080p] x264 - Jalucian/The Naked Gun 3 (1994) [1080p] x264 - Jalucian.srt",
      "/home/srghma/Downloads/The Naked Gun Trilogy [1080p] x264 - Jalucian/The Naked Gun 2 (1991) [1080p] x264 - Jalucian.srt",
      "/home/srghma/Downloads/The Naked Gun Trilogy [1080p] x264 - Jalucian/The Naked Gun (1988) [1080p] x264 - Jalucian.srt",
    ];
    for srt_file in srt_files:
        translate_srt(srt_file)

if __name__ == "__main__":
    main()
