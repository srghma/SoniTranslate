// var fs = require("fs");
// var path = require("path");
// var { glob } = require("glob");
// var { mkdirp } = require("mkdirp");
// var { translateText, translateDocs } = require("puppeteer-google-translate");
// var srtParser2 = require("srt-parser-2").default;
// var languageEncoding = require("detect-file-encoding-and-language");
// var translator = require("open-google-translator");
// var Keyv = require("keyv").default;

import * as fs from "node:fs";
import { exec } from "node:child_process";
import * as path from "node:path";
import glob from "glob";
import srtParser2 from "srt-parser-2";
import languageEncoding from "detect-file-encoding-and-language";
import translator from "open-google-translator";
import Keyv from "keyv";
import KeyvSqlite from "@keyv/sqlite";

async function checkFileExists(file) {
  try {
    await fs.promises.access(file, fs.constants.F_OK);
    return true;
  } catch {
    return false;
  }
}
/////////////

const parser = new srtParser2();
// const downloadsDir = path.join(process.env.HOME, "Downloads");

const args = process.argv.slice(process.argv[0].endsWith("node") ? 2 : 1);

let srts = await Promise.all(
  args.map(async (arg) => {
    if (arg.match(/\.(mp4|mkv|avi|mov|wmv|flv|webm)$/i)) {
      const enSrtFile = arg.replace(/\.[^.]+$/, ".en.srt");
      const srtFile = arg.replace(/\.[^.]+$/, ".srt");
      if (await checkFileExists(enSrtFile)) {
        console.log(`found srt file at ${enSrtFile}`);
        return enSrtFile;
      } else if (await checkFileExists(srtFile)) {
        console.log(`found srt file at ${srtFile}`);
        return srtFile;
      } else {
        console.log(`trying ffmpeg -i "${arg}" -map "0:s:0" "${srtFile}"`);
        await new Promise((resolve, reject) => {
          exec(`ffmpeg -i "${arg}" -map "0:s:0" "${srtFile}"`, (error) => {
            if (error) reject(error);
            else resolve();
          });
        });
        return srtFile;
      }
    } else if (arg.endsWith(".srt")) {
      return arg;
    }
  }),
).then((files) => files.filter(Boolean));

// let srts = await glob(`${downloadsDir}/**/*.srt`);

// srts = [
//   "/home/srghma/Downloads/Kindergarten Cop (1990)/Kindergarten.Cop.1990.720p.BluRay.x264.YIFY.srt",
// ];

srts = srts.map((srt) => ({
  srt,
  // outputPathInDownloads: "/home/srghma/Downloads/" + path.basename(srt).replace(/\.srt$/, ".km.srt"),
  outputPath: srt.replace(/\.srt$/, ".km.srt"),
}));

for (const { srt, outputPathInDownloads, outputPath } of srts) {
  if (!(await checkFileExists(srt))) {
    throw new Error(`File not found ${srt}`);
  }
  if (await checkFileExists(outputPathInDownloads)) {
    console.log(`${outputPathInDownloads} exists`);
  }
  if (await checkFileExists(outputPath)) {
    console.log(`${outputPath} exists`);
  }
}

srts = await Promise.all(
  srts.map(async ({ srt, outputPathInDownloads, outputPath }) => {
    const buffer = fs.readFileSync(srt);
    const charsetMatch = await languageEncoding(buffer);
    if (charsetMatch.confidence.encoding !== 1) {
      console.log("charsetMatch:", charsetMatch);
      throw new Error(
        `${srt} -> low confidence.encoding: ${charsetMatch.confidence.encoding} for ${charsetMatch.encoding}`,
      );
    }
    if (charsetMatch.confidence.language !== 1) {
      console.log("charsetMatch:", charsetMatch);
      console.log(
        `${srt} -> low confidence.language: ${charsetMatch.confidence.language} for ${charsetMatch.language}`,
      );
    }
    let srtString = null;
    try {
      srtString = buffer.toString(charsetMatch.encoding);
    } catch (error) {
      console.log("Error converting buffer with detected encoding:", error);
      console.log("charsetMatch:", charsetMatch);
      // Fallback to UTF-8 if encoding fails
      srtString = buffer.toString("utf8");
      // Test that string is valid utf8 by attempting to re-encode
      const testEncode = Buffer.from(srtString, "utf8").toString("utf8");
      if (testEncode !== srtString) {
        throw new Error("Failed to convert file to UTF-8");
      }
    }
    return { srt, srtString, outputPathInDownloads, outputPath };
  }),
);

srts = srts.map((x) => {
  const { srt, srtString, outputPathInDownloads, outputPath } = x;
  const strDataArray = parser.fromSrt(srtString);
  return { srt, strDataArray, outputPathInDownloads, outputPath };
});

async function translateSrt({ strDataArray, fromLanguage, toLanguage }) {
  // const { srt, strDataArray, outputPathInDownloads, outputPath } = srts[0];
  // const listOfWordsToTranslate = strDataArray;
  // const fromLanguage = "en";
  // const toLanguage = "km";

  const store = new Keyv({
    store: new KeyvSqlite({
      uri: `sqlite://${process.env.XDG_CACHE_HOME || `${process.env.HOME}/.cache`}/my-translate-srt-files-cache.sqlite`,
    }),
    namespace: `${fromLanguage}-${toLanguage}`,
  });

  const maybeTranslations = await Promise.all(
    strDataArray
      .map(({ text }) => text.trim())
      .filter((x) => x)
      .map(async (original) => ({
        original,
        translation: await store.get(original),
      })),
  );

  const listOfWordsToTranslate = maybeTranslations
    .map(({ original, translation }) => (!translation ? original : null))
    .filter((x) => x);

  // console.log(listOfWordsToTranslate)

  let translations = [];

  if (listOfWordsToTranslate.length > 0) {
    console.log(
      `requesting google translations ${listOfWordsToTranslate.length}`,
    );
    translations = await translator.TranslateLanguageData({
      listOfWordsToTranslate,
      fromLanguage,
      toLanguage,
    });
  }

  const invalidTranslations = translations.filter(
    ({ translation }) => !translation.trim(),
  );
  console.log(invalidTranslations);
  if (invalidTranslations.length > 0) {
    throw new Error(
      `no translation for ${invalidTranslations.map((x) => x.original)}`,
    );
  }

  for (const { original, translation } of translations) {
    await store.set(original, translation);
  }

  const output = await Promise.all(
    strDataArray.map(async (strData) => {
      const { text } = strData;
      if (!text.trim()) {
        return { ...strData, translation: text };
      }
      const translation = await store.get(text);
      const valid = !!translation.trim();
      if (!valid) {
        throw new Error(`no translation for ${text}: ${translation}`);
      }
      return { ...strData, translation };
    }),
  );
  // console.log(output)

  return output;
}

for (const { srt, strDataArray, outputPath } of srts) {
  console.log(`processing ${srt}`);
  // const { srt, strDataArray, outputPathInDownloads, outputPath } = srts[0];
  const output = await translateSrt({
    strDataArray,
    fromLanguage: "en",
    toLanguage: "km",
  });

  const outputWithMergedText = output.map((data) => ({
    ...data,
    text: `${data.text}\n<font color="yellow">${data.translation}</font>`,
  }));

  const srt_string = parser.toSrt(outputWithMergedText);

  fs.writeFileSync(outputPath, srt_string);

  console.log(`${outputPath} is created`);
}
