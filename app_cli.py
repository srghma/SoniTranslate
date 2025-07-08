from soni_translate.logging_setup import (
    logger,
    set_logging_level,
    configure_logging_libs,
); configure_logging_libs() # noqa
import whisperx
import shutil
import torch
import os
from soni_translate.audio_segments import create_translated_audio
from soni_translate.text_to_speech import (
    audio_segmentation_to_voice,
    edge_tts_voices_list,
    coqui_xtts_voices_list,
    piper_tts_voices_list,
    create_wav_file_vc,
    accelerate_segments,
)
from soni_translate.translate_segments_cached import (
    translate_text,
    TRANSLATION_PROCESS_OPTIONS,
    DOCS_TRANSLATION_PROCESS_OPTIONS
)
from soni_translate.preprocessor import (
    audio_video_preprocessor,
    audio_preprocessor,
)
from soni_translate.postprocessor import (
    OUTPUT_TYPE_OPTIONS,
    DOCS_OUTPUT_TYPE_OPTIONS,
    sound_separate,
    get_no_ext_filename,
    media_out,
    get_subtitle_speaker,
)
from soni_translate.language_configuration import (
    LANGUAGES,
    UNIDIRECTIONAL_L_LIST,
    LANGUAGES_LIST,
    BARK_VOICES_LIST,
    VITS_VOICES_LIST,
    OPENAI_TTS_MODELS,
)
from soni_translate.utils import (
    remove_files,
    download_list,
    upload_model_list,
    download_manager,
    run_command,
    is_audio_file,
    is_subtitle_file,
    copy_files,
    get_valid_files,
    get_link_list,
    remove_directory_contents,
)
from soni_translate.mdx_net import (
    UVR_MODELS,
    MDX_DOWNLOAD_LINK,
    mdxnet_models_dir,
)
from soni_translate.speech_segmentation import (
    ASR_MODEL_OPTIONS,
    COMPUTE_TYPE_GPU,
    COMPUTE_TYPE_CPU,
    find_whisper_models,
    transcribe_speech,
    align_speech,
    diarize_speech,
    diarization_models,
)
from soni_translate.text_multiformat_processor import (
    BORDER_COLORS,
    srt_file_to_segments,
    document_preprocessor,
    determine_chunk_size,
    plain_text_to_segments,
    segments_to_plain_text,
    process_subtitles,
    linguistic_level_segments,
    break_aling_segments,
    doc_to_txtximg_pages,
    page_data_to_segments,
    update_page_data,
    fix_timestamps_docs,
    create_video_from_images,
    merge_video_and_audio,
)
from soni_translate.languages_gui import language_data, news
import copy
import logging
import json
from pydub import AudioSegment
from voice_main import ClassVoices
import argparse
import time
import hashlib
import sys
from app_rvc import SoniTranslate
from pytube import Playlist

if __name__ == "__main__":
    set_logging_level("debug")

    for id_model in UVR_MODELS:
        download_manager(
            os.path.join(MDX_DOWNLOAD_LINK, id_model), mdxnet_models_dir
        )

    models_path, index_path = upload_model_list()

    SoniTr = SoniTranslate(cpu_mode=True)

    # CLI translation parameters
    #
    # cd ~/Downloads && unroot-root-files
    # NAME='nevzorov-shorts'
    # DIR="$HOME/Downloads/$NAME"
    # mkdir -p "$DIR" && cd "$DIR"
    # yt-dlp --embed-subs "https://www.youtube.com/shorts/rYrKALtxOks"
    # wget -O thumbnail.jpg "https://img.youtube.com/vi/bbiu8SUgPr4/maxresdefault.jpg"

    # Get all video files in the Veritasium directory
    input_dir = "/home/srghma/Videos/"
    output_dir = "/home/srghma/Videos/output-ru/"

    os.makedirs(output_dir, exist_ok=True)

    # Get list of video files
    video_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(('.mp4', '.webm', '.mkv'))]
    # video_files = ["/home/srghma/Videos/russians-torture/IMG_1651.MP4"]

    for video_path in video_files:
        result = SoniTr.multilingual_media_conversion(
            media_file=video_path,
            min_speakers=1,
            max_speakers=2,
            origin_language="English (en)",
            # target_language="Ukrainian (uk)",
            target_language="Russian (ru)",
            # target_language="Khmer (km)",
            # target_language="English (en)",
            # tts_voice00="km-KH-SreypichNeural-Female",
            tts_voice00="ru_RU-denis-medium VITS-onnx",
            tts_voice00="ru_speaker_0-Male BARK",
            # tts_voice00="uk-UA-OstapNeural-Male", # Azure
            # tts_voice01="uk_UA-ukrainian_tts-medium VITS-onnx",
            # volume_original_audio=0.95,
            diarization_model="pyannote_3.1",
            voice_imitation=True,
            is_gui=False,
            progress=None
        )

        print(f"Translation complete. Output saved to: {result}")

        os.makedirs(output_dir, exist_ok=True)

        for result_file in result:
            shutil.copy2(result_file, Path(output_dir) / Path(result_file).name)

        # cp -p /app/outputs/* /home/srghma/Videos/output-uk/
