import translator from "open-google-translator";
import { open } from "sqlite";
import sqlite3 from "sqlite3";

let db;

export async function openDB() {
  const dbPath = `${process.env.XDG_CACHE_HOME || `${process.env.HOME}/.cache`}/my-translate-srt-files-cache.sqlite`;

  db = await open({
    filename: dbPath,
    driver: sqlite3.Database,
  });

  await db.exec(`CREATE TABLE IF NOT EXISTS translations (
    language_from TEXT NOT NULL,
    language_to TEXT NOT NULL,
    original TEXT NOT NULL,
    translation TEXT NOT NULL,
    PRIMARY KEY (language_from, language_to, original)
  )`);
}

// input { from: "en", to: "km", strings: ["im in db", "im not in db"] }
// returns [{ original: "im in db", text_translation: "..." }]
export async function db__getArrayOfTranslations({
  languageFrom,
  languageTo,
  strArray,
}) {
  if (!strArray.length) return [];

  const placeholders = Array(strArray.length).fill("?").join(",");
  const params = [languageFrom, languageTo, ...strArray];

  const rows = await db.all(
    `SELECT original, translation
     FROM translations
     WHERE language_from = ?
     AND language_to = ?
     AND original IN (${placeholders})`,
    params,
  );

  return rows.map(({ original, translation }) => ({
    original,
    translation,
  }));
}

export async function db__upsertArrayOfTranslations({
  languageFrom,
  languageTo,
  translations,
}) {
  if (!translations.length) return [];

  const values = translations
    .map(({ original, translation }) => `(?, ?, ?, ?)`)
    .join(",");

  const params = translations.flatMap(({ original, translation }) => [
    languageFrom,
    languageTo,
    original,
    translation,
  ]);

  await db.run(
    `INSERT OR REPLACE INTO translations (language_from, language_to, original, translation) VALUES ${values}`,
    params,
  );
}

export async function translateSrt({
  strDataArray,
  languageFrom,
  languageTo,
}) {
  const srtDataText__nonEmpty = strDataArray.map(({ text }) => text.trim()).filter((x) => x)

  const translationsFromDB = await getTranslationsFromDbIfExist({
    languageFrom,
    languageTo,
    strArray: srtDataText__nonEmpty,
  });

  const listOfWordsToTranslate = srtDataText__nonEmpty
    .filter(
      (text) => !translationsFromDB.find((t) => t.original === text),
    );

  if (listOfWordsToTranslate.length + translationsFromDB.length !== srtDataText__nonEmpty.length) {
    throw new Error(
      `not all words are translated,
      listOfWordsToTranslate.length (${listOfWordsToTranslate.length}) + translationsFromDB.length (${translationsFromDB.length})
      === ${listOfWordsToTranslate.length + translationsFromDB.length}
      !== srtDataText__nonEmpty.length (${srtDataText__nonEmpty.length})`,
    );
  }

  let translations = [];

  if (listOfWordsToTranslate.length > 0) {
    // console.log(`requesting google translations ${listOfWordsToTranslate.length}`);
    translations = await translator.TranslateLanguageData({
      listOfWordsToTranslate,
      languageFrom,
      languageTo,
    });
  }

  const invalidTranslations = translations.filter((x) => !x.translation.trim());

  if (invalidTranslations.length > 0) {
    throw new Error(`no translation for ${invalidTranslations.map((x) => x.original)}`);
  }

  db__upsertArrayOfTranslations({
    translations,
    languageFrom,
    languageTo,
  });

  const output = strDataArray.map(async (strData) => {
    const { text } = strData;
    if (!text.trim()) {
      return { ...strData, translation: text };
    }
    // find
    return { ...strData, translation };
  });
  return output;
}
