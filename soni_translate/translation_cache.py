import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import hashlib
from .logging_setup import logger

class TranslationCache:
    """Translation cache using SQLite for persistent storage."""

    def __init__(self, cache_path: Optional[str] = None):
        if cache_path is None:
            cache_path = os.environ.get('TRANSLATION_CACHE_SQLITE_PATH')
            if cache_path is None:
                raise ValueError(
                    "TRANSLATION_CACHE_SQLITE_PATH is empty, but expected something like /app/translation-cache.sqlite"
                )

        self.db_path = cache_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS translations (
                    language_from TEXT NOT NULL,
                    language_to TEXT NOT NULL,
                    original TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    translation_method TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (language_from, language_to, original, translation_method)
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_lookup ON translations(language_from, language_to, original, translation_method)')
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def get_cached_translations(
        self,
        language_from: str,
        language_to: str,
        texts: List[str],
        translation_method: str = "google_translator"
    ) -> Dict[str, str]:
        """Get cached translations for a list of texts.

        Args:
            language_from: Source language code
            language_to: Target language code
            texts: List of texts to check for cached translations
            translation_method: Translation method used

        Returns:
            Dictionary mapping original text to cached translation
        """
        if not texts:
            return {}

        # Remove duplicates while preserving order
        unique_texts = list(dict.fromkeys(texts))

        placeholders = ','.join('?' * len(unique_texts))
        query = f'''
            SELECT original, translation
            FROM translations
            WHERE language_from = ? AND language_to = ? AND translation_method = ?
            AND original IN ({placeholders})
        '''

        params = [language_from, language_to, translation_method] + unique_texts

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            results = cursor.fetchall()

        cached_translations = {original: translation for original, translation in results}

        logger.debug(f"Found {len(cached_translations)} cached translations out of {len(unique_texts)} requested")

        return cached_translations

    def save_translations(
        self,
        language_from: str,
        language_to: str,
        translations: List[Dict[str, str]],
        translation_method: str = "google_translator"
    ):
        """Save translations to cache.

        Args:
            language_from: Source language code
            language_to: Target language code
            translations: List of dicts with 'original' and 'translation' keys
            translation_method: Translation method used
        """
        if not translations:
            return

        # Prepare data for batch insert
        insert_data = [
            (language_from, language_to, t['original'], t['translation'], translation_method)
            for t in translations
            if t.get('original') and t.get('translation')  # Skip empty translations
        ]

        if not insert_data:
            return

        with self._get_connection() as conn:
            conn.executemany('''
                INSERT OR REPLACE INTO translations
                (language_from, language_to, original, translation, translation_method)
                VALUES (?, ?, ?, ?, ?)
            ''', insert_data)
            conn.commit()

        logger.debug(f"Saved {len(insert_data)} translations to cache")

    def clear_cache(self, language_from: str = None, language_to: str = None):
        """Clear cache entries.

        Args:
            language_from: If provided, only clear entries for this source language
            language_to: If provided, only clear entries for this target language
        """
        with self._get_connection() as conn:
            if language_from and language_to:
                conn.execute(
                    'DELETE FROM translations WHERE language_from = ? AND language_to = ?',
                    (language_from, language_to)
                )
            elif language_from:
                conn.execute('DELETE FROM translations WHERE language_from = ?', (language_from,))
            elif language_to:
                conn.execute('DELETE FROM translations WHERE language_to = ?', (language_to,))
            else:
                conn.execute('DELETE FROM translations')
            conn.commit()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM translations')
            total_entries = cursor.fetchone()[0]

            cursor = conn.execute('''
                SELECT language_from, language_to, translation_method, COUNT(*)
                FROM translations
                GROUP BY language_from, language_to, translation_method
            ''')
            breakdown = cursor.fetchall()

        return {
            'total_entries': total_entries,
            'breakdown': breakdown
        }


# Global cache instance
_translation_cache = None

def get_translation_cache() -> TranslationCache:
    """Get the global translation cache instance."""
    global _translation_cache
    if _translation_cache is None:
        _translation_cache = TranslationCache()
    return _translation_cache


def extract_texts_from_segments(segments: List[Dict]) -> List[str]:
    """Extract text content from segments, filtering out empty texts."""
    texts = []
    for segment in segments:
        text = segment.get('text', '').strip()
        if text:  # Only include non-empty texts
            texts.append(text)
    return texts


def create_translation_mapping(
    segments: List[Dict],
    cached_translations: Dict[str, str],
    new_translations: List[str]
) -> Dict[str, str]:
    """Create a mapping from original text to translation."""
    translation_mapping = cached_translations.copy()

    # Get unique non-empty texts that need translation
    texts_needing_translation = []
    for segment in segments:
        text = segment.get('text', '').strip()
        if text and text not in cached_translations:
            texts_needing_translation.append(text)

    # Remove duplicates while preserving order
    unique_texts_needing_translation = list(dict.fromkeys(texts_needing_translation))

    # Map new translations
    for i, text in enumerate(unique_texts_needing_translation):
        if i < len(new_translations):
            translation_mapping[text] = new_translations[i]

    return translation_mapping


def apply_cached_translations(segments: List[Dict], translation_mapping: Dict[str, str]) -> List[Dict]:
    """Apply cached translations to segments."""
    translated_segments = []
    for segment in segments:
        segment_copy = segment.copy()
        text = segment.get('text', '').strip()

        if text and text in translation_mapping:
            segment_copy['text'] = translation_mapping[text]
        elif not text:
            # Keep empty text as is
            segment_copy['text'] = segment.get('text', '')

        translated_segments.append(segment_copy)

    return translated_segments
