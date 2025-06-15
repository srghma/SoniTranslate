from tqdm import tqdm
from deep_translator import GoogleTranslator
from itertools import chain
import copy
from .language_configuration import fix_code_language, INVERTED_LANGUAGES
from .logging_setup import logger
import re
import json
import time

# Import original functions and constants
from .translate_segments import (
    translate_iterative,
    translate_batch,
    gpt_sequential,
    gpt_batch,
    # call_gpt_translate,
    # verify_translate,
    TRANSLATION_PROCESS_OPTIONS as ORIGINAL_TRANSLATION_PROCESS_OPTIONS,
    DOCS_TRANSLATION_PROCESS_OPTIONS as ORIGINAL_DOCS_TRANSLATION_PROCESS_OPTIONS
)

# Import cache functionality
from .translation_cache import (
    get_translation_cache,
    extract_texts_from_segments,
    create_translation_mapping,
    apply_cached_translations
)

# Export the same constants as the original module
TRANSLATION_PROCESS_OPTIONS = ORIGINAL_TRANSLATION_PROCESS_OPTIONS
DOCS_TRANSLATION_PROCESS_OPTIONS = ORIGINAL_DOCS_TRANSLATION_PROCESS_OPTIONS


def translate_iterative_cached(segments, target, source=None):
    """
    Translate text segments individually with caching support.
    """
    cache = get_translation_cache()
    method_name = "google_translator"

    # Extract texts and check cache
    texts = extract_texts_from_segments(segments)
    cached_translations = cache.get_cached_translations(
        source or "auto", target, texts, method_name
    )

    # Find texts that need translation
    texts_to_translate = [text for text in texts if text not in cached_translations]

    if not texts_to_translate:
        logger.info("All translations found in cache")
        translation_mapping = cached_translations
    else:
        logger.info(f"Translating {len(texts_to_translate)} new texts, {len(cached_translations)} from cache")

        # Create segments for texts that need translation
        segments_to_translate = []
        for text in texts_to_translate:
            segments_to_translate.append({'text': text})

        # Translate using existing function
        translated_segments = translate_iterative(segments_to_translate, target, source)
        new_translations = [seg['text'] for seg in translated_segments]

        # Save new translations to cache
        cache_data = [
            {'original': orig, 'translation': trans}
            for orig, trans in zip(texts_to_translate, new_translations)
        ]
        cache.save_translations(source or "auto", target, cache_data, method_name)

        # Create complete translation mapping
        translation_mapping = create_translation_mapping(
            segments, cached_translations, new_translations
        )

    # Apply translations to all segments
    return apply_cached_translations(segments, translation_mapping)


def translate_batch_cached(segments, target, chunk_size=2000, source=None):
    """
    Translate text segments in batches with caching support.
    """
    cache = get_translation_cache()
    method_name = "google_translator_batch"

    # Extract texts and check cache
    texts = extract_texts_from_segments(segments)
    cached_translations = cache.get_cached_translations(
        source or "auto", target, texts, method_name
    )

    # Find texts that need translation
    texts_to_translate = [text for text in texts if text not in cached_translations]

    if not texts_to_translate:
        logger.info("All translations found in cache")
        translation_mapping = cached_translations
    else:
        logger.info(f"Translating {len(texts_to_translate)} new texts, {len(cached_translations)} from cache")

        # Create segments for texts that need translation
        segments_to_translate = []
        for text in texts_to_translate:
            segments_to_translate.append({'text': text})

        # Translate using existing function
        translated_segments = translate_batch(segments_to_translate, target, chunk_size, source)
        new_translations = [seg['text'] for seg in translated_segments]

        # Save new translations to cache
        cache_data = [
            {'original': orig, 'translation': trans}
            for orig, trans in zip(texts_to_translate, new_translations)
        ]
        cache.save_translations(source or "auto", target, cache_data, method_name)

        # Create complete translation mapping
        translation_mapping = create_translation_mapping(
            segments, cached_translations, new_translations
        )

    # Apply translations to all segments
    return apply_cached_translations(segments, translation_mapping)


def gpt_sequential_cached(segments, model, target, source=None):
    """
    Translate text segments sequentially using GPT with caching support.
    """
    cache = get_translation_cache()
    method_name = model

    # Extract texts and check cache
    texts = extract_texts_from_segments(segments)
    cached_translations = cache.get_cached_translations(
        source or "auto", target, texts, method_name
    )

    # Find texts that need translation
    texts_to_translate = [text for text in texts if text not in cached_translations]

    if not texts_to_translate:
        logger.info("All translations found in cache")
        translation_mapping = cached_translations
    else:
        logger.info(f"Translating {len(texts_to_translate)} new texts, {len(cached_translations)} from cache")

        # Create segments for texts that need translation (preserve structure needed for GPT)
        segments_to_translate = []
        for segment in segments:
            text = segment.get('text', '').strip()
            if text and text in texts_to_translate:
                segments_to_translate.append(segment)

        # Translate using existing function
        translated_segments = gpt_sequential(segments_to_translate, model, target, source)

        # Extract new translations and save to cache
        original_texts = [seg['text'] for seg in segments_to_translate]
        translated_texts = [seg['text'] for seg in translated_segments]

        cache_data = [
            {'original': orig, 'translation': trans}
            for orig, trans in zip(original_texts, translated_texts)
        ]
        cache.save_translations(source or "auto", target, cache_data, method_name)

        # Create translation mapping
        translation_mapping = create_translation_mapping(
            segments, cached_translations, translated_texts
        )

    # Apply translations to all segments
    return apply_cached_translations(segments, translation_mapping)


def gpt_batch_cached(segments, model, target, token_batch_limit=900, source=None):
    """
    Translate text segments in batches using GPT with caching support.
    """
    cache = get_translation_cache()
    method_name = f"{model}_batch"

    # Extract texts and check cache
    texts = extract_texts_from_segments(segments)
    cached_translations = cache.get_cached_translations(
        source or "auto", target, texts, method_name
    )

    # Find texts that need translation
    texts_to_translate = [text for text in texts if text not in cached_translations]

    if not texts_to_translate:
        logger.info("All translations found in cache")
        translation_mapping = cached_translations
    else:
        logger.info(f"Translating {len(texts_to_translate)} new texts, {len(cached_translations)} from cache")

        # Create segments for texts that need translation (preserve structure needed for GPT)
        segments_to_translate = []
        for segment in segments:
            text = segment.get('text', '').strip()
            if text and text in texts_to_translate:
                segments_to_translate.append(segment)

        # Translate using existing function
        translated_segments = gpt_batch(segments_to_translate, model, target, token_batch_limit, source)

        # Extract new translations and save to cache
        original_texts = [seg['text'] for seg in segments_to_translate]
        translated_texts = [seg['text'] for seg in translated_segments]

        cache_data = [
            {'original': orig, 'translation': trans}
            for orig, trans in zip(original_texts, translated_texts)
        ]
        cache.save_translations(source or "auto", target, cache_data, method_name)

        # Create translation mapping
        translation_mapping = create_translation_mapping(
            segments, cached_translations, translated_texts
        )

    # Apply translations to all segments
    return apply_cached_translations(segments, translation_mapping)


def translate_text(
    segments,
    target,
    translation_process="google_translator_batch",
    chunk_size=4500,
    source=None,
    token_batch_limit=1000,
    use_cache=True,
):
    """
    Translates text segments using a specified process with caching support.

    This is the main function that replaces the original translate_text from translate_segments.py
    By default, caching is enabled. Set use_cache=False to disable caching.
    """

    if not use_cache:
        # Import and use original function without caching
        from .translate_segments import translate_text as original_translate_text
        return original_translate_text(
            segments, target, translation_process, chunk_size, source, token_batch_limit
        )

    match translation_process:
        case "google_translator_batch":
            return translate_batch_cached(
                segments,
                fix_code_language(target),
                chunk_size,
                fix_code_language(source)
            )
        case "google_translator":
            return translate_iterative_cached(
                segments,
                fix_code_language(target),
                fix_code_language(source)
            )
        case model if model in ["gpt-3.5-turbo-0125", "gpt-4-turbo-preview"]:
            return gpt_sequential_cached(segments, model, target, source)
        case model if model in ["gpt-3.5-turbo-0125_batch", "gpt-4-turbo-preview_batch"]:
            return gpt_batch_cached(
                segments,
                translation_process.replace("_batch", ""),
                target,
                token_batch_limit,
                source
            )
        case "disable_translation":
            return segments
        case _:
            raise ValueError("No valid translation process")


# Utility functions for cache management
def clear_translation_cache(language_from: str = None, language_to: str = None):
    """Clear translation cache."""
    cache = get_translation_cache()
    cache.clear_cache(language_from, language_to)
    logger.info(f"Cache cleared for {language_from or 'all'} -> {language_to or 'all'}")


def get_cache_statistics():
    """Get translation cache statistics."""
    cache = get_translation_cache()
    return cache.get_cache_stats()


def preload_translations(text_list, target_lang, source_lang='en', method='google_translator'):
    """
    Preload translations for a list of common texts.
    Useful for warming up the cache with frequently used phrases.
    """
    segments = [{'text': text, 'start': i, 'speaker': 'preload'}
                for i, text in enumerate(text_list)]

    translate_text(
        segments=segments,
        target=target_lang,
        source=source_lang,
        translation_process=method,
        use_cache=True
    )

    logger.info(f"Preloaded {len(text_list)} translations for {source_lang} -> {target_lang}")


# Additional utility functions that might be useful
def batch_translate_with_cache(file_segments_list, target_lang, source_lang='en',
                              translation_process='google_translator_batch'):
    """
    Translate multiple files efficiently using cache.

    Args:
        file_segments_list: List of (filename, segments) tuples
        target_lang: Target language code
        source_lang: Source language code
        translation_process: Translation method to use

    Returns:
        List of (filename, translated_segments) tuples
    """
    results = []

    for filename, segments in file_segments_list:
        logger.info(f"Translating {filename}...")
        translated = translate_text(
            segments=segments,
            target=target_lang,
            source=source_lang,
            translation_process=translation_process,
            use_cache=True
        )
        results.append((filename, translated))

    return results
